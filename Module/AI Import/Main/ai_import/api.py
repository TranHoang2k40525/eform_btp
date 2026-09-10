from __future__ import annotations

from fastapi import FastAPI, HTTPException

from . import __version__
from .config import settings
from .models import (
    HierarchyMapRequest,
    HierarchyMapResponse,
    HierarchyPromptResponse,
    MapRequest,
    MapResponse,
    ModelVersionDto,
    ParseRequest,
    ParseResponse,
)
from .security import UnsafeWorkbookError
from .service import ImportAiService


app = FastAPI(title="eForm Excel Parse AI", version=__version__)
service = ImportAiService(settings)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


@app.get("/model/version", response_model=ModelVersionDto)
def model_version() -> ModelVersionDto:
    return ModelVersionDto(service_version=__version__, strategy="parse:hierarchy+deterministic+fuzzy+optional-embedding+structured-llm",
        embedding_enabled=settings.embedding_enabled,
        embedding_model=settings.embedding_model if settings.embedding_enabled else None,
        llm_enabled=settings.llm_enabled)


@app.post("/map", response_model=MapResponse)
def map_fields(request: MapRequest) -> MapResponse:
    return service.map(request)


@app.post("/hierarchy/prompt", response_model=HierarchyPromptResponse)
def hierarchy_prompt(request: HierarchyMapRequest) -> HierarchyPromptResponse:
    return service.hierarchy_prompt(request)


@app.post("/hierarchy/map", response_model=HierarchyMapResponse)
def map_hierarchy(request: HierarchyMapRequest) -> HierarchyMapResponse:
    try:
        return service.map_hierarchy(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/parse", response_model=ParseResponse)
def parse(request: ParseRequest) -> ParseResponse:
    """Single internal contract: private workbook path + target schema -> flat JSON result."""
    try:
        return service.parse_flat(request)
    except (UnsafeWorkbookError, FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
