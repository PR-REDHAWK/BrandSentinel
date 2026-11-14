import io
from typing import Any, Dict, List
import docx
from PIL import Image

from app.parsers.chunker import TextChunk, chunk_text


class ParsedDocxDocument:
    def __init__(self, full_text: str, chunks: List[TextChunk], images: List[Dict[str, Any]], paragraph_count: int):
        self.full_text = full_text
        self.chunks = chunks
        self.images = images
        self.paragraph_count = paragraph_count


def parse_docx(file_path: str, extract_images: bool = True) -> ParsedDocxDocument:
    """
    Ingest a DOCX file using python-docx. Extracts paragraphs, headers, tables,
    and embedded images.
    """
    doc = docx.Document(file_path)
    text_sections: List[str] = []
    current_heading = "General"

    for p in doc.paragraphs:
        txt = p.text.strip()
        if not txt:
            continue
        if p.style and "Heading" in p.style.name:
            current_heading = txt
            text_sections.append(f"\n### {txt}\n")
        else:
            text_sections.append(txt)

    # Process tables
    for table_idx, table in enumerate(doc.tables):
        table_rows = []
        for row in table.rows:
            row_data = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if row_data:
                table_rows.append(" | ".join(row_data))
        if table_rows:
            text_sections.append(f"\n[Table {table_idx + 1}]\n" + "\n".join(table_rows))

    full_text = "\n\n".join(text_sections)
    raw_chunks = chunk_text(full_text, chunk_size=600, overlap=100, section_title=current_heading)

    # Extract images from relationships
    extracted_images: List[Dict[str, Any]] = []
    if extract_images:
        for rel in doc.part.rels.values():
            if "image" in rel.target_ref:
                try:
                    img_part = rel.target_part
                    img_bytes = img_part.blob
                    pil_img = Image.open(io.BytesIO(img_bytes))
                    extracted_images.append(
                        {
                            "width": pil_img.width,
                            "height": pil_img.height,
                            "format": pil_img.format or "PNG",
                            "raw_bytes": img_bytes,
                        }
                    )
                except Exception:
                    continue

    return ParsedDocxDocument(
        full_text=full_text,
        chunks=raw_chunks,
        images=extracted_images,
        paragraph_count=len(doc.paragraphs),
    )
