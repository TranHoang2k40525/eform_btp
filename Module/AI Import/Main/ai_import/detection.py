from __future__ import annotations

from collections.abc import Sequence
from typing import Any


def _non_empty(value: Any) -> bool:
    return value is not None and str(value).strip() != ""


def _text_ratio(row: Sequence[Any]) -> float:
    values = [value for value in row if _non_empty(value)]
    if not values:
        return 0.0
    return sum(isinstance(value, str) and not str(value).startswith("=") for value in values) / len(values)


def find_row_bands(matrix: list[list[Any]], minimum_filled: int = 2) -> list[tuple[int, int]]:
    """Return 0-based inclusive bands, joining gaps of one empty row."""
    active = [sum(_non_empty(value) for value in row) >= minimum_filled for row in matrix]
    bands: list[tuple[int, int]] = []
    start: int | None = None
    empty_run = 0
    for index, is_active in enumerate(active):
        if is_active:
            if start is None:
                start = index
            empty_run = 0
        elif start is not None:
            empty_run += 1
            if empty_run > 1:
                bands.append((start, index - empty_run))
                start = None
                empty_run = 0
    if start is not None:
        bands.append((start, len(active) - 1 - empty_run))
    return [band for band in bands if band[1] >= band[0]]


def choose_header_rows(
    matrix: list[list[Any]], start: int, end: int, bold_rows: set[int] | None = None
) -> tuple[int, int, float]:
    bold_rows = bold_rows or set()
    candidates = range(start, min(end + 1, start + 8))
    scored: list[tuple[float, int]] = []
    for index in candidates:
        row = matrix[index]
        filled = sum(_non_empty(value) for value in row)
        if filled == 0:
            continue
        density = filled / max(1, len(row))
        score = 0.55 * _text_ratio(row) + 0.30 * min(1.0, density * 2)
        if index in bold_rows:
            score += 0.15
        scored.append((score, index))
    if not scored:
        return start, start, 0.0
    best_score, best = max(scored)
    header_end = best
    if best + 1 <= end:
        next_row = matrix[best + 1]
        next_filled = [value for value in next_row if _non_empty(value)]
        if next_filled and _text_ratio(next_row) >= 0.75 and len(next_filled) >= 2:
            header_end = best + 1
    return best, header_end, min(1.0, best_score)


def flatten_headers(matrix: list[list[Any]], start_row: int, end_row: int, start_col: int, end_col: int) -> list[str]:
    headers: list[str] = []
    inherited: list[Any] = [None] * (end_col + 1)
    for row_index in range(start_row, end_row + 1):
        last_value: Any = None
        for col_index in range(start_col, end_col + 1):
            value = matrix[row_index][col_index] if col_index < len(matrix[row_index]) else None
            if _non_empty(value):
                last_value = value
                inherited[col_index] = value
            elif last_value is not None:
                inherited[col_index] = last_value
    for col_index in range(start_col, end_col + 1):
        parts: list[str] = []
        for row_index in range(start_row, end_row + 1):
            value = matrix[row_index][col_index] if col_index < len(matrix[row_index]) else None
            if not _non_empty(value):
                value = inherited[col_index]
            text = str(value).strip() if _non_empty(value) else ""
            if text and (not parts or parts[-1] != text):
                parts.append(text)
        headers.append(" / ".join(parts) or f"Cột {col_index + 1}")
    return headers

