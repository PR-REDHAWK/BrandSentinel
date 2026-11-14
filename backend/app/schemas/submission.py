from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.audit import SubmissionStatus
from app.schemas.finding import FindingResponse


class SubmissionCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    target_channel: Optional[str] = Field("Web", json_schema_extra={"example": "Web"})
    raw_content: Optional[str] = Field(None, json_schema_extra={"example": "Our software cuts your costs by 50% overnight."})


class ContentVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    submission_id: str
    version_number: int
    raw_content: Optional[str] = None
    document_path: Optional[str] = None
    has_images: bool
    image_metadata: List[Dict[str, Any]] = Field(default_factory=list)
    audit_score: Optional[float] = None
    created_at: datetime
    findings: List[FindingResponse] = Field(default_factory=list)


class SubmissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    creator_id: str
    title: str
    target_channel: Optional[str] = None
    current_status: SubmissionStatus
    created_at: datetime
    updated_at: datetime
    versions: List[ContentVersionResponse] = Field(default_factory=list)
