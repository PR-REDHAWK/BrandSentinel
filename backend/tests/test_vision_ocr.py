import io
from PIL import Image, ImageDraw
import pytest

from app.engines.vision.color_checker import (
    check_image_color_compliance,
    color_distance,
    extract_dominant_colors,
)
from app.engines.vision.logo_checker import check_logo_integrity
from app.engines.vision.ocr_engine import extract_text_from_image
from app.models.knowledge import BrandAsset


def create_solid_image(hex_color: str, width: int = 200, height: int = 100) -> bytes:
    img = Image.new("RGB", (width, height), color=hex_color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def create_two_tone_image(color1: str, color2: str, width: int = 200, height: int = 100) -> bytes:
    img = Image.new("RGB", (width, height), color=color1)
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, width // 2, height], fill=color2)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_dominant_color_extraction():
    img_bytes = create_solid_image("#FF6B35", width=100, height=100)
    pil_img = Image.open(io.BytesIO(img_bytes))
    dominant = extract_dominant_colors(pil_img, max_colors=2)

    assert len(dominant) >= 1
    assert dominant[0][0] == "#FF6B35"
    assert dominant[0][1] >= 0.95


def test_off_brand_color_detection():
    # Approved palette is Navy (#0B2046) and White (#FFFFFF)
    palettes = [
        BrandAsset(
            id="1",
            organization_id="org1",
            asset_type="PALETTE",
            name="Official Theme",
            hex_colors=["#0B2046", "#FFFFFF"],
        )
    ]

    # Image is solid Magenta (#FF00FF)
    magenta_img = create_solid_image("#FF00FF")
    findings = check_image_color_compliance(magenta_img, approved_palettes=palettes)

    offbrand_findings = [f for f in findings if f.rule_id == "VIS-01-OFFBRAND-COLOR"]
    assert len(offbrand_findings) >= 1
    assert "#FF00FF" in offbrand_findings[0].detected_content


def test_image_low_contrast_detection():
    # Low contrast: Light Gray #CCCCCC on White #FFFFFF (~1.6:1)
    low_contrast_img = create_two_tone_image("#CCCCCC", "#FFFFFF")
    findings = check_image_color_compliance(low_contrast_img, approved_palettes=[])

    contrast_findings = [f for f in findings if f.rule_id == "VIS-02-IMAGE-LOW-CONTRAST"]
    assert len(contrast_findings) >= 1
    assert "fails the WCAG 2.2" in contrast_findings[0].explanation


def test_logo_distortion_check():
    logo_asset = BrandAsset(
        id="logo1",
        organization_id="org1",
        asset_type="LOGO",
        name="Horizontal Wordmark",
        aspect_ratio=3.5,  # Expected 3.5:1
    )

    # Distorted image with 1.0 aspect ratio (square instead of horizontal banner)
    square_img = create_solid_image("#0B2046", width=200, height=200)
    findings = check_logo_integrity(square_img, approved_logo_assets=[logo_asset])

    assert len(findings) == 1
    assert findings[0].rule_id == "VIS-03-LOGO-DISTORTION"
    assert "1.0:1" in findings[0].detected_content


def test_ocr_engine_runner():
    # Test OCR runner with simple banner
    test_img = create_solid_image("#0B2046", width=400, height=200)
    result = extract_text_from_image(test_img)
    assert result.confidence > 0.0
    assert result.source_engine in ["TESSERACT_OCR", "GEMINI_VISION", "PIL_ANALYZER"]
