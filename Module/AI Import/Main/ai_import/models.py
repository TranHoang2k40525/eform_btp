from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictDto(BaseModel):
    """Contract dùng giữa .NET, AI service và LLM: không nhận field lạ."""

    model_config = ConfigDict(extra="forbid")


class CellDto(StrictDto):
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


class IndicatorDto(StrictDto):
    """Một dòng chỉ tiêu đã giữ nguyên mã cấp và đường dẫn cha/con."""

    source_ref: str
    source_row: int | None = None
    code: str = ""
    label: str
    kind: str = "detail"
    level: int = Field(default=0, ge=0, le=12)
    parent_ref: str | None = None
    path: list[str] = Field(default_factory=list)


class TargetIndicatorDto(StrictDto):
    target_ref: str
    target_row: int | None = None
    code: str = ""
    label: str
    kind: str = "detail"
    level: int = Field(default=0, ge=0, le=12)
    parent_ref: str | None = None
    path: list[str] = Field(default_factory=list)


class TableRegionDto(StrictDto):
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
    source_columns: list[int] = Field(default_factory=list)
    header_paths: list[list[str]] = Field(default_factory=list)
    column_codes: list[str] = Field(default_factory=list)
    section_path: list[str] = Field(default_factory=list)
    indicators: list[IndicatorDto] = Field(default_factory=list)
    rows: list[list[Any]] = Field(default_factory=list)


class SheetAnalysisDto(StrictDto):
    name: str
    state: str
    row_count: int
    column_count: int
    merged_ranges: list[str]
    regions: list[TableRegionDto]
    warnings: list[str] = Field(default_factory=list)


class WorkbookAnalysisDto(StrictDto):
    file_name: str
    sha256: str
    sheets: list[SheetAnalysisDto]
    warnings: list[str] = Field(default_factory=list)
    timings_ms: dict[str, float] = Field(default_factory=dict)
    elapsed_ms: float


class AnalyzePathRequest(StrictDto):
    path: str
    include_hidden: bool = False
    preview_rows: int = Field(default=100, ge=1, le=50000)


class TargetFieldDto(StrictDto):
    field_id: str
    label: str
    aliases: list[str] = Field(default_factory=list)
    data_type: str = "string"
    required: bool = False
    description: str = ""
    field_name: str = ""
    doc_type_code: str = ""
    form_id: str = ""
    form_index: int = Field(default=0, ge=0)
    column_code: str = ""
    header_path: list[str] = Field(default_factory=list)
    read_only: bool = False
    hidden: bool = False


class ParseRequest(StrictDto):
    path: str
    target_fields: list[TargetFieldDto] = Field(default_factory=list)
    target_schema_json: str | None = None
    target_indicators: list[TargetIndicatorDto] = Field(default_factory=list)
    doc_type_code: str = ""
    report_title: str = ""
    form_index: int = Field(default=0, ge=0)
    include_hidden: bool = False
    max_rows: int = Field(default=50000, ge=1, le=50000)


class MappingCandidateDto(StrictDto):
    source_column: int
    source_header: str
    target_field_id: str | None = None
    target_label: str | None = None
    confidence: float = Field(ge=0, le=1)
    decision: str
    provenance: list[str]
    alternatives: list[dict[str, Any]] = Field(default_factory=list)
    source_header_path: list[str] = Field(default_factory=list)
    source_column_code: str = ""
    target_column_code: str = ""


class MapRequest(StrictDto):
    headers: list[str]
    target_fields: list[TargetFieldDto]
    sample_rows: list[list[Any]] = Field(default_factory=list)
    header_paths: list[list[str]] = Field(default_factory=list)
    column_codes: list[str] = Field(default_factory=list)
    doc_type_code: str = ""
    report_title: str = ""
    form_index: int = Field(default=0, ge=0)


class MapResponse(StrictDto):
    mappings: list[MappingCandidateDto]
    model_version: str
    requires_review: bool


class ValidationRuleDto(StrictDto):
    rule_id: str
    field_id: str
    rule_type: str
    severity: str = "error"
    message: str
    parameters: dict[str, Any] = Field(default_factory=dict)


class ValidateRequest(StrictDto):
    headers: list[str]
    rows: list[list[Any]]
    mappings: list[MappingCandidateDto]
    target_fields: list[TargetFieldDto]
    rules: list[ValidationRuleDto] = Field(default_factory=list)


class ValidationIssueDto(StrictDto):
    row: int
    column: int | None = None
    field_id: str | None = None
    severity: str
    code: str
    message: str
    value: Any = None


class ValidateResponse(StrictDto):
    valid: bool
    error_count: int
    warning_count: int
    issues: list[ValidationIssueDto]


class DetectRequest(StrictDto):
    path: str
    sheet: str | None = None
    include_hidden: bool = False


class ModelVersionDto(StrictDto):
    service_version: str
    strategy: str
    embedding_enabled: bool
    embedding_model: str | None
    llm_enabled: bool


class FeedbackRequest(StrictDto):
    job_id: str
    source_header: str
    suggested_field_id: str | None = None
    selected_field_id: str | None = None
    accepted: bool
    confidence: float = Field(ge=0, le=1)
    comment: str = ""


class FeedbackResponse(StrictDto):
    accepted: bool
    reference_id: str


class MappingDecision(str, Enum):
    auto = "auto"
    review = "review"
    unmapped = "unmapped"


class HierarchyMapRequest(StrictDto):
    doc_type_code: str
    report_title: str = ""
    form_index: int = Field(default=0, ge=0)
    source_indicators: list[IndicatorDto]
    target_indicators: list[TargetIndicatorDto]
    use_llm: bool = True

    @field_validator("source_indicators", "target_indicators")
    @classmethod
    def must_not_be_empty(cls, value: list[Any]) -> list[Any]:
        if not value:
            raise ValueError("Danh sách chỉ tiêu không được rỗng.")
        return value


class HierarchyAlternativeDto(StrictDto):
    target_ref: str
    label: str
    score: float = Field(ge=0, le=1)


class HierarchyMappingDto(StrictDto):
    source_ref: str
    target_ref: str | None = None
    confidence: float = Field(ge=0, le=1)
    decision: MappingDecision
    reason_codes: list[str] = Field(default_factory=list)
    alternatives: list[HierarchyAlternativeDto] = Field(default_factory=list)


class HierarchyIssueDto(StrictDto):
    code: str
    severity: str
    source_ref: str | None = None
    target_ref: str | None = None
    message: str


class HierarchyMapResponse(StrictDto):
    schema_version: Literal["1.0"] = "1.0"
    doc_type_code: str
    mappings: list[HierarchyMappingDto]
    issues: list[HierarchyIssueDto] = Field(default_factory=list)
    valid: bool
    requires_review: bool
    strategy: str


class LlmHierarchyMappingDto(StrictDto):
    source_ref: str
    target_ref: str | None
    confidence: float = Field(ge=0, le=1)


class LlmHierarchyResponse(StrictDto):
    schema_version: Literal["1.0"]
    mappings: list[LlmHierarchyMappingDto]


class HierarchyPromptResponse(StrictDto):
    schema_version: Literal["1.0"] = "1.0"
    messages: list[dict[str, str]]
    output_schema: dict[str, Any]


class ParseResponse(StrictDto):
    schema_version: Literal["1.0"] = "1.0"
    file_name: str
    sha256: str
    doc_type_code: str = ""
    form_index: int = 0
    sheet: str
    region: dict[str, int]
    columns: list[MappingCandidateDto]
    row_mappings: list[HierarchyMappingDto] = Field(default_factory=list)
    rows: list[dict[str, Any]]
    row_count: int
    valid: bool
    issues: list[ValidationIssueDto | HierarchyIssueDto] = Field(default_factory=list)
    model_version: str
    requires_review: bool
    timings_ms: dict[str, float] = Field(default_factory=dict)
