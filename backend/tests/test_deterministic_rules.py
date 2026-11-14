import pytest
from app.engines.deterministic.accessibility import scan_accessibility
from app.engines.deterministic.contrast import (
    calculate_contrast_ratio,
    check_wcag_contrast,
    scan_html_css_contrast,
)
from app.engines.deterministic.terms import scan_terminology
from app.models.knowledge import GlossaryTerm


def test_banned_term_detection():
    glossary = [
        GlossaryTerm(
            id="1",
            organization_id="org1",
            term="dirt cheap",
            is_banned=True,
            preferred_term="cost-effective",
            definition_or_rule="Colloquial slang devaluing product tier.",
            case_sensitive=False,
        ),
        GlossaryTerm(
            id="2",
            organization_id="org1",
            term="rock-bottom",
            is_banned=True,
            preferred_term="competitive",
            definition_or_rule="Slang.",
            case_sensitive=False,
        ),
    ]

    text = "We offer dirt cheap pricing and rock-bottom subscription fees."
    findings = scan_terminology(text, glossary)

    assert len(findings) == 2
    rule_ids = [f.rule_id for f in findings]
    assert "RULE-01-BANNED-TERM" in rule_ids
    assert findings[0].suggested_correction == "cost-effective"
    assert findings[0].requires_human_review is True


def test_word_boundary_prevents_false_positives():
    glossary = [
        GlossaryTerm(
            id="1",
            organization_id="org1",
            term="cheap",
            is_banned=True,
            definition_or_rule="Use affordable.",
            case_sensitive=False,
        )
    ]
    # "cheapskate" contains "cheap" as substring, but word boundary \b should not trigger on whole word
    safe_text = "This is a cheapskate behavior."
    findings = scan_terminology(safe_text, glossary)
    assert len(findings) == 0

    violating_text = "This is a cheap solution."
    findings2 = scan_terminology(violating_text, glossary)
    assert len(findings2) == 1


def test_glossary_preferred_usage():
    glossary = [
        GlossaryTerm(
            id="1",
            organization_id="org1",
            term="end-user",
            is_banned=False,
            preferred_term="customer",
            definition_or_rule="Prefer customer over technical jargon.",
            case_sensitive=False,
        )
    ]
    text = "We prioritize every end-user experience."
    findings = scan_terminology(text, glossary)

    assert len(findings) == 1
    assert findings[0].rule_id == "RULE-02-GLOSSARY-MISMATCH"
    assert findings[0].suggested_correction == "customer"


def test_wcag_contrast_math():
    # Black on White: 21:1
    ratio_bw = calculate_contrast_ratio("#000000", "#FFFFFF")
    assert ratio_bw == 21.0

    # White on White: 1:1
    ratio_ww = calculate_contrast_ratio("#FFFFFF", "#FFFFFF")
    assert ratio_ww == 1.0

    # Low contrast gray #999999 on white #FFFFFF (~2.84:1)
    ratio_low = calculate_contrast_ratio("#999999", "#FFFFFF")
    assert ratio_low < 3.0

    finding = check_wcag_contrast("#999999", "#FFFFFF", is_large_text=False)
    assert finding is not None
    assert finding.rule_id == "RULE-03-WCAG-CONTRAST"
    assert finding.severity.value == "HIGH"

    # High contrast gray #595959 on white #FFFFFF (>4.5:1)
    ratio_ok = calculate_contrast_ratio("#595959", "#FFFFFF")
    assert ratio_ok >= 4.5
    finding_ok = check_wcag_contrast("#595959", "#FFFFFF", is_large_text=False)
    assert finding_ok is None


def test_scan_html_css_contrast():
    html_snippet = '<p style="color: #aaaaaa; background-color: #ffffff;">Subtle caption</p>'
    findings = scan_html_css_contrast(html_snippet)
    assert len(findings) >= 1
    assert findings[0].rule_id == "RULE-03-WCAG-CONTRAST"


def test_missing_alt_text():
    markdown_content = "Here is our product banner: ![](https://acme.com/banner.png)"
    findings = scan_accessibility(markdown_content)

    alt_findings = [f for f in findings if f.rule_id == "RULE-04-MISSING-ALT"]
    assert len(alt_findings) == 1
    assert "https://acme.com/banner.png" in alt_findings[0].explanation


def test_missing_html_language():
    html_content = "<html><head><title>No Lang</title></head><body><h1>Welcome</h1></body></html>"
    findings = scan_accessibility(html_content, is_html=True)

    lang_findings = [f for f in findings if f.rule_id == "RULE-05-MISSING-LANG"]
    assert len(lang_findings) == 1


def test_all_caps_shouting():
    content = "You must BUY THIS INCREDIBLE PRODUCT TODAY to unlock full features."
    findings = scan_accessibility(content)

    caps_findings = [f for f in findings if f.rule_id == "RULE-06-FORMATTING-ALLCAPS"]
    assert len(caps_findings) == 1
    assert "BUY THIS INCREDIBLE PRODUCT TODAY" in caps_findings[0].detected_content
