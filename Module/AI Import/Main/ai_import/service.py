from __future__ import annotations

import json
import uuid
from pathlib import Path

from .config import Settings
from .excel import WorkbookAnalyzer
from .mapping import HybridFieldMapper
from .models import FeedbackRequest, FeedbackResponse, MapRequest, MapResponse, ParseRequest, TargetFieldDto, ValidateRequest, ValidateResponse
from .validation import DeterministicValidator


class ImportAiService:
    def __init__(self, config: Settings):
        self.config = config
        self.analyzer = WorkbookAnalyzer(config)
        self.mapper = HybridFieldMapper(config)
        self.validator = DeterministicValidator()

    def analyze(self, path: str, include_hidden: bool = False, preview_rows: int = 100):
        return self.analyzer.analyze(path, include_hidden, preview_rows)

    def map(self, request: MapRequest) -> MapResponse:
        return self.mapper.map(request)

    def validate(self, request: ValidateRequest) -> ValidateResponse:
        return self.validator.validate(request)

    def parse_flat(self, request: ParseRequest) -> dict:
        fields = list(request.target_fields)
        if not fields and request.target_schema_json:
            raw = json.loads(request.target_schema_json)
            raw_fields = raw.get("fields", raw) if isinstance(raw, dict) else raw
            fields = [item if isinstance(item, TargetFieldDto) else TargetFieldDto(**item) for item in raw_fields]
        if not fields:
            raise ValueError("target_fields không được rỗng.")
        analysis = self.analyze(request.path, request.include_hidden, request.max_rows)
        regions = [region for sheet in analysis.sheets for region in sheet.regions]
        if not regions:
            raise ValueError("Không phát hiện được vùng bảng.")
        region = max(regions, key=lambda item: (item.confidence, len(item.rows)))
        mapped = self.map(MapRequest(headers=region.headers, target_fields=fields, sample_rows=region.rows[:10]))
        validation = self.validate(ValidateRequest(headers=region.headers, rows=region.rows,
            mappings=mapped.mappings, target_fields=fields))
        flat_rows: list[dict] = []
        for row in region.rows:
            item: dict = {}
            duplicate_counts: dict[str, int] = {}
            for candidate in mapped.mappings:
                if not candidate.target_field_id or candidate.source_column >= len(row):
                    continue
                key = candidate.target_field_id
                duplicate_counts[key] = duplicate_counts.get(key, 0) + 1
                if duplicate_counts[key] > 1:
                    key = f"{key}__{duplicate_counts[candidate.target_field_id]}"
                item[key] = row[candidate.source_column]
            flat_rows.append(item)
        return {
            "file_name": analysis.file_name, "sha256": analysis.sha256,
            "sheet": region.sheet, "region": {"start_row": region.start_row, "end_row": region.end_row,
                "header_start_row": region.header_start_row, "header_end_row": region.header_end_row},
            "columns": [candidate.model_dump() for candidate in mapped.mappings],
            "rows": flat_rows, "row_count": len(flat_rows),
            "valid": validation.valid, "issues": [issue.model_dump() for issue in validation.issues],
            "model_version": mapped.model_version, "requires_review": mapped.requires_review,
            "timings_ms": analysis.timings_ms,
        }

    def save_feedback(self, request: FeedbackRequest) -> FeedbackResponse:
        reference = str(uuid.uuid4())
        directory = self.config.upload_dir.parent / "feedback"
        directory.mkdir(parents=True, exist_ok=True)
        record = {"reference_id": reference, **request.model_dump()}
        # One JSON object per line; never include workbook cells or access tokens.
        with (directory / "mapping-feedback.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
        return FeedbackResponse(accepted=True, reference_id=reference)
