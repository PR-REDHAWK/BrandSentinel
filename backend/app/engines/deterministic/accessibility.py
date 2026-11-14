import re
from typing import Any, Dict, List
from app.models.audit import AuditEngine, FindingSeverity
from app.schemas.finding import FindingBase


def scan_accessibility(
    content: str,
    images_metadata: List[Dict[str, Any]] = None,
    is_html: bool = False,
) -> List[FindingBase]:
    """
    Deterministic accessibility and formatting checks:
    - Missing image alt text (WCAG SC 1.1.1)
    - Missing document language declaration (WCAG SC 3.1.1)
    - Excessive uppercase shouting / formatting rules
    - Empty links (WCAG SC 2.4.4)
    """
    findings: List[FindingBase] = []
    if not content:
        content = ""

    # 1. Missing Image Alt Text in Markdown: ![ ](url) or ![](url)
    md_img_pattern = re.compile(r"!\[(.*?)\]\((.*?)\)")
    for match in md_img_pattern.finditer(content):
        alt_text = match.group(1).strip()
        img_url = match.group(2).strip()
        if not alt_text:
            findings.append(
                FindingBase(
                    rule_id="RULE-04-MISSING-ALT",
                    engine=AuditEngine.DETERMINISTIC,
                    category="ACCESSIBILITY",
                    severity=FindingSeverity.HIGH,
                    title="Missing Image Alt-Text",
                    detected_content=match.group(0),
                    explanation=(
                        f"Image pointing to '{img_url}' has an empty or missing alt text attribute. "
                        "Alt text is required for screen readers and search engines."
                    ),
                    source_citation="W3C WCAG 2.2 Success Criterion 1.1.1 (Non-text Content)",
                    supporting_passage="All non-text content that is presented to the user has a text alternative that serves the equivalent purpose.",
                    suggested_correction=f"![Descriptive summary of image]({img_url})",
                    confidence_score=1.0,
                    requires_human_review=False,
                )
            )

    # 2. Missing Image Alt Text in HTML: <img ...> with missing or empty alt=""
    html_img_pattern = re.compile(r"<img\b([^>]*)>", re.IGNORECASE)
    for match in html_img_pattern.finditer(content):
        attrs = match.group(1)
        alt_match = re.search(r'alt=["\']([^"\']*)["\']', attrs, re.IGNORECASE)
        if not alt_match or not alt_match.group(1).strip():
            findings.append(
                FindingBase(
                    rule_id="RULE-04-MISSING-ALT",
                    engine=AuditEngine.DETERMINISTIC,
                    category="ACCESSIBILITY",
                    severity=FindingSeverity.HIGH,
                    title="Missing HTML Image Alt Attribute",
                    detected_content=match.group(0),
                    explanation=(
                        "HTML <img> element is missing a descriptive alt attribute. "
                        "Fails WCAG 2.2 Level A non-text content criteria."
                    ),
                    source_citation="W3C WCAG 2.2 Success Criterion 1.1.1 (Non-text Content)",
                    supporting_passage="All non-text content that is presented to the user has a text alternative that serves the equivalent purpose.",
                    suggested_correction='Add alt="Descriptive summary of image"',
                    confidence_score=1.0,
                    requires_human_review=False,
                )
            )

    # 3. Document Language Declaration Check (WCAG SC 3.1.1)
    if is_html or "<html" in content.lower():
        html_tag_match = re.search(r"<html\b([^>]*)>", content, re.IGNORECASE)
        if html_tag_match:
            attrs = html_tag_match.group(1)
            lang_match = re.search(r'lang=["\'][^"\']+["\']', attrs, re.IGNORECASE)
            if not lang_match:
                findings.append(
                    FindingBase(
                        rule_id="RULE-05-MISSING-LANG",
                        engine=AuditEngine.DETERMINISTIC,
                        category="ACCESSIBILITY",
                        severity=FindingSeverity.MEDIUM,
                        title="Missing Document Language Declaration",
                        detected_content=html_tag_match.group(0),
                        explanation=(
                            "The <html> root element does not declare a language attribute (e.g. lang='en'). "
                            "Required for assistive technologies and text-to-speech engines."
                        ),
                        source_citation="W3C WCAG 2.2 Success Criterion 3.1.1 (Language of Page)",
                        supporting_passage="The default human language of each Web page can be programmatically determined.",
                        suggested_correction='<html lang="en">',
                        confidence_score=1.0,
                        requires_human_review=False,
                    )
                )

    # 4. Excessive Uppercase Shouting Check
    # Looks for sequences of 4 or more consecutive ALL-CAPS words (min 3 chars each)
    shout_pattern = re.compile(r"\b([A-Z]{3,}(?:\s+[A-Z]{3,}){3,})\b")
    for match in shout_pattern.finditer(content):
        shouted_text = match.group(0)
        # Exclude common acronym headers or legal disclaimers like "ALL RIGHTS RESERVED"
        if "ALL RIGHTS RESERVED" in shouted_text:
            continue
        findings.append(
            FindingBase(
                rule_id="RULE-06-FORMATTING-ALLCAPS",
                engine=AuditEngine.DETERMINISTIC,
                category="FORMATTING",
                severity=FindingSeverity.LOW,
                title="Excessive Uppercase Text (Shouting)",
                detected_content=shouted_text,
                explanation=(
                    "Continuous strings of all-caps text decrease readability and violate brand style conventions."
                ),
                source_citation="Brand Guidelines — Editorial Typography & Case Conventions",
                supporting_passage="Avoid ALL-CAPS styling for sentences or long phrases. Use title case or standard sentence case.",
                suggested_correction=shouted_text.title(),
                confidence_score=0.95,
                requires_human_review=False,
            )
        )

    # 5. Empty Hyperlinks Check
    empty_link_pattern = re.compile(r"<a\b[^>]*>\s*</a>|\[\s*\]\(([^)]+)\)", re.IGNORECASE)
    for match in empty_link_pattern.finditer(content):
        findings.append(
            FindingBase(
                rule_id="RULE-07-EMPTY-LINK",
                engine=AuditEngine.DETERMINISTIC,
                category="ACCESSIBILITY",
                severity=FindingSeverity.MEDIUM,
                title="Empty Hyperlink Detected",
                detected_content=match.group(0),
                explanation=(
                    "Hyperlink contains no anchor text or screen-reader accessible label."
                ),
                source_citation="W3C WCAG 2.2 Success Criterion 2.4.4 (Link Purpose in Context)",
                supporting_passage="The purpose of each link can be determined from the link text alone or from the link text together with its context.",
                suggested_correction="Add descriptive anchor text inside the hyperlink.",
                confidence_score=1.0,
                requires_human_review=False,
            )
        )

    return findings
