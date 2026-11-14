from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field

from app.models.audit import AuditEngine, DecisionAction, FindingSeverity


class FindingBase(BaseModel):
    rule_id: str = Field(..., json_schema_extra={"example": "RULE-01"})
    engine: AuditEngine = Field(..., json_schema_extra={"example": AuditEngine.DETERMINISTIC})
    category: str = Field(..., json_schema_extra={"example": "TERMINOLOGY"})
    severity: FindingSeverity = Field(..., json_schema_extra={"example": FindingSeverity.HIGH})
    title: str = Field(..., json_schema_extra={"example": "Banned Slang Detected"})
    detected_content: str = Field(..., json_schema_extra={"example": "dirt cheap"})
    explanation: str = Field(..., json_schema_extra={"example": "The term 'dirt cheap' is in the banned glossary."})
    source_citation: Optional[str] = Field(None, json_schema_extra={"example": "Brand Guidelines v2, p. 8"})
    supporting_passage: Optional[str] = Field(None, json_schema_extra={"example": "Avoid colloquial slang such as 'dirt cheap'."})
    suggested_correction: Optional[str] = Field(None, json_schema_extra={"example": "cost-effective"})
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)
    requires_human_review: bool = Field(default=False)


class FindingDecisionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    decision: DecisionAction
    custom_edit: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: datetime


class FindingResponse(FindingBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    content_version_id: str
    created_at: datetime
    decision: Optional[FindingDecisionResponse] = None


class DecisionCreate(BaseModel):
    decision: DecisionAction
    custom_edit: Optional[str] = None
    rejection_reason: Optional[str] = None
