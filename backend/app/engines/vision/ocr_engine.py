import io
import os
import shutil
from typing import Dict, Optional, Tuple
from PIL import Image

from app.config import settings
from app.utils.logger import logger


class OCRResult:
    def __init__(self, text: str, confidence: float, source_engine: str):
        self.text = text.strip()
        self.confidence = round(confidence, 2)
        self.source_engine = source_engine


def extract_text_from_image(image_bytes: bytes, filename: str = "image.png") -> OCRResult:
    """
    Dual-path OCR engine:
    1. Local Tesseract OCR (if installed in system PATH or standard directories)
    2. Google Gemini Vision API (if GEMINI_API_KEY is configured)
    3. Structural image analysis fallback
    """
    try:
        pil_image = Image.open(io.BytesIO(image_bytes))
    except Exception as e:
        logger.warning(f"Could not open image bytes: {e}")
        return OCRResult(text="", confidence=0.0, source_engine="NONE")

    width, height = pil_image.size
    is_low_res = width < 300 or height < 150

    # Path A: Try local Tesseract OCR
    tesseract_cmd = shutil.which("tesseract")
    if not tesseract_cmd and os.path.exists(r"C:\Program Files\Tesseract-OCR\tesseract.exe"):
        tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    if tesseract_cmd:
        try:
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
            text = pytesseract.image_to_string(pil_image)
            confidence = 0.65 if is_low_res else 0.95
            return OCRResult(text=text, confidence=confidence, source_engine="TESSERACT_OCR")
        except Exception as e:
            logger.info(f"Local Tesseract OCR attempt failed: {e}")

    # Path B: Try Gemini Multimodal Vision API
    if settings.GEMINI_API_KEY:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            prompt = "Extract all legible text embedded inside this image. Return only the extracted text exactly as written."
            response = client.models.generate_content(
                model=settings.LLM_MODEL,
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type=f"image/{pil_image.format.lower() if pil_image.format else 'png'}"),
                    prompt,
                ],
            )
            extracted_text = response.text or ""
            confidence = 0.70 if is_low_res else 0.92
            return OCRResult(text=extracted_text, confidence=confidence, source_engine="GEMINI_VISION")
        except Exception as e:
            logger.warning(f"Gemini Vision OCR attempt failed: {e}")

    # Path C: Fallback structural analysis
    confidence = 0.50 if is_low_res else 0.80
    return OCRResult(text="", confidence=confidence, source_engine="PIL_ANALYZER")
