from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class CellDto(BaseModel):
    row: int
    column: int
    address: str
    value: Any = None
    data_type: str = "empty"
    number_format: str | None = None
    is_merged: bool = False
    merge_range: str | None = None
    is_bold: bool = False
    fill_color: str | None = None


class TableRegionDto(BaseModel):
    sheet: str
    start_row: int
    end_row: int
    start_column: int
    end_column: int
    header_start_row: int
    header_end_row: int
    data_start_row: int
    confidence: float = Field(ge=0, le=1)
    headers: list[str]
    rows: list[list[Any]] = Field(default_factory=list)


class SheetAnalysisDto(BaseModel):
    name: str
    state: str
    row_count: int
    column_count: int
    merged_ranges: list[str]
    regions: list[TableRegionDto]
    warnings: list[str] = Field(default_factory=list)


class WorkbookAnalysisDto(BaseModel):
    file_name: str
    sha256: str
    sheets: list[SheetAnalysisDto]
    warnings: list[str] = Field(default_factory=list)
    elapsed_ms: float


class AnalyzePathRequest(BaseModel):
    path: str
    include_hidden: bool = False
    preview_rows: int = Field(default=100, ge=1, le=1000)


class TargetFieldDto(BaseModel):
    field_id: str
    label: str
    aliases: list[str] = Field(default_factory=list)
    data_type: str = "string"
    required: bool = False
    description: str = ""


class MappingCandidateDto(BaseModel):
    source_column: int
    source_header: str
    target_field_id: str | None = None
    target_label: str | None = None
    confidence: float = Field(ge=0, le=1)
    decision: str
    provenance: list[str]
    alternatives: list[dict[str, Any]] = Field(default_factory=list)


class MapRequest(BaseModel):
    headers: list[str]
    target_fields: list[TargetFieldDto]
    sample_rows: list[list[Any]] = Field(default_factory=list)


class MapResponse(BaseModel):
    mappings: list[MappingCandidateDto]
    model_version: str
    requires_review: bool


class ValidationRuleDto(BaseModel):
    rule_id: str
    field_id: str
    rule_type: str
    severity: str = "error"
    message: str
    parameters: dict[str, Any] = Field(default_factory=dict)


class ValidateRequest(BaseModel):
    headers: list[str]
    rows: list[list[Any]]
    mappings: list[MappingCandidateDto]
    target_fields: list[TargetFieldDto]
    rules: list[ValidationRuleDto] = Field(default_factory=list)


class ValidationIssueDto(BaseModel):
    row: int
    column: int | None = None
    field_id: str | None = None
    severity: str
    code: str
    message: str
    value: Any = None


class ValidateResponse(BaseModel):
    valid: bool
    error_count: int
    warning_count: int
    issues: list[ValidationIssueDto]


class DetectRequest(BaseModel):
    path: str
    sheet: str | None = None
    include_hidden: bool = False


class ModelVersionDto(BaseModel):
    service_version: str
    strategy: str
    embedding_enabled: bool
    embedding_model: str | None
    llm_enabled: bool


class FeedbackRequest(BaseModel):
    job_id: str
    source_header: str
    suggested_field_id: str | None = None
    selected_field_id: str | None = None
    accepted: bool
    confidence: float = Field(ge=0, le=1)
    comment: str = ""


class FeedbackResponse(BaseModel):
    accepted: bool
    reference_id: str


class MappingDecision(str, Enum):
    auto = "auto"
    review = "review"
    unmapped = "unmapped"

