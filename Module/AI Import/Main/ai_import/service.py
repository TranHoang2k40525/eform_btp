from __future__ import annotations

import json
import math
import uuid
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any

from .config import Settings
from .excel import WorkbookAnalyzer
from .hierarchy import DeterministicHierarchyMapper
from .llm import LlmOutputError, StructuredLlmClient
from .mapping import HybridFieldMapper
from .models import (
    FeedbackRequest,
    FeedbackResponse,
    HierarchyIssueDto,
    HierarchyMapRequest,
    HierarchyMapResponse,
    HierarchyMappingDto,
    HierarchyPromptResponse,
    MapRequest,
    MapResponse,
    MappingDecision,
    ParseRequest,
    ParseResponse,
    ValidateRequest,
    ValidateResponse,
)
from .prompting import build_hierarchy_messages, hierarchy_output_schema
from .schema import ParsedTargetSchema, parse_target_schema
from .validation import DeterministicValidator


def _json_safe(value: Any) -> Any:
    """Đảm bảo response không chứa NaN, datetime hoặc kiểu Excel làm hỏng JSON."""

    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return str(value)


class ImportAiService:
    def __init__(self, config: Settings):
        self.config = config
        self.analyzer = WorkbookAnalyzer(config)
        self.mapper = HybridFieldMapper(config)
        self.hierarchy_mapper = DeterministicHierarchyMapper(config)
        self.llm = StructuredLlmClient(config)
        self.validator = DeterministicValidator()

    def analyze(self, path: str, include_hidden: bool = False, preview_rows: int = 100):
        return self.analyzer.analyze(path, include_hidden, preview_rows)

    def map(self, request: MapRequest) -> MapResponse:
        return self.mapper.map(request)

    def validate(self, request: ValidateRequest) -> ValidateResponse:
        return self.validator.validate(request)

    def hierarchy_prompt(self, request: HierarchyMapRequest) -> HierarchyPromptResponse:
        return HierarchyPromptResponse(
            messages=build_hierarchy_messages(request),
            output_schema=hierarchy_output_schema(),
        )

    def map_hierarchy(self, request: HierarchyMapRequest) -> HierarchyMapResponse:
        baseline = self.hierarchy_mapper.map(request)
        if not self.config.llm_enabled or not request.use_llm:
            return baseline
        try:
            llm_result = self.llm.map_hierarchy(request)
        except LlmOutputError as exc:
            issue = HierarchyIssueDto(
                code="LLM_OUTPUT_REJECTED",
                severity="warning",
                message=str(exc),
            )
            return baseline.model_copy(update={
                "issues": [*baseline.issues, issue],
                "requires_review": True,
                "strategy": "hierarchy-deterministic-fallback-v1",
            })

        llm_by_source = {item.source_ref: item for item in llm_result.mappings}
        baseline_by_source = {item.source_ref: item for item in baseline.mappings}
        mappings: list[HierarchyMappingDto] = []
        issues = list(baseline.issues)
        for source in request.source_indicators:
            base = baseline_by_source[source.source_ref]
            if "IGNORED_MARKER_ROW" in base.reason_codes:
                mappings.append(base)
                continue
            llm_item = llm_by_source[source.source_ref]
            if llm_item.target_ref is None:
                if base.decision == MappingDecision.auto and base.target_ref:
                    mappings.append(base.model_copy(update={
                        "decision": MappingDecision.review,
                        "reason_codes": [*base.reason_codes, "LLM_UNMAPPED_DISAGREEMENT"],
                    }))
                    issues.append(HierarchyIssueDto(
                        code="LLM_BASELINE_DISAGREEMENT",
                        severity="warning",
                        source_ref=source.source_ref,
                        target_ref=base.target_ref,
                        message="LLM bỏ trống ánh xạ đã được baseline chọn; giữ candidate và bắt buộc duyệt.",
                    ))
                else:
                    mappings.append(base.model_copy(update={
                        "target_ref": None,
                        "confidence": llm_item.confidence,
                        "decision": MappingDecision.unmapped,
                        "reason_codes": ["LLM_UNMAPPED", "STRUCTURE_VALIDATED"],
                    }))
                continue
            confirmed = base.target_ref == llm_item.target_ref
            confidence = min(llm_item.confidence, base.confidence + (0.05 if confirmed else 0.0))
            decision = (
                MappingDecision.auto
                if confirmed
                and base.decision == MappingDecision.auto
                and confidence >= self.config.auto_accept_threshold
                else MappingDecision.review
            )
            reason_codes = ["LLM_STRUCTURED_OUTPUT", "STRUCTURE_VALIDATED"]
            if confirmed:
                reason_codes.extend(base.reason_codes)
                reason_codes.append("DETERMINISTIC_CONFIRMED")
            else:
                reason_codes.append("LLM_DIFFERS_FROM_BASELINE")
            if confirmed and base.decision != MappingDecision.auto:
                reason_codes.append("BASELINE_REVIEW_PRESERVED")
            if not confirmed:
                issues.append(HierarchyIssueDto(
                    code="LLM_BASELINE_DISAGREEMENT",
                    severity="warning",
                    source_ref=source.source_ref,
                    target_ref=llm_item.target_ref,
                    message="LLM và baseline chọn hai dòng đích khác nhau; bắt buộc duyệt.",
                ))
            mappings.append(base.model_copy(update={
                "target_ref": llm_item.target_ref,
                "confidence": round(confidence, 4),
                "decision": decision,
                "reason_codes": reason_codes,
            }))
        return HierarchyMapResponse(
            doc_type_code=request.doc_type_code,
            mappings=mappings,
            issues=issues,
            valid=not any(item.severity == "error" for item in issues),
            requires_review=any(item.decision != MappingDecision.auto for item in mappings),
            strategy=f"llm-structured-v1:{self.config.llm_model}",
        )

    def parse_flat(self, request: ParseRequest) -> ParseResponse:
        fields = list(request.target_fields)
        parsed_schema = ParsedTargetSchema()
        if not fields and request.target_schema_json:
            parsed_schema = parse_target_schema(request.target_schema_json, request.form_index)
            fields = parsed_schema.fields
        fields = [item for item in fields if item.form_index == request.form_index and not item.hidden]
        if not fields:
            raise ValueError("target_fields không được rỗng.")
        analysis = self.analyze(request.path, request.include_hidden, request.max_rows)
        regions = [region for sheet in analysis.sheets for region in sheet.regions]
        if not regions:
            raise ValueError("Không phát hiện được vùng bảng.")
        ordered_regions = sorted(regions, key=lambda item: (item.sheet, item.header_end_row))
        region = ordered_regions[request.form_index] if request.form_index < len(ordered_regions) else max(
            regions, key=lambda item: (item.confidence, len(item.rows))
        )
        doc_type_code = request.doc_type_code or parsed_schema.doc_type_code
        report_title = request.report_title or parsed_schema.report_title
        mapped = self.map(MapRequest(
            headers=region.headers,
            target_fields=fields,
            sample_rows=region.rows[:10],
            header_paths=region.header_paths,
            column_codes=region.column_codes,
            doc_type_code=doc_type_code,
            report_title=report_title,
            form_index=request.form_index,
        ))
        validation = self.validate(ValidateRequest(headers=region.headers, rows=region.rows,
            mappings=mapped.mappings, target_fields=fields))
        target_indicators = request.target_indicators or parsed_schema.indicators
        hierarchy: HierarchyMapResponse | None = None
        if region.indicators and target_indicators:
            hierarchy = self.map_hierarchy(HierarchyMapRequest(
                doc_type_code=doc_type_code,
                report_title=report_title,
                form_index=request.form_index,
                source_indicators=region.indicators,
                target_indicators=target_indicators,
            ))
        flat_rows: list[dict] = []
        for row in region.rows:
            item: dict = {}
            for candidate in mapped.mappings:
                if not candidate.target_field_id or candidate.source_column >= len(row):
                    continue
                item[candidate.target_field_id] = _json_safe(row[candidate.source_column])
            flat_rows.append(item)
        hierarchy_issues = hierarchy.issues if hierarchy else []
        return ParseResponse(
            file_name=analysis.file_name,
            sha256=analysis.sha256,
            doc_type_code=doc_type_code,
            form_index=request.form_index,
            sheet=region.sheet,
            region={
                "start_row": region.start_row,
                "end_row": region.end_row,
                "header_start_row": region.header_start_row,
                "header_end_row": region.header_end_row,
                "data_start_row": region.data_start_row,
            },
            columns=mapped.mappings,
            row_mappings=hierarchy.mappings if hierarchy else [],
            rows=flat_rows,
            row_count=len(flat_rows),
            valid=validation.valid and (hierarchy.valid if hierarchy else True),
            issues=[*validation.issues, *hierarchy_issues],
            model_version=mapped.model_version + (f"+{hierarchy.strategy}" if hierarchy else ""),
            requires_review=mapped.requires_review or (hierarchy.requires_review if hierarchy else False),
            timings_ms=analysis.timings_ms,
        )

    def save_feedback(self, request: FeedbackRequest) -> FeedbackResponse:
        reference = str(uuid.uuid4())
        directory = self.config.upload_dir.parent / "feedback"
        directory.mkdir(parents=True, exist_ok=True)
        record = {"reference_id": reference, **request.model_dump()}
        # One JSON object per line; never include workbook cells or access tokens.
        with (directory / "mapping-feedback.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
        return FeedbackResponse(accepted=True, reference_id=reference)
