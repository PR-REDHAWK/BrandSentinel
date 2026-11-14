from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.dependencies import get_current_active_user, require_role
from app.models.auth import User, UserRole
from app.models.knowledge import (
    ApprovedFact,
    BrandAsset,
    DocumentChunk,
    GlossaryTerm,
    Guideline,
)
from app.schemas.knowledge import (
    AssetCreate,
    AssetResponse,
    FactCreate,
    FactResponse,
    GlossaryCreate,
    GlossaryResponse,
    GuidelineResponse,
)
from app.services.knowledge_service import KnowledgeService

router = APIRouter(prefix="/knowledge", tags=["Brand Knowledge Management"])


# ==================== GUIDELINES ====================

@router.post(
    "/guidelines/upload",
    response_model=GuidelineResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role([UserRole.ADMIN, UserRole.BRAND_MANAGER]))],
)
def upload_guideline(
    title: str = Form(..., description="Human-readable title of the guideline"),
    file: UploadFile = File(..., description="PDF or DOCX guideline document"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Upload and genuinely ingest a PDF or DOCX brand guideline document.
    """
    allowed_extensions = {".pdf", ".docx", ".doc", ".txt"}
    import os
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{ext}'. Allowed: {list(allowed_extensions)}",
        )

    file_bytes = file.file.read()
    if len(file_bytes) > 25 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds maximum allowed threshold of 25MB",
        )

    guideline = KnowledgeService.process_and_store_guideline(
        db=db,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        file_bytes=file_bytes,
        filename=file.filename,
        title=title,
    )

    chunk_count_stmt = select(func.count(DocumentChunk.id)).where(DocumentChunk.guideline_id == guideline.id)
    chunk_count = db.execute(chunk_count_stmt).scalar() or 0

    resp = GuidelineResponse.model_validate(guideline)
    resp.chunk_count = chunk_count
    return resp


@router.get("/guidelines", response_model=List[GuidelineResponse])
def list_guidelines(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List all guidelines uploaded for the user's organization."""
    stmt = (
        select(Guideline)
        .where(Guideline.organization_id == current_user.organization_id)
        .order_by(Guideline.created_at.desc())
    )
    guidelines = db.execute(stmt).scalars().all()

    response_list = []
    for g in guidelines:
        c_count_stmt = select(func.count(DocumentChunk.id)).where(DocumentChunk.guideline_id == g.id)
        c_count = db.execute(c_count_stmt).scalar() or 0
        item = GuidelineResponse.model_validate(g)
        item.chunk_count = c_count
        response_list.append(item)

    return response_list


# ==================== APPROVED FACTS ====================

@router.post(
    "/facts",
    response_model=FactResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role([UserRole.ADMIN, UserRole.BRAND_MANAGER]))],
)
def create_approved_fact(
    payload: FactCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Add an individual approved fact with explicit source citation."""
    fact = ApprovedFact(
        organization_id=current_user.organization_id,
        category=payload.category,
        claim_pattern=payload.claim_pattern,
        approved_truth=payload.approved_truth,
        mandatory_caveat=payload.mandatory_caveat,
        source_citation=payload.source_citation,
        effective_from=payload.effective_from,
        expires_at=payload.expires_at,
    )
    db.add(fact)
    db.commit()
    db.refresh(fact)
    return FactResponse.model_validate(fact)


@router.post(
    "/facts/import-csv",
    response_model=List[FactResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role([UserRole.ADMIN, UserRole.BRAND_MANAGER]))],
)
def import_facts_csv(
    file: UploadFile = File(..., description="CSV file containing approved facts"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Bulk import approved facts from a CSV file."""
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a .csv format",
        )
    content = file.file.read().decode("utf-8", errors="ignore")
    facts = KnowledgeService.import_approved_facts_csv(
        db=db,
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        csv_content=content,
    )
    return [FactResponse.model_validate(f) for f in facts]


@router.get("/facts", response_model=List[FactResponse])
def list_approved_facts(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List approved facts for the current organization."""
    stmt = select(ApprovedFact).where(ApprovedFact.organization_id == current_user.organization_id)
    if category:
        stmt = stmt.where(ApprovedFact.category == category)
    stmt = stmt.order_by(ApprovedFact.created_at.desc())
    facts = db.execute(stmt).scalars().all()
    return [FactResponse.model_validate(f) for f in facts]


# ==================== GLOSSARY & BANNED TERMS ====================

@router.post(
    "/glossary",
    response_model=GlossaryResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role([UserRole.ADMIN, UserRole.BRAND_MANAGER]))],
)
def create_glossary_term(
    payload: GlossaryCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Add a glossary term or banned word rule."""
    term = GlossaryTerm(
        organization_id=current_user.organization_id,
        term=payload.term.strip(),
        is_banned=payload.is_banned,
        preferred_term=payload.preferred_term.strip() if payload.preferred_term else None,
        definition_or_rule=payload.definition_or_rule.strip(),
        case_sensitive=payload.case_sensitive,
    )
    db.add(term)
    db.commit()
    db.refresh(term)
    return GlossaryResponse.model_validate(term)


@router.get("/glossary", response_model=List[GlossaryResponse])
def list_glossary_terms(
    banned_only: Optional[bool] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List glossary and banned terms for the organization."""
    stmt = select(GlossaryTerm).where(GlossaryTerm.organization_id == current_user.organization_id)
    if banned_only is not None:
        stmt = stmt.where(GlossaryTerm.is_banned == banned_only)
    stmt = stmt.order_by(GlossaryTerm.term.asc())
    terms = db.execute(stmt).scalars().all()
    return [GlossaryResponse.model_validate(t) for t in terms]


# ==================== BRAND ASSETS ====================

@router.post(
    "/assets",
    response_model=AssetResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role([UserRole.ADMIN, UserRole.BRAND_MANAGER]))],
)
def create_brand_asset(
    payload: AssetCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Register an approved brand asset such as official hex palettes or logo parameters."""
    asset = BrandAsset(
        organization_id=current_user.organization_id,
        asset_type=payload.asset_type,
        name=payload.name,
        hex_colors=payload.hex_colors,
        aspect_ratio=payload.aspect_ratio,
        rules=payload.rules,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return AssetResponse.model_validate(asset)


@router.get("/assets", response_model=List[AssetResponse])
def list_brand_assets(
    asset_type: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List brand assets for the organization."""
    stmt = select(BrandAsset).where(BrandAsset.organization_id == current_user.organization_id)
    if asset_type:
        stmt = stmt.where(BrandAsset.asset_type == asset_type)
    stmt = stmt.order_by(BrandAsset.created_at.desc())
    assets = db.execute(stmt).scalars().all()
    return [AssetResponse.model_validate(a) for a in assets]
