from __future__ import annotations

import asyncio
import os
import sys
import tempfile
import time
import zipfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from openpyxl.utils.exceptions import InvalidFileException
from pydantic import BaseModel, ConfigDict, Field


MODULE_ROOT = Path(__file__).resolve().parents[1]
TRAIN_ROOT = MODULE_ROOT / "Train"
if str(TRAIN_ROOT) not in sys.path:
    sys.path.insert(0, str(TRAIN_ROOT))

from training_core import EFormPredictor, MODEL_FILENAME  # noqa: E402


SERVICE_VERSION = "1.0.0"
DEFAULT_MODEL_PATH = TRAIN_ROOT / "Output_Local" / MODEL_FILENAME
ALLOWED_EXTENSIONS = {".xlsx", ".xlsm"}
MAX_UPLOAD_BYTES = int(os.getenv("EFORM_MAX_UPLOAD_BYTES", str(50 * 1024 * 1024)))
MAX_UNCOMPRESSED_BYTES = int(
    os.getenv("EFORM_MAX_UNCOMPRESSED_BYTES", str(500 * 1024 * 1024))
)
REVIEW_THRESHOLD = float(os.getenv("EFORM_REVIEW_THRESHOLD", "0.75"))


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ModelInfoResponse(ContractModel):
    name: str
    format: str
    device: str
    artifact: str


class HealthResponse(ContractModel):
    status: Literal["ready"]
    serviceVersion: str
    model: ModelInfoResponse


class MergeCellResponse(ContractModel):
    row: int = Field(ge=0)
    col: int = Field(ge=0)
    rowspan: int = Field(ge=1)
    colspan: int = Field(ge=1)


class ColumnResponse(ContractModel):
    columnIndex: int = Field(ge=0)
    excelColumn: str
    headerPath: list[str]
    label: str
    columnCode: str


class RowResponse(ContractModel):
    rowIndex: int = Field(ge=0)
    excelRow: int = Field(ge=1)
    rowType: Literal[
        "grand_total",
        "section",
        "item",
        "subitem",
        "detail",
        "data",
        "empty",
        "unclassified",
    ]
    level: int | None = Field(default=None, ge=0)
    code: str
    label: str
    parentRowIndex: int | None = Field(default=None, ge=0)
    hierarchyPath: list[str]
    mappingConfidence: float = Field(ge=0.0, le=1.0)
    requiresReview: bool
    reason: str


class TableResponse(ContractModel):
    sourceRange: str
    headerRows: int = Field(ge=1)
    rowCount: int = Field(ge=1)
    columnCount: int = Field(ge=1)
    valueRowCount: int = Field(ge=0)
    data: list[list[Any]]
    mergeCells: list[MergeCellResponse]
    columns: list[ColumnResponse]
    rows: list[RowResponse]
    rowHierarchySummary: dict[str, int]
    columnWidths: list[int]
    rowHeights: list[int]
    cellStyles: list[dict[str, Any]]
    formulaCells: list[dict[str, Any]]
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    postprocessing: str | None = None
    trimmedHeaderRows: int = Field(default=0, ge=0)
    trimmedFooterRows: int = Field(ge=0)


class SheetResponse(ContractModel):
    sheetIndex: int = Field(ge=0)
    sheetName: str
    sheetState: str
    tables: list[TableResponse]


class SummaryResponse(ContractModel):
    sheetCount: int = Field(ge=0)
    tableCount: int = Field(ge=0)
    rowCount: int = Field(ge=0)
    valueRowCount: int = Field(ge=0)
    cellCount: int = Field(ge=0)
    ambiguousRowCount: int = Field(ge=0)
    lowConfidenceTableCount: int = Field(ge=0)
    uploadBytes: int = Field(ge=0)


class ExtractResponse(ContractModel):
    schemaVersion: Literal["2.0"]
    model: str
    modelFormat: str
    device: str
    sourceFile: str
    summary: SummaryResponse
    sheets: list[SheetResponse]
    durationMs: float = Field(ge=0.0)
    requiresReview: bool
    warnings: list[str]


class ErrorResponse(ContractModel):
    detail: Any


def _model_path() -> Path:
    configured = os.getenv("EFORM_MODEL_PATH", "").strip()
    return Path(configured).expanduser().resolve() if configured else DEFAULT_MODEL_PATH.resolve()


def _validate_ooxml(path: Path) -> None:
    if not zipfile.is_zipfile(path):
        raise ValueError("File tải lên không phải workbook Excel Open XML hợp lệ.")
    with zipfile.ZipFile(path) as archive:
        names = {item.filename for item in archive.infolist()}
        if "[Content_Types].xml" not in names or "xl/workbook.xml" not in names:
            raise ValueError("File không có cấu trúc workbook Excel hợp lệ.")
        total_uncompressed = sum(item.file_size for item in archive.infolist())
        if total_uncompressed > MAX_UNCOMPRESSED_BYTES:
            raise ValueError("Workbook sau giải nén vượt giới hạn an toàn của dịch vụ.")


async def _save_upload(upload: UploadFile, destination: Path) -> int:
    size = 0
    with destination.open("xb") as output:
        while True:
            chunk = await upload.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > MAX_UPLOAD_BYTES:
                raise HTTPException(status_code=413, detail="File Excel vượt giới hạn 50 MB.")
            output.write(chunk)
    if size == 0:
        raise HTTPException(status_code=400, detail="File Excel rỗng.")
    return size


@asynccontextmanager
async def lifespan(app: FastAPI):
    predictor = await run_in_threadpool(
        EFormPredictor,
        _model_path(),
        os.getenv("EFORM_DEVICE", "auto"),
    )
    app.state.predictor = predictor
    app.state.inference_lock = asyncio.Lock()
    yield


app = FastAPI(
    title="eForm Excel Table Extractor",
    description="Phát hiện vùng bảng và trả nguyên dữ liệu Excel để giao diện xem trước.",
    version=SERVICE_VERSION,
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    predictor: EFormPredictor = app.state.predictor
    return HealthResponse.model_validate({
        "status": "ready",
        "serviceVersion": SERVICE_VERSION,
        "model": predictor.model_info,
    })


@app.get("/api/eform/model", response_model=ModelInfoResponse)
async def model_info() -> ModelInfoResponse:
    predictor: EFormPredictor = app.state.predictor
    return ModelInfoResponse.model_validate(predictor.model_info)


@app.post(
    "/api/eform/extract",
    response_model=ExtractResponse,
    responses={
        400: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        415: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
)
async def extract(
    file: UploadFile = File(...),
    originalFileName: str | None = Form(default=None),
) -> ExtractResponse:
    original_name = Path(originalFileName or file.filename or "").name
    extension = Path(original_name).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=415, detail="Chỉ chấp nhận file .xlsx hoặc .xlsm.")

    started = time.perf_counter()
    try:
        with tempfile.TemporaryDirectory(prefix="eform-ai-") as temporary_directory:
            workbook_path = Path(temporary_directory) / f"workbook{extension}"
            upload_size = await _save_upload(file, workbook_path)
            try:
                await run_in_threadpool(_validate_ooxml, workbook_path)
                predictor: EFormPredictor = app.state.predictor
                async with app.state.inference_lock:
                    result = await run_in_threadpool(
                        predictor.predict,
                        workbook_path,
                        original_name,
                    )
            except (InvalidFileException, zipfile.BadZipFile, OSError, ValueError) as exc:
                raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        await file.close()

    tables = [table for sheet in result["sheets"] for table in sheet["tables"]]
    low_confidence = sum(
        1
        for table in tables
        if table.get("confidence") is None or float(table["confidence"]) < REVIEW_THRESHOLD
    )
    ambiguous_rows = sum(
        int(table.get("rowHierarchySummary", {}).get("requiresReview", 0))
        for table in tables
    )
    result["summary"]["lowConfidenceTableCount"] = low_confidence
    result["summary"]["ambiguousRowCount"] = ambiguous_rows
    result["summary"]["uploadBytes"] = upload_size
    result["durationMs"] = round((time.perf_counter() - started) * 1000, 2)
    result["requiresReview"] = not tables or low_confidence > 0 or ambiguous_rows > 0
    warnings: list[str] = []
    if not tables:
        warnings.append("AI chưa phát hiện được vùng bảng trong workbook.")
    if low_confidence:
        warnings.append("Có vùng bảng độ tin cậy thấp, cần kiểm tra trước khi nhập.")
    if ambiguous_rows:
        warnings.append(
            f"Có {ambiguous_rows} hàng chưa đủ căn cứ xác định cấp, cần kiểm tra."
        )
    result["warnings"] = warnings
    return ExtractResponse.model_validate(result)
