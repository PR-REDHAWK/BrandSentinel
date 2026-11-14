import io
from typing import List, Optional
from PIL import Image

from app.models.audit import AuditEngine, FindingSeverity
from app.models.knowledge import BrandAsset
from app.schemas.finding import FindingBase


def check_logo_integrity(
    image_bytes: bytes,
    approved_logo_assets: List[BrandAsset],
    image_label: str = "Image Asset",
) -> List[FindingBase]:
    """
    Check logo aspect ratio distortion and dimension guidelines.
    """
    findings: List[FindingBase] = []
    try:
        pil_img = Image.open(io.BytesIO(image_bytes))
    except Exception:
        return findings

    width, height = pil_img.size
    aspect_ratio = round(width / float(height), 2)

    for logo in approved_logo_assets:
        if logo.asset_type == "LOGO" and logo.aspect_ratio:
            expected_ratio = logo.aspect_ratio
            ratio_diff = abs(aspect_ratio - expected_ratio) / expected_ratio

            # Tolerance > 15% indicates stretched or squished logo
            if ratio_diff > 0.15:
                findings.append(
                    FindingBase(
                        rule_id="VIS-03-LOGO-DISTORTION",
                        engine=AuditEngine.VISION_OCR,
                        category="VISUAL",
                        severity=FindingSeverity.HIGH,
                        title=f"Distorted Brand Logo Aspect Ratio ({aspect_ratio}:1 vs {expected_ratio}:1)",
                        detected_content=f"{image_label}: Dimensions {width}x{height} (Ratio {aspect_ratio}:1)",
                        explanation=(
                            f"The detected logo aspect ratio ({aspect_ratio}:1) deviates from the official "
                            f"approved aspect ratio of {expected_ratio}:1. Brand guidelines prohibit distorting or stretching logos."
                        ),
                        source_citation=f"Brand Assets — {logo.name}",
                        supporting_passage=f"Official Logo: {logo.name}, Approved Aspect Ratio: {expected_ratio}:1",
                        suggested_correction=f"Lock proportions to {expected_ratio}:1 aspect ratio.",
                        confidence_score=0.92,
                        requires_human_review=True,
                    )
                )

    return findings
