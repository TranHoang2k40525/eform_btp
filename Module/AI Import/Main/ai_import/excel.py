from __future__ import annotations

import time
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any

from openpyxl import load_workbook

from .config import Settings
from .detection import choose_header_rows, find_row_bands, flatten_headers
from .models import SheetAnalysisDto, TableRegionDto, WorkbookAnalysisDto
from .security import validate_workbook_path


def _trim_matrix(matrix: list[list[Any]]) -> tuple[list[list[Any]], int, int]:
    non_empty = [
        (r, c)
        for r, row in enumerate(matrix)
        for c, value in enumerate(row)
        if value is not None and str(value).strip() != ""
    ]
    if not non_empty:
        return [], 0, 0
    max_row = max(item[0] for item in non_empty)
    max_col = max(item[1] for item in non_empty)
    return [row[: max_col + 1] for row in matrix[: max_row + 1]], max_row + 1, max_col + 1


def _read_merge_ranges(workbook_path: Path, worksheet_path: str) -> list[str]:
    """Read merge refs directly; read-only openpyxl skips drawings/images and merged-cell objects."""
    ranges: list[str] = []
    namespace = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}mergeCell"
    normalized = worksheet_path.lstrip("/")
    with zipfile.ZipFile(workbook_path, "r") as archive, archive.open(normalized, "r") as stream:
        for _, element in ET.iterparse(stream, events=("end",)):
            if element.tag == namespace and element.attrib.get("ref"):
                ranges.append(element.attrib["ref"])
            element.clear()
    return ranges


class WorkbookAnalyzer:
    def __init__(self, config: Settings):
        self.config = config

    def analyze(self, raw_path: str, include_hidden: bool = False, preview_rows: int = 100) -> WorkbookAnalysisDto:
        started = time.perf_counter()
        path, digest = validate_workbook_path(raw_path, self.config)
        secured = time.perf_counter()
        # read_only avoids openpyxl's drawing/image loader. The service never inspects media entries.
        workbook = load_workbook(path, read_only=True, data_only=False, keep_links=False)
        parsed = time.perf_counter()
        sheets: list[SheetAnalysisDto] = []
        warnings: list[str] = []
        try:
            for worksheet in workbook.worksheets:
                if worksheet.sheet_state != "visible" and not include_hidden:
                    continue
                if worksheet.max_row is None or worksheet.max_column is None:
                    worksheet.calculate_dimension(force=True)
                max_row = worksheet.max_row or 0
                max_column = worksheet.max_column or 0
                if (max_row > self.config.max_rows or max_column > self.config.max_columns
                        or max_row * max_column > self.config.max_cells):
                    warnings.append(f"Bỏ qua sheet {worksheet.title}: vượt giới hạn hàng/cột.")
                    continue
                matrix = [list(row) for row in worksheet.iter_rows(values_only=True)]
                matrix, row_count, column_count = _trim_matrix(matrix)
                if not matrix:
                    sheets.append(SheetAnalysisDto(name=worksheet.title, state=worksheet.sheet_state, row_count=0,
                        column_count=0, merged_ranges=[], regions=[], warnings=["Sheet trống."]))
                    continue
                bold_rows = {
                    cell.row - 1
                    for row in worksheet.iter_rows(min_row=1, max_row=min(max_row, 10))
                    for cell in row
                    if cell.value is not None and cell.font and cell.font.bold
                }
                regions: list[TableRegionDto] = []
                for band_start, band_end in find_row_bands(matrix):
                    populated_columns = [
                        col for col in range(column_count)
                        if any(col < len(matrix[row]) and matrix[row][col] not in (None, "") for row in range(band_start, band_end + 1))
                    ]
                    if len(populated_columns) < 2:
                        continue
                    start_col, end_col = min(populated_columns), max(populated_columns)
                    header_start, header_end, confidence = choose_header_rows(matrix, band_start, band_end, bold_rows)
                    headers = flatten_headers(matrix, header_start, header_end, start_col, end_col)
                    data_start = min(header_end + 1, band_end + 1)
                    rows = [
                        [matrix[r][c] if c < len(matrix[r]) else None for c in range(start_col, end_col + 1)]
                        for r in range(data_start, min(band_end + 1, data_start + preview_rows))
                    ]
                    regions.append(TableRegionDto(sheet=worksheet.title, start_row=band_start + 1,
                        end_row=band_end + 1, start_column=start_col + 1, end_column=end_col + 1,
                        header_start_row=header_start + 1, header_end_row=header_end + 1,
                        data_start_row=data_start + 1, confidence=confidence, headers=headers, rows=rows))
                merges = _read_merge_ranges(path, worksheet._worksheet_path)
                sheets.append(SheetAnalysisDto(name=worksheet.title, state=worksheet.sheet_state,
                    row_count=row_count, column_count=column_count, merged_ranges=merges,
                    regions=regions, warnings=[] if regions else ["Không phát hiện được vùng bảng đủ tin cậy."]))
        finally:
            workbook.close()
        finished = time.perf_counter()
        return WorkbookAnalysisDto(file_name=Path(path).name, sha256=digest, sheets=sheets, warnings=warnings,
            timings_ms={"security": round((secured - started) * 1000, 2),
                        "parse": round((parsed - secured) * 1000, 2),
                        "table_detection": round((finished - parsed) * 1000, 2)},
            elapsed_ms=round((finished - started) * 1000, 2))
