import io
import math
from typing import List, Optional, Tuple
from PIL import Image

from app.engines.deterministic.contrast import calculate_contrast_ratio, hex_to_rgb
from app.models.audit import AuditEngine, FindingSeverity
from app.models.knowledge import BrandAsset
from app.schemas.finding import FindingBase


def rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{r:02x}{g:02x}{b:02x}".upper()


def extract_dominant_colors(pil_image: Image.Image, max_colors: int = 5) -> List[Tuple[str, float]]:
    """
    Extract the top dominant colors from an image along with their percentage coverage.
    """
    # Resize image for fast processing while preserving color distribution
    img = pil_image.convert("RGB")
    img = img.resize((150, 150))

    # Quantize using Pillow's adaptive palette
    quantized = img.quantize(colors=max_colors, method=Image.Quantize.MEDIANCUT)
    palette = quantized.getpalette()[: max_colors * 3]
    color_counts = quantized.getcolors()

    if not color_counts:
        return []

    total_pixels = sum(count for count, _ in color_counts)
    results: List[Tuple[str, float]] = []

    for count, index in sorted(color_counts, reverse=True):
        r = palette[index * 3]
        g = palette[index * 3 + 1]
        b = palette[index * 3 + 2]
        hex_color = rgb_to_hex(r, g, b)
        pct = round(count / total_pixels, 3)
        results.append((hex_color, pct))

    return results


def color_distance(hex1: str, hex2: str) -> float:
    """Euclidean distance in sRGB color space (0 to 441.67)."""
    r1, g1, b1 = hex_to_rgb(hex1)
    r2, g2, b2 = hex_to_rgb(hex2)
    return math.sqrt((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2)


def check_image_color_compliance(
    image_bytes: bytes,
    approved_palettes: List[BrandAsset],
    image_label: str = "Uploaded Image",
) -> List[FindingBase]:
    """
    Check image dominant colors against approved brand color assets.
    Also calculates contrast between dominant background and foreground elements.
    """
    findings: List[FindingBase] = []
    try:
        pil_img = Image.open(io.BytesIO(image_bytes))
    except Exception:
        return findings

    dominant_colors = extract_dominant_colors(pil_img, max_colors=5)
    if not dominant_colors:
        return findings

    # Collect all approved brand hex colors
    approved_hex_set = []
    for asset in approved_palettes:
        if asset.hex_colors:
            approved_hex_set.extend([c.upper() for c in asset.hex_colors])

    # 1. Palette Consistency Check
    if approved_hex_set:
        for hex_col, pct in dominant_colors:
            # Only evaluate colors that take up at least 15% of the visual space (main theme colors)
            if pct < 0.15:
                continue
            # Neutral white or pure black backgrounds are universally permissible
            if hex_col in ["#FFFFFF", "#000000", "#F8F9FA", "#0F172A"]:
                continue

            # Minimum distance to any approved color
            min_dist = min(color_distance(hex_col, app_col) for app_col in approved_hex_set)

            # Distance > 110 indicates an unapproved color family (e.g. bright purple instead of brand navy)
            if min_dist > 110.0:
                findings.append(
                    FindingBase(
                        rule_id="VIS-01-OFFBRAND-COLOR",
                        engine=AuditEngine.VISION_OCR,
                        category="VISUAL",
                        severity=FindingSeverity.MEDIUM,
                        title=f"Off-Brand Dominant Color ({hex_col})",
                        detected_content=f"Color {hex_col} covers {int(pct*100)}% of {image_label}",
                        explanation=(
                            f"The dominant color {hex_col} in this visual asset deviates significantly "
                            f"from your approved organization palette: {', '.join(approved_hex_set)}."
                        ),
                        source_citation="Brand Assets — Official Color Palette",
                        supporting_passage=f"Approved colors: {', '.join(approved_hex_set)}",
                        suggested_correction=f"Align visual theme with approved brand colors: {approved_hex_set[0]}.",
                        confidence_score=0.90,
                        requires_human_review=True,
                    )
                )

    # 2. Contrast Check for Image Banner Text / Foreground
    if len(dominant_colors) >= 2:
        top_color, _ = dominant_colors[0]
        second_color, _ = dominant_colors[1]
        contrast = calculate_contrast_ratio(top_color, second_color)

        if contrast < 4.5:
            findings.append(
                FindingBase(
                    rule_id="VIS-02-IMAGE-LOW-CONTRAST",
                    engine=AuditEngine.VISION_OCR,
                    category="ACCESSIBILITY",
                    severity=FindingSeverity.HIGH if contrast < 3.0 else FindingSeverity.MEDIUM,
                    title=f"Low Visual Contrast in Image ({contrast}:1)",
                    detected_content=f"Image primary colors: {top_color} and {second_color} in {image_label}",
                    explanation=(
                        f"The contrast ratio between the primary dominant visual layers is {contrast}:1, "
                        "which fails the WCAG 2.2 standard of 4.5:1. Text embedded on this background may be unreadable."
                    ),
                    source_citation="W3C WCAG 2.2 Success Criterion 1.4.3 (Contrast Minimum)",
                    supporting_passage="Text and images of text must have a contrast ratio of at least 4.5:1.",
                    suggested_correction="Increase contrast between text overlay and image background.",
                    confidence_score=0.88,
                    requires_human_review=True,
                )
            )

    return findings
