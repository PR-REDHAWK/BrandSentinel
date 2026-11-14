import math
import re
from typing import List, Optional, Tuple
from app.models.audit import AuditEngine, FindingSeverity
from app.schemas.finding import FindingBase


def hex_to_rgb(hex_code: str) -> Tuple[int, int, int]:
    """Parse a 3 or 6 digit hex color code into (R, G, B) integers (0-255)."""
    h = hex_code.strip().lstrip("#")
    if len(h) == 3:
        h = "".join([c * 2 for c in h])
    if len(h) != 6:
        raise ValueError(f"Invalid hex color format: '{hex_code}'")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def calculate_relative_luminance(rgb: Tuple[int, int, int]) -> float:
    """
    Calculate WCAG 2.2 relative luminance of an sRGB color.
    https://www.w3.org/WAI/GL/wiki/Relative_luminance
    """
    channels = []
    for val in rgb:
        s = val / 255.0
        if s <= 0.04045:
            c = s / 12.92
        else:
            c = math.pow((s + 0.055) / 1.055, 2.4)
        channels.append(c)

    # L = 0.2126 * R + 0.7152 * G + 0.0722 * B
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def calculate_contrast_ratio(color1: str, color2: str) -> float:
    """
    Calculate the WCAG contrast ratio between two hex colors.
    Returns float value between 1.0 and 21.0.
    """
    rgb1 = hex_to_rgb(color1)
    rgb2 = hex_to_rgb(color2)
    l1 = calculate_relative_luminance(rgb1)
    l2 = calculate_relative_luminance(rgb2)

    lighter = max(l1, l2)
    darker = min(l1, l2)
    ratio = (lighter + 0.05) / (darker + 0.05)
    return round(ratio, 2)


def check_wcag_contrast(
    foreground_hex: str,
    background_hex: str,
    is_large_text: bool = False,
    context_label: str = "Text element",
) -> Optional[FindingBase]:
    """
    Evaluate contrast against WCAG 2.2 Success Criterion 1.4.3 (Level AA).
    - Normal text threshold: 4.5:1
    - Large text threshold (>=18pt or >=14pt bold): 3.0:1
    """
    try:
        ratio = calculate_contrast_ratio(foreground_hex, background_hex)
    except Exception:
        return None

    required_ratio = 3.0 if is_large_text else 4.5
    text_desc = "large text (>=18pt or 14pt bold)" if is_large_text else "body / normal text"

    if ratio < required_ratio:
        return FindingBase(
            rule_id="RULE-03-WCAG-CONTRAST",
            engine=AuditEngine.DETERMINISTIC,
            category="ACCESSIBILITY",
            severity=FindingSeverity.HIGH if ratio < 3.0 else FindingSeverity.MEDIUM,
            title=f"WCAG 2.2 Contrast Failure ({ratio}:1 vs {required_ratio}:1)",
            detected_content=f"{context_label}: FG={foreground_hex}, BG={background_hex}",
            explanation=(
                f"Contrast ratio between foreground {foreground_hex} and background {background_hex} "
                f"is {ratio}:1, failing WCAG 2.2 Level AA requirement of {required_ratio}:1 for {text_desc}."
            ),
            source_citation="W3C WCAG 2.2 Guideline 1.4.3 (Contrast Minimum)",
            supporting_passage=(
                "The visual presentation of text and images of text has a contrast ratio of at least 4.5:1, "
                "except for large-scale text which requires at least 3:1."
            ),
            suggested_correction=(
                f"Increase lightness contrast between {foreground_hex} and {background_hex} "
                f"to exceed {required_ratio}:1 (e.g. darken text or lighten background)."
            ),
            confidence_score=1.0,
            requires_human_review=True,
        )

    return None


def scan_html_css_contrast(content: str) -> List[FindingBase]:
    """
    Scans content containing inline CSS or HTML color combinations for contrast violations.
    e.g. color: #999; background-color: #fff;
    """
    findings: List[FindingBase] = []
    # Pattern to find style tags or inline styles with color and background
    style_pattern = re.compile(
        r'style=["\'][^"\']*(?:color:\s*(#[0-9a-fA-F]{3,6}))[^"\']*(?:background(?:-color)?:\s*(#[0-9a-fA-F]{3,6}))',
        re.IGNORECASE,
    )
    for match in style_pattern.finditer(content):
        fg, bg = match.group(1), match.group(2)
        finding = check_wcag_contrast(fg, bg, is_large_text=False, context_label="Inline styled element")
        if finding:
            findings.append(finding)

    # Reverse order pattern (background first, then color)
    style_pattern_rev = re.compile(
        r'style=["\'][^"\']*(?:background(?:-color)?:\s*(#[0-9a-fA-F]{3,6}))[^"\']*(?:color:\s*(#[0-9a-fA-F]{3,6}))',
        re.IGNORECASE,
    )
    for match in style_pattern_rev.finditer(content):
        bg, fg = match.group(1), match.group(2)
        finding = check_wcag_contrast(fg, bg, is_large_text=False, context_label="Inline styled element")
        if finding:
            findings.append(finding)

    return findings
