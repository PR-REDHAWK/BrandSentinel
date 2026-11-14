import io
from pathlib import Path
from typing import Any, Dict, List, Tuple
from PIL import Image
import pymupdf

from app.parsers.chunker import TextChunk, chunk_text


class ParsedPDFDocument:
    def __init__(self, full_text: str, chunks: List[TextChunk], images: List[Dict[str, Any]], page_count: int):
        self.full_text = full_text
        self.chunks = chunks
        self.images = images
        self.page_count = page_count


def parse_pdf(file_path: str, extract_images: bool = True) -> ParsedPDFDocument:
    """
    Ingest a PDF file using PyMuPDF. Extracts clean structured text, generates
    semantic chunks annotated with page numbers, and extracts embedded images.
    """
    doc = pymupdf.open(file_path)
    all_text_parts: List[str] = []
    all_chunks: List[TextChunk] = []
    extracted_images: List[Dict[str, Any]] = []

    global_chunk_counter = 0

    for page_idx in range(len(doc)):
        page_num = page_idx + 1
        page = doc[page_idx]

        # Extract text blocks
        page_text = page.get_text("text").strip()
        if page_text:
            all_text_parts.append(page_text)
            page_chunks = chunk_text(page_text, page_number=page_num, section_title=f"Page {page_num}")
            for c in page_chunks:
                c.chunk_index = global_chunk_counter
                global_chunk_counter += 1
                all_chunks.append(c)

        # Extract images if requested
        if extract_images:
            image_list = page.get_images(full=True)
            for img_index, img_info in enumerate(image_list):
                xref = img_info[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]

                try:
                    pil_img = Image.open(io.BytesIO(image_bytes))
                    extracted_images.append(
                        {
                            "page_number": page_num,
                            "index": img_index,
                            "width": pil_img.width,
                            "height": pil_img.height,
                            "format": image_ext,
                            "raw_bytes": image_bytes,
                        }
                    )
                except Exception:
                    continue

    page_count = len(doc)
    doc.close()
    full_text = "\n\n".join(all_text_parts)

    return ParsedPDFDocument(
        full_text=full_text,
        chunks=all_chunks,
        images=extracted_images,
        page_count=page_count,
    )
