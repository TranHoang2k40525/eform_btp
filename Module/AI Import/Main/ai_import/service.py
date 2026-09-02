from __future__ import annotations

import json
import uuid
from pathlib import Path

from .config import Settings
from .excel import WorkbookAnalyzer
from .mapping import HybridFieldMapper
from .models import FeedbackRequest, FeedbackResponse, MapRequest, MapResponse, ValidateRequest, ValidateResponse
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

    def save_feedback(self, request: FeedbackRequest) -> FeedbackResponse:
        reference = str(uuid.uuid4())
        directory = self.config.upload_dir.parent / "feedback"
        directory.mkdir(parents=True, exist_ok=True)
        record = {"reference_id": reference, **request.model_dump()}
        # One JSON object per line; never include workbook cells or access tokens.
        with (directory / "mapping-feedback.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
        return FeedbackResponse(accepted=True, reference_id=reference)

