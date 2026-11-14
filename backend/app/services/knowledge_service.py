import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.config import settings
from app.models.auth import User
from app.models.knowledge import (
    ApprovedFact,
    BrandAsset,
    DocumentChunk,
    GlossaryTerm,
    Guideline,
)
from app.models.log import AuditLog
from app.parsers.chunker import chunk_text
from app.parsers.csv_parser import parse_approved_facts_csv
from app.parsers.docx_parser import parse_docx
from app.parsers.pdf_parser import parse_pdf
from app.services.embedding_service import cosine_similarity, get_embeddings_batch
from app.utils.logger import logger


class KnowledgeService:
    @staticmethod
    def process_and_store_guideline(
        db: Session,
        organization_id: str,
        user_id: str,
        file_bytes: bytes,
        filename: str,
        title: str,
    ) -> Guideline:
        """
        Genuinely parses PDF/DOCX guidelines, chunks them, generates embeddings,
        and saves all entities to the database with organization-level isolation.
        """
        org_upload_dir = Path(settings.UPLOAD_DIR) / organization_id / "guidelines"
        org_upload_dir.mkdir(parents=True, exist_ok=True)
        file_path = org_upload_dir / filename
        with open(file_path, "wb") as f:
            f.write(file_bytes)

        file_ext = Path(filename).suffix.lower()
        chunks_to_create = []

        if file_ext == ".pdf":
            parsed_doc = parse_pdf(str(file_path), extract_images=False)
            chunks_to_create = parsed_doc.chunks
            file_type = "PDF"
        elif file_ext in [".docx", ".doc"]:
            parsed_doc = parse_docx(str(file_path), extract_images=False)
            chunks_to_create = parsed_doc.chunks
            file_type = "DOCX"
        else:
            text = file_bytes.decode("utf-8", errors="ignore")
            chunks_to_create = chunk_text(text)
            file_type = "TXT"

        guideline = Guideline(
            organization_id=organization_id,
            title=title,
            file_type=file_type,
            file_path=str(file_path),
            version=1,
            status="ACTIVE",
            created_by=user_id,
        )
        db.add(guideline)
        db.flush()  # Populates guideline.id

        chunk_texts = [c.content for c in chunks_to_create]
        embeddings = get_embeddings_batch(chunk_texts)

        for idx, c in enumerate(chunks_to_create):
            db_chunk = DocumentChunk(
                organization_id=organization_id,
                guideline_id=guideline.id,
                chunk_index=c.chunk_index,
                content=c.content,
                section_title=c.section_title,
                page_number=c.page_number,
                embedding=embeddings[idx] if idx < len(embeddings) else None,
                chunk_metadata=c.metadata,
            )
            db.add(db_chunk)

        audit_log = AuditLog(
            organization_id=organization_id,
            user_id=user_id,
            event_type="GUIDELINE_UPLOAD",
            entity_type="Guideline",
            entity_id=guideline.id,
            details={"title": title, "chunks_count": len(chunks_to_create), "filename": filename},
        )
        db.add(audit_log)
        db.commit()
        db.refresh(guideline)
        return guideline

    @staticmethod
    def import_approved_facts_csv(
        db: Session,
        organization_id: str,
        user_id: str,
        csv_content: str,
    ) -> List[ApprovedFact]:
        """Import approved facts from CSV string and persist them."""
        parsed_facts = parse_approved_facts_csv(csv_content)
        saved_facts: List[ApprovedFact] = []

        for pf in parsed_facts:
            fact = ApprovedFact(
                organization_id=organization_id,
                category=pf.get("category", "General"),
                claim_pattern=pf.get("claim_pattern", ""),
                approved_truth=pf["approved_truth"],
                mandatory_caveat=pf.get("mandatory_caveat"),
                source_citation=pf["source_citation"],
                effective_from=pf.get("effective_from"),
                expires_at=pf.get("expires_at"),
            )
            db.add(fact)
            saved_facts.append(fact)

        audit_log = AuditLog(
            organization_id=organization_id,
            user_id=user_id,
            event_type="FACTS_CSV_IMPORT",
            entity_type="ApprovedFact",
            entity_id=organization_id,
            details={"imported_count": len(saved_facts)},
        )
        db.add(audit_log)
        db.commit()
        return saved_facts

    @staticmethod
    def search_relevant_chunks(
        db: Session,
        organization_id: str,
        query_embedding: List[float],
        top_k: int = 5,
        min_similarity: float = 0.25,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve top-k relevant document chunks for an organization using cosine similarity.
        """
        stmt = (
            select(DocumentChunk)
            .options(selectinload(DocumentChunk.guideline))
            .where(DocumentChunk.organization_id == organization_id)
        )
        chunks = db.execute(stmt).scalars().all()

        scored_chunks = []
        for ch in chunks:
            if ch.embedding:
                sim = cosine_similarity(query_embedding, ch.embedding)
                if sim >= min_similarity:
                    scored_chunks.append({
                        "chunk_id": ch.id,
                        "guideline_title": ch.guideline.title if ch.guideline else "Guideline",
                        "content": ch.content,
                        "page_number": ch.page_number,
                        "section_title": ch.section_title,
                        "similarity": sim,
                    })

        scored_chunks.sort(key=lambda x: x["similarity"], reverse=True)
        return scored_chunks[:top_k]
