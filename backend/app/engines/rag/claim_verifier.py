import json
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.engines.rag.prompt_templates import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from app.models.audit import AuditEngine, FindingSeverity
from app.models.knowledge import ApprovedFact, DocumentChunk
from app.schemas.finding import FindingBase
from app.services.embedding_service import get_embedding
from app.services.knowledge_service import KnowledgeService
from app.utils.logger import logger


class LLMFindingItem(BaseModel):
    rule_id: str = Field(default="RAG-01-CLAIM")
    category: str = Field(default="FACTUAL")
    severity: str = Field(default="HIGH")
    title: str
    detected_content: str
    explanation: str
    source_citation: str
    supporting_passage: str
    suggested_correction: str
    confidence_score: float = Field(default=0.9, ge=0.0, le=1.0)
    requires_human_review: bool = Field(default=True)


class LLMAuditOutput(BaseModel):
    findings: List[LLMFindingItem] = Field(default_factory=list)
    overall_tone_summary: Optional[str] = None


def run_deterministic_rag_grounding(
    content: str,
    approved_facts: List[ApprovedFact],
    relevant_chunks: List[Dict[str, Any]],
) -> List[FindingBase]:
    """
    High-fidelity deterministic claim and tone verifier used for offline evaluation
    or as a baseline to guarantee zero hallucinations and instantaneous verification.
    """
    findings: List[FindingBase] = []
    content_lower = content.lower()

    # 1. Fact-vs-Claim Verification
    for fact in approved_facts:
        truth = fact.approved_truth.lower()
        # Look for numbers/percentages in approved truth vs draft
        truth_pcts = re.findall(r"(\d+)%", truth)
        draft_pcts = re.findall(r"(\d+)%", content)

        # Check if draft mentions the topic or claim pattern
        pattern_words = [w for w in fact.claim_pattern.lower().split() if len(w) > 3]
        pattern_match = any(pw in content_lower for pw in pattern_words) if pattern_words else True

        if pattern_match and truth_pcts and draft_pcts:
            t_val = int(truth_pcts[0])
            for d_str in draft_pcts:
                d_val = int(d_str)
                if d_val > t_val:
                    # Exaggerated metric detected!
                    findings.append(
                        FindingBase(
                            rule_id="RAG-01-CLAIM-EXAGGERATION",
                            engine=AuditEngine.RAG_LLM,
                            category="FACTUAL",
                            severity=FindingSeverity.HIGH,
                            title=f"Exaggerated Performance Claim ({d_val}% vs approved {t_val}%)",
                            detected_content=f"{d_val}% (in draft: '{content}')",
                            explanation=(
                                f"Draft claims {d_val}%, which exceeds the organization's approved truth "
                                f"of up to {t_val}%. {fact.mandatory_caveat or ''}"
                            ),
                            source_citation=fact.source_citation,
                            supporting_passage=fact.approved_truth,
                            suggested_correction=f"Customers achieve up to {t_val}% improvement.",
                            confidence_score=0.95,
                            requires_human_review=True,
                        )
                    )

        # Timeframe comparison (e.g. "overnight" or "instant" vs months/weeks)
        if ("overnight" in content_lower or "instantly" in content_lower) and (
            "month" in truth or "week" in truth or "year" in truth
        ):
            findings.append(
                FindingBase(
                    rule_id="RAG-02-TIMEFRAME-MISMATCH",
                    engine=AuditEngine.RAG_LLM,
                    category="FACTUAL",
                    severity=FindingSeverity.HIGH,
                    title="Unsubstantiated Timeframe Promise",
                    detected_content="overnight" if "overnight" in content_lower else "instantly",
                    explanation=(
                        f"Draft promises instantaneous/overnight results, but the approved factual benchmark "
                        f"states: '{fact.approved_truth}'"
                    ),
                    source_citation=fact.source_citation,
                    supporting_passage=fact.approved_truth,
                    suggested_correction="over documented deployment cycles",
                    confidence_score=0.92,
                    requires_human_review=True,
                )
            )

    # 2. Tone & Hyperbole Analysis against Guidelines
    hyperbole_phrases = [
        ("100% foolproof", "foolproof", "Avoid absolute reliability claims without qualification"),
        ("guaranteed success", "guaranteed", "Avoid unsupportable commercial guarantees"),
        ("miracle", "miracle", "Unprofessional hyperbole"),
        ("unmatched in every way", "unmatched", "Requires competitive substantiation"),
    ]
    for phrase, keyword, reason in hyperbole_phrases:
        if keyword in content_lower:
            citation = "Brand Communication Guidelines — Tone & Substantiation"
            passage = "All promotional messaging must remain objective, evidence-based, and free of hyperbolic guarantees."
            if relevant_chunks:
                citation = relevant_chunks[0]["guideline_title"]
                passage = relevant_chunks[0]["content"][:200]

            findings.append(
                FindingBase(
                    rule_id="RAG-03-OFFBRAND-TONE",
                    engine=AuditEngine.RAG_LLM,
                    category="TONE",
                    severity=FindingSeverity.MEDIUM,
                    title=f"Hyperbolic Brand Tone Detected: '{keyword}'",
                    detected_content=phrase if phrase in content_lower else keyword,
                    explanation=f"Use of hyperbolic language violates brand voice principles: {reason}.",
                    source_citation=citation,
                    supporting_passage=passage,
                    suggested_correction="proven, data-supported solution",
                    confidence_score=0.88,
                    requires_human_review=True,
                )
            )

    return findings


def run_gemini_rag_grounding(
    content: str,
    approved_facts: List[ApprovedFact],
    relevant_chunks: List[Dict[str, Any]],
) -> List[FindingBase]:
    """
    Invoke Google Gemini API with structured JSON output, hard citation boundaries,
    and automatic validation of cited passages.
    """
    from google import genai
    from google.genai import types

    facts_text = "\n".join(
        [
            f"- [Fact ID: {f.id}] Category: {f.category} | Truth: \"{f.approved_truth}\" | Source: {f.source_citation}"
            for f in approved_facts
        ]
    )
    if not facts_text:
        facts_text = "No registered approved facts found for this organization."

    chunks_text = "\n".join(
        [
            f"- [Chunk ID: {c['chunk_id']}] Doc: {c['guideline_title']} (p. {c.get('page_number', 1)}) | Text: \"{c['content']}\""
            for c in relevant_chunks
        ]
    )
    if not chunks_text:
        chunks_text = "No guideline passages retrieved."

    user_prompt = USER_PROMPT_TEMPLATE.format(
        approved_facts_str=facts_text,
        guideline_passages_str=chunks_text,
        content=content,
    )

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    response = client.models.generate_content(
        model=settings.LLM_MODEL,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=LLMAuditOutput,
            temperature=0.1,  # Low temperature for deterministic adherence to evidence
        ),
    )

    findings: List[FindingBase] = []
    try:
        raw_text = response.text
        parsed = LLMAuditOutput.model_validate_json(raw_text)

        # Build citation lookup for hallucination verification
        known_sources = {f.source_citation.lower(): f.approved_truth for f in approved_facts}
        for c in relevant_chunks:
            known_sources[c["guideline_title"].lower()] = c["content"]

        for item in parsed.findings:
            # Map severity
            sev = FindingSeverity.MEDIUM
            if item.severity.upper() == "HIGH":
                sev = FindingSeverity.HIGH
            elif item.severity.upper() == "LOW":
                sev = FindingSeverity.LOW

            # Hallucination Defense: verify source citation is grounded
            is_grounded = any(
                src_key in item.source_citation.lower() or item.source_citation.lower() in src_key
                for src_key in known_sources
            )
            confidence = item.confidence_score if is_grounded else 0.5

            findings.append(
                FindingBase(
                    rule_id=item.rule_id,
                    engine=AuditEngine.RAG_LLM,
                    category=item.category.upper(),
                    severity=sev,
                    title=item.title,
                    detected_content=item.detected_content,
                    explanation=item.explanation,
                    source_citation=item.source_citation,
                    supporting_passage=item.supporting_passage,
                    suggested_correction=item.suggested_correction,
                    confidence_score=confidence,
                    requires_human_review=sev == FindingSeverity.HIGH or confidence < 0.85,
                )
            )
    except Exception as e:
        logger.error(f"Error parsing Gemini structured response: {e}")
        # Graceful fallback to deterministic grounding
        return run_deterministic_rag_grounding(content, approved_facts, relevant_chunks)

    return findings


def audit_content_with_rag(
    db: Session,
    organization_id: str,
    content: str,
) -> List[FindingBase]:
    """
    Main entry point for Engine B (RAG + LLM Grounding).
    Retrieves candidate facts and semantic chunks, then executes grounded verification.
    """
    if not content or not content.strip():
        return []

    # 1. Retrieve organization approved facts
    stmt_facts = select(ApprovedFact).where(ApprovedFact.organization_id == organization_id)
    approved_facts = db.execute(stmt_facts).scalars().all()

    # 2. Semantic retrieval of top guideline chunks
    query_vector = get_embedding(content)
    relevant_chunks = KnowledgeService.search_relevant_chunks(
        db=db,
        organization_id=organization_id,
        query_embedding=query_vector,
        top_k=4,
        min_similarity=0.15,
    )

    # 3. Execute LLM or Grounded Fallback
    if settings.GEMINI_API_KEY:
        try:
            return run_gemini_rag_grounding(content, approved_facts, relevant_chunks)
        except Exception as e:
            logger.warning(f"Gemini API call failed: {e}. Running deterministic grounding fallback.")
            return run_deterministic_rag_grounding(content, approved_facts, relevant_chunks)
    else:
        return run_deterministic_rag_grounding(content, approved_facts, relevant_chunks)
