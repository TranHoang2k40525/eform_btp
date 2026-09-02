from __future__ import annotations

from fastapi import FastAPI, HTTPException

from . import __version__
from .config import settings
from .models import (
    AnalyzePathRequest, DetectRequest, FeedbackRequest, FeedbackResponse, MapRequest, MapResponse,
    ModelVersionDto, ValidateRequest, ValidateResponse, WorkbookAnalysisDto,
)
from .security import UnsafeWorkbookError
from .service import ImportAiService


app = FastAPI(title="eForm AI Import Service", version=__version__)
service = ImportAiService(settings)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


@app.get("/model/version", response_model=ModelVersionDto)
def model_version() -> ModelVersionDto:
    return ModelVersionDto(service_version=__version__, strategy="deterministic+fuzzy+optional-embedding",
        embedding_enabled=settings.embedding_enabled,
        embedding_model=settings.embedding_model if settings.embedding_enabled else None,
        llm_enabled=settings.llm_enabled)


@app.post("/analyze", response_model=WorkbookAnalysisDto)
def analyze(request: AnalyzePathRequest) -> WorkbookAnalysisDto:
    try:
        return service.analyze(request.path, request.include_hidden, request.preview_rows)
    except (UnsafeWorkbookError, FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/detect-table")
def detect_table(request: DetectRequest) -> dict:
    try:
        analysis = service.analyze(request.path, request.include_hidden)
        regions = [region.model_dump() for sheet in analysis.sheets
                   if request.sheet is None or sheet.name == request.sheet for region in sheet.regions]
        return {"regions": regions}
    except (UnsafeWorkbookError, FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/detect-form")
def detect_form(request: DetectRequest) -> dict:
    analysis = analyze(AnalyzePathRequest(path=request.path, include_hidden=request.include_hidden))
    ranked = sorted(
        ({"sheet": sheet.name, "confidence": max((region.confidence for region in sheet.regions), default=0.0),
          "region_count": len(sheet.regions)} for sheet in analysis.sheets),
        key=lambda item: item["confidence"], reverse=True,
    )
    return {"candidates": ranked}


@app.post("/map", response_model=MapResponse)
def map_fields(request: MapRequest) -> MapResponse:
    return service.map(request)


@app.post("/validate", response_model=ValidateResponse)
def validate(request: ValidateRequest) -> ValidateResponse:
    return service.validate(request)


@app.post("/feedback", response_model=FeedbackResponse)
def feedback(request: FeedbackRequest) -> FeedbackResponse:
    return service.save_feedback(request)

