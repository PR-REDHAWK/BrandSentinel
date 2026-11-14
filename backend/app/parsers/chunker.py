import re
from typing import Any, Dict, List


class TextChunk:
    def __init__(
        self,
        chunk_index: int,
        content: str,
        section_title: str = "",
        page_number: int = 1,
        metadata: Dict[str, Any] = None,
    ):
        self.chunk_index = chunk_index
        self.content = content.strip()
        self.section_title = section_title
        self.page_number = page_number
        self.metadata = metadata or {}


def chunk_text(
    text: str,
    chunk_size: int = 600,
    overlap: int = 100,
    page_number: int = 1,
    section_title: str = "",
) -> List[TextChunk]:
    """
    Split text into overlapping semantic chunks respecting sentence or paragraph boundaries.
    """
    if not text or not text.strip():
        return []

    # Clean redundant whitespace
    clean_text = re.sub(r"\r\n", "\n", text).strip()
    paragraphs = [p.strip() for p in clean_text.split("\n\n") if p.strip()]

    chunks: List[TextChunk] = []
    current_chunk = ""
    chunk_idx = 0

    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) + 2 <= chunk_size:
            current_chunk = f"{current_chunk}\n\n{paragraph}".strip()
        else:
            if current_chunk:
                chunks.append(
                    TextChunk(
                        chunk_index=chunk_idx,
                        content=current_chunk,
                        section_title=section_title,
                        page_number=page_number,
                    )
                )
                chunk_idx += 1

                # Carry over overlap from the end of the previous chunk
                words = current_chunk.split()
                overlap_words = words[-max(1, overlap // 6):] if len(words) > 10 else []
                current_chunk = " ".join(overlap_words) + ("\n\n" if overlap_words else "") + paragraph
            else:
                # Paragraph itself exceeds chunk_size, split by sentences
                sentences = re.split(r"(?<=[.!?]) +", paragraph)
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) + 1 <= chunk_size:
                        current_chunk = f"{current_chunk} {sentence}".strip()
                    else:
                        if current_chunk:
                            chunks.append(
                                TextChunk(
                                    chunk_index=chunk_idx,
                                    content=current_chunk,
                                    section_title=section_title,
                                    page_number=page_number,
                                )
                            )
                            chunk_idx += 1
                        current_chunk = sentence

    if current_chunk.strip():
        chunks.append(
            TextChunk(
                chunk_index=chunk_idx,
                content=current_chunk,
                section_title=section_title,
                page_number=page_number,
            )
        )

    return chunks
