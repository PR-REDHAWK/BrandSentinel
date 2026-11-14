from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# Guidelines & Chunks
class DocumentChunkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    chunk_index: int
    content: str
    section_title: Optional[str] = None
    page_number: Optional[int] = None


class GuidelineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    title: str
    file_type: str
    file_path: str
    version: int
    status: str
    created_at: datetime
    chunk_count: Optional[int] = 0


# Approved Facts
class FactCreate(BaseModel):
    category: str = Field(..., json_schema_extra={"example": "Performance"})
    claim_pattern: str = Field(..., json_schema_extra={"example": "Cost savings and ROI"})
    approved_truth: str = Field(..., json_schema_extra={"example": "Customers achieve up to 30% reduction in infrastructure costs within six months."})
    mandatory_caveat: Optional[str] = Field(None, json_schema_extra={"example": "Based on surveyed deployments over 500 instances."})
    source_citation: str = Field(..., json_schema_extra={"example": "Q4 2025 Auditor Report, p. 12"})
    effective_from: Optional[str] = None
    expires_at: Optional[str] = None


class FactResponse(FactCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    created_at: datetime


# Glossary & Banned Terms
class GlossaryCreate(BaseModel):
    term: str = Field(..., min_length=1, max_length=200)
    is_banned: bool = Field(default=False)
    preferred_term: Optional[str] = None
    definition_or_rule: str = Field(..., min_length=2)
    case_sensitive: bool = Field(default=False)


class GlossaryResponse(GlossaryCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    created_at: datetime


# Brand Assets
class AssetCreate(BaseModel):
    asset_type: str = Field(..., json_schema_extra={"example": "PALETTE"})
    name: str = Field(..., json_schema_extra={"example": "Primary Brand Colors"})
    hex_colors: Optional[List[str]] = Field(default=None, json_schema_extra={"example": ["#0B2046", "#FF6B35", "#FFFFFF"]})
    aspect_ratio: Optional[float] = None
    rules: Dict[str, Any] = Field(default_factory=dict)


class AssetResponse(AssetCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    file_path: Optional[str] = None
    created_at: datetime
