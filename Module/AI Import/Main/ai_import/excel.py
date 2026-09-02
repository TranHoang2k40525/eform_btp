from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

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


class WorkbookAnalyzer:
    def __init__(self, config: Settings):
        self.config = config

    def analyze(self, raw_path: str, include_hidden: bool = False, preview_rows: int = 100) -> WorkbookAnalysisDto:
        started = time.perf_counter()
        path, digest = validate_workbook_path(raw_path, self.config)
        workbook = load_workbook(path, read_only=False, data_only=False, keep_links=False)
        sheets: list[SheetAnalysisDto] = []
        warnings: list[str] = []
        try:
            for worksheet in workbook.worksheets:
                if worksheet.sheet_state != "visible" and not include_hidden:
                    continue
                if worksheet.max_row > self.config.max_rows or worksheet.max_column > self.config.max_columns:
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
                    for row in worksheet.iter_rows(min_row=1, max_row=min(worksheet.max_row, 10))
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
                merges = [str(item) for item in worksheet.merged_cells.ranges]
                sheets.append(SheetAnalysisDto(name=worksheet.title, state=worksheet.sheet_state,
                    row_count=row_count, column_count=column_count, merged_ranges=merges,
                    regions=regions, warnings=[] if regions else ["Không phát hiện được vùng bảng đủ tin cậy."]))
        finally:
            workbook.close()
        return WorkbookAnalysisDto(file_name=Path(path).name, sha256=digest, sheets=sheets, warnings=warnings,
            elapsed_ms=round((time.perf_counter() - started) * 1000, 2))

