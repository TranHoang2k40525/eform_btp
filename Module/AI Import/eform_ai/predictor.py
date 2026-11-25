from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import torch
from openpyxl import load_workbook

from eform_ai.encoder import actual_bounds, encode_sheet
from eform_ai.extractor import extract_table_payload, merge_repeated_header_tables
from eform_ai.postprocess import decode_predictions
from eform_ai.schema import FORMAT_VERSION


def resolve_device(device_name: str | None = None) -> torch.device:
    requested = (device_name or "auto").strip().lower()
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if requested.startswith("cuda") and not torch.cuda.is_available():
        raise ValueError("CUDA was requested but is not available.")
    return torch.device(requested)


def load_torchscript_artifact(
    model_path: Path, device: torch.device
) -> tuple[torch.jit.ScriptModule, dict[str, Any]]:
    """Load a self-contained TorchScript .eformmodel bundle without importing any training code."""
    extra_files: dict[str, bytes] = {"metadata.json": b""}
    model = torch.jit.load(
        str(model_path), map_location=device, _extra_files=extra_files
    )
    model.eval()
    raw_meta = extra_files.get("metadata.json", b"")
    if not raw_meta:
        raise ValueError(
            f"Artifact {model_path.name} thiếu metadata.json nhúng (cần định dạng {FORMAT_VERSION})."
        )
    metadata = json.loads(raw_meta.decode("utf-8"))
    if metadata.get("format_version") != FORMAT_VERSION:
        raise ValueError(
            f"Định dạng artifact không khớp: {metadata.get('format_version')} (cần {FORMAT_VERSION})."
        )
    return model, metadata


def _workbook_has_formulas(workbook: Any) -> bool:
    for worksheet in workbook.worksheets:
        for cell in getattr(worksheet, "_cells", {}).values():
            if getattr(cell, "data_type", "") == "f":
                return True
    return False


class EFormPredictor:
    """Thin, self-contained PyTorch TorchScript runtime for FastAPI.

    Loads a single .eformmodel artifact directly via torch.jit.load() with zero dependency
    on Train/ code, training libraries, or hardcoded boundary/regex heuristics.
    """

    def __init__(self, model_path: Path | str, device_name: str | None = None) -> None:
        self.model_path = Path(model_path).resolve()
        if not self.model_path.is_file():
            raise FileNotFoundError(f"Model artifact not found: {self.model_path}")
        self.device = resolve_device(device_name)
        self.model, self.metadata = load_torchscript_artifact(self.model_path, self.device)
        self.inference_config: dict[str, Any] = self.metadata.get("inference_config", {})

    @property
    def model_info(self) -> dict[str, Any]:
        return {
            "name": str(self.metadata["model_name"]),
            "format": str(self.metadata["format_version"]),
            "device": str(self.device),
            "artifact": self.model_path.name,
        }

    @torch.inference_mode()
    def predict_worksheet(self, worksheet: Any) -> list[dict[str, Any]]:
        rows, columns = actual_bounds(worksheet)
        if rows == 0 or columns == 0:
            return []
        features = encode_sheet(worksheet, rows, columns).unsqueeze(0).to(self.device)
        outputs: dict[str, torch.Tensor] = self.model(features)
        return decode_predictions(
            cell_logits=outputs["cell_logits"][0],
            table_start_logits=outputs["table_start_logits"][0],
            col_role_logits=outputs["col_role_logits"][0],
            col_mismatch_logits=outputs["col_mismatch_logits"][0],
            row_type_logits=outputs["row_type_logits"][0],
            minimum_component_cells=int(self.inference_config.get("minimum_component_cells", 4)),
            header_fraction_threshold=float(self.inference_config.get("header_fraction_threshold", 0.30)),
            table_start_threshold=float(self.inference_config.get("table_start_threshold", 0.45)),
        )

    def predict(self, excel_path: Path | str, source_name: str | None = None) -> dict[str, Any]:
        excel_path = Path(excel_path)
        workbook = load_workbook(excel_path, read_only=False, data_only=False, keep_links=False)
        value_workbook = None
        sheets: list[dict[str, Any]] = []
        mismatch_threshold = float(self.inference_config.get("col_mismatch_threshold", 0.55))
        try:
            # Lazily load data_only=True only when formulas actually exist (halves Excel I/O latency)
            if _workbook_has_formulas(workbook):
                value_workbook = load_workbook(
                    excel_path, read_only=False, data_only=True, keep_links=False
                )
            for sheet_index, worksheet in enumerate(workbook.worksheets):
                value_worksheet = (
                    value_workbook.worksheets[sheet_index] if value_workbook is not None else None
                )
                regions = self.predict_worksheet(worksheet)
                extracted = [
                    extract_table_payload(
                        worksheet,
                        region,
                        value_worksheet,
                        mismatch_threshold=mismatch_threshold,
                    )
                    for region in regions
                ]
                extracted = merge_repeated_header_tables(extracted)
                sheets.append({
                    "sheetIndex": sheet_index,
                    "sheetName": worksheet.title,
                    "sheetState": worksheet.sheet_state,
                    "tables": extracted,
                })
        finally:
            if value_workbook is not None:
                value_workbook.close()
            workbook.close()

        tables = [table for sheet in sheets for table in sheet["tables"]]
        return {
            "schemaVersion": "2.0",
            "model": str(self.metadata["model_name"]),
            "modelFormat": str(self.metadata["format_version"]),
            "device": str(self.device),
            "sourceFile": source_name or excel_path.name,
            "summary": {
                "sheetCount": len(sheets),
                "tableCount": len(tables),
                "rowCount": sum(table["rowCount"] for table in tables),
                "valueRowCount": sum(table["valueRowCount"] for table in tables),
                "cellCount": sum(table["rowCount"] * table["columnCount"] for table in tables),
                "ambiguousRowCount": sum(
                    int(table["rowHierarchySummary"].get("requiresReview", 0))
                    for table in tables
                ),
            },
            "sheets": sheets,
        }


def predict_excel(
    model_path: Path | str,
    excel_path: Path | str,
    device_name: str | None = None,
) -> dict[str, Any]:
    return EFormPredictor(model_path, device_name).predict(excel_path)
