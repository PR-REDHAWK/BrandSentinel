import re
from typing import List
from app.models.audit import AuditEngine, FindingSeverity
from app.models.knowledge import GlossaryTerm
from app.schemas.finding import FindingBase


def scan_terminology(content: str, glossary_terms: List[GlossaryTerm]) -> List[FindingBase]:
    """
    Deterministic scanner for banned terms and non-standard glossary usage.
    Uses regex word boundaries to prevent false positives (e.g. 'class' in 'classic').
    """
    findings: List[FindingBase] = []
    if not content or not glossary_terms:
        return findings

    for term_rule in glossary_terms:
        term = term_rule.term.strip()
        if not term:
            continue

        flags = 0 if term_rule.case_sensitive else re.IGNORECASE
        pattern = r"\b" + re.escape(term) + r"\b"

        for match in re.finditer(pattern, content, flags):
            matched_text = match.group(0)

            if term_rule.is_banned:
                # Banned Term Violation
                fix = term_rule.preferred_term or (f"Remove or replace '{matched_text}'")
                findings.append(
                    FindingBase(
                        rule_id="RULE-01-BANNED-TERM",
                        engine=AuditEngine.DETERMINISTIC,
                        category="TERMINOLOGY",
                        severity=FindingSeverity.HIGH,
                        title=f"Banned Terminology: '{matched_text}'",
                        detected_content=matched_text,
                        explanation=(
                            f"The term '{matched_text}' is registered as strictly banned. "
                            f"Rule definition: {term_rule.definition_or_rule}"
                        ),
                        source_citation="Organization Banned Terms Registry",
                        supporting_passage=f"Banned term: '{term}'. Rule: {term_rule.definition_or_rule}",
                        suggested_correction=fix,
                        confidence_score=1.0,
                        requires_human_review=True,
                    )
                )
            elif term_rule.preferred_term and matched_text.lower() != term_rule.preferred_term.lower():
                # Non-Preferred Glossary Usage
                findings.append(
                    FindingBase(
                        rule_id="RULE-02-GLOSSARY-MISMATCH",
                        engine=AuditEngine.DETERMINISTIC,
                        category="TERMINOLOGY",
                        severity=FindingSeverity.MEDIUM,
                        title=f"Inconsistent Brand Terminology: '{matched_text}'",
                        detected_content=matched_text,
                        explanation=(
                            f"Use of '{matched_text}' deviates from official brand terminology. "
                            f"Preferred brand term is '{term_rule.preferred_term}'. "
                            f"Context: {term_rule.definition_or_rule}"
                        ),
                        source_citation="Organization Brand Glossary",
                        supporting_passage=f"Term: '{term}'. Preferred: '{term_rule.preferred_term}'. Definition: {term_rule.definition_or_rule}",
                        suggested_correction=term_rule.preferred_term,
                        confidence_score=1.0,
                        requires_human_review=False,
                    )
                )

    return findings
