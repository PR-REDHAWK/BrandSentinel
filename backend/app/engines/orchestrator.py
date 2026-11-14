import os
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.engines.deterministic.accessibility import scan_accessibility
from app.engines.deterministic.contrast import scan_html_css_contrast
from app.engines.deterministic.terms import scan_terminology
from app.engines.rag.claim_verifier import audit_content_with_rag
from app.engines.vision.color_checker import check_image_color_compliance
from app.engines.vision.logo_checker import check_logo_integrity
from app.engines.vision.ocr_engine import extract_text_from_image
from app.models.audit import (
    AuditEngine,
    ContentVersion,
    Finding,
    FindingSeverity,
    Submission,
    SubmissionStatus,
)
from app.models.knowledge import BrandAsset, GlossaryTerm
from app.models.log import AuditLog
from app.schemas.finding import FindingBase
from app.utils.logger import logger


class AuditPipelineResult:
    def __init__(
        self,
        content_version_id: str,
        audit_score: float,
        findings: List[Finding],
        summary: Dict[str, Any],
    ):
        self.content_version_id = content_version_id
        self.audit_score = audit_score
        self.findings = findings
        self.summary = summary


def calculate_brand_compliance_score(findings: List[FindingBase]) -> float:
    """
    Computes an objective Brand Compliance Index (0.0 to 100.0) based on finding severities.
    - HIGH severity (factual errors, banned terms, contrast fails): -15 pts
    - MEDIUM severity (tone mismatch, glossary deviations): -8 pts
    - LOW severity (all-caps shouting, formatting): -3 pts
    """
    score = 100.0
    for f in findings:
        if f.severity == FindingSeverity.HIGH:
            score -= 15.0
        elif f.severity == FindingSeverity.MEDIUM:
            score -= 8.0
        elif f.severity == FindingSeverity.LOW:
            score -= 3.0
    return max(0.0, round(score, 1))


def run_unified_audit_pipeline(
    db: Session,
    organization_id: str,
    user_id: str,
    submission_id: str,
    content: str,
    image_bytes_list: Optional[List[bytes]] = None,
    document_path: Optional[str] = None,
) -> AuditPipelineResult:
    """
    Unified Tri-Engine Auditing Pipeline.
    1. Deterministic Engine: Terms, WCAG contrast, accessibility.
    2. RAG + LLM Grounding Engine: Claim vs fact verification, tone analysis.
    3. Vision + OCR Engine: Multimodal text extraction, palette tolerances, logo checks.
    Aggregates findings, computes brand score, enforces review flags, and persists results.
    """
    aggregated_findings: List[FindingBase] = []
    image_bytes_list = image_bytes_list or []

    # 1. Fetch organization knowledge assets
    glossary_stmt = select(GlossaryTerm).where(GlossaryTerm.organization_id == organization_id)
    glossary_terms = db.execute(glossary_stmt).scalars().all()

    assets_stmt = select(BrandAsset).where(BrandAsset.organization_id == organization_id)
    brand_assets = db.execute(assets_stmt).scalars().all()
    palette_assets = [a for a in brand_assets if a.asset_type == "PALETTE"]
    logo_assets = [a for a in brand_assets if a.asset_type == "LOGO"]

    # ----------------------------------------------------
    # ENGINE A: Deterministic Rule Engine
    # ----------------------------------------------------
    # Terms & Glossary
    term_findings = scan_terminology(content, glossary_terms)
    aggregated_findings.extend(term_findings)

    # HTML/CSS Contrast
    css_contrast_findings = scan_html_css_contrast(content)
    aggregated_findings.extend(css_contrast_findings)

    # Accessibility & Typography
    accessibility_findings = scan_accessibility(content, is_html="<html" in content.lower())
    aggregated_findings.extend(accessibility_findings)

    # ----------------------------------------------------
    # ENGINE B: RAG + LLM Grounding Engine
    # ----------------------------------------------------
    rag_findings = audit_content_with_rag(db, organization_id, content)
    aggregated_findings.extend(rag_findings)

    # ----------------------------------------------------
    # ENGINE C: Vision + OCR Engine
    # ----------------------------------------------------
    extracted_image_texts = []
    for idx, img_bytes in enumerate(image_bytes_list):
        label = f"Image #{idx + 1}"

        # C.1 OCR Text Extraction
        ocr_res = extract_text_from_image(img_bytes)
        if ocr_res.text:
            extracted_image_texts.append(ocr_res.text)
            # Re-run deterministic banned term check on text found in images!
            img_term_findings = scan_terminology(ocr_res.text, glossary_terms)
            for itf in img_term_findings:
                itf.title = f"[Image OCR] {itf.title}"
                itf.confidence_score = round(itf.confidence_score * ocr_res.confidence, 2)
                aggregated_findings.append(itf)

        # C.2 Color Palette & Image Contrast
        color_findings = check_image_color_compliance(img_bytes, palette_assets, image_label=label)
        aggregated_findings.extend(color_findings)

        # C.3 Logo Integrity
        logo_findings = check_logo_integrity(img_bytes, logo_assets, image_label=label)
        aggregated_findings.extend(logo_findings)

    # ----------------------------------------------------
    # Aggregation, Scoring & Severity Sorting
    # ----------------------------------------------------
    # Deduplicate findings by title and detected content
    unique_findings: List[FindingBase] = []
    seen_keys = set()
    for f in aggregated_findings:
        key = (f.rule_id, f.detected_content.strip().lower())
        if key not in seen_keys:
            seen_keys.add(key)
            unique_findings.append(f)

    # Sort: HIGH -> MEDIUM -> LOW -> INFO
    severity_order = {
        FindingSeverity.HIGH: 0,
        FindingSeverity.MEDIUM: 1,
        FindingSeverity.LOW: 2,
        FindingSeverity.INFO: 3,
    }
    unique_findings.sort(key=lambda x: severity_order.get(x.severity, 4))

    audit_score = calculate_brand_compliance_score(unique_findings)

    # ----------------------------------------------------
    # Persist ContentVersion and Findings in Database
    # ----------------------------------------------------
    # Determine version number
    version_count_stmt = select(ContentVersion).where(ContentVersion.submission_id == submission_id)
    existing_versions = db.execute(version_count_stmt).scalars().all()
    next_ver_num = len(existing_versions) + 1

    content_version = ContentVersion(
        submission_id=submission_id,
        version_number=next_ver_num,
        raw_content=content,
        document_path=document_path,
        has_images=len(image_bytes_list) > 0,
        image_metadata=[{"index": i, "size": len(b)} for i, b in enumerate(image_bytes_list)],
        audit_score=audit_score,
    )
    db.add(content_version)
    db.flush()

    db_findings: List[Finding] = []
    for f in unique_findings:
        # Enforce that all HIGH severity findings or low-confidence findings require human review
        must_review = f.requires_human_review or f.severity == FindingSeverity.HIGH or f.confidence_score < 0.85

        db_finding = Finding(
            content_version_id=content_version.id,
            rule_id=f.rule_id,
            engine=f.engine,
            category=f.category,
            severity=f.severity,
            title=f.title,
            detected_content=f.detected_content,
            explanation=f.explanation,
            source_citation=f.source_citation,
            supporting_passage=f.supporting_passage,
            suggested_correction=f.suggested_correction,
            confidence_score=f.confidence_score,
            requires_human_review=must_review,
        )
        db.add(db_finding)
        db_findings.append(db_finding)

    # Update Submission status
    submission_stmt = select(Submission).where(Submission.id == submission_id)
    submission = db.execute(submission_stmt).scalar_one_or_none()
    if submission:
        submission.current_status = SubmissionStatus.AUDITED
        db.add(submission)

    # Audit Trail
    log = AuditLog(
        organization_id=organization_id,
        user_id=user_id,
        event_type="AUDIT_RUN",
        entity_type="ContentVersion",
        entity_id=content_version.id,
        details={
            "submission_id": submission_id,
            "version": next_ver_num,
            "findings_count": len(db_findings),
            "score": audit_score,
        },
    )
    db.add(log)
    db.commit()

    summary = {
        "score": audit_score,
        "total_findings": len(db_findings),
        "high_severity": sum(1 for f in db_findings if f.severity == FindingSeverity.HIGH),
        "medium_severity": sum(1 for f in db_findings if f.severity == FindingSeverity.MEDIUM),
        "low_severity": sum(1 for f in db_findings if f.severity == FindingSeverity.LOW),
        "ocr_texts": extracted_image_texts,
    }

    return AuditPipelineResult(
        content_version_id=content_version.id,
        audit_score=audit_score,
        findings=db_findings,
        summary=summary,
    )
