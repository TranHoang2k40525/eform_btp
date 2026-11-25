from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from datetime import date, datetime, time
from typing import Any

import torch
from openpyxl.cell.cell import MergedCell
from openpyxl.utils.cell import range_boundaries

from eform_ai.schema import (
    CH_ALPHA_RATIO,
    CH_BOLD,
    CH_BOOLEAN,
    CH_BORDER,
    CH_BULLET_START,
    CH_CENTERED,
    CH_CODE_SEQ_ROW,
    CH_DECIMAL_INDEX,
    CH_FORMULA,
    CH_FORMULA_ERROR,
    CH_HAS_COLON,
    CH_INT_INDEX,
    CH_LETTER_CODE,
    CH_MERGE_ANCHOR,
    CH_MERGE_COLSPAN,
    CH_MERGE_ROWSPAN,
    CH_MERGED,
    CH_NEG_INT,
    CH_NONEMPTY,
    CH_NUMERIC,
    CH_NUMERIC_TEXT,
    CH_PAREN_CODE,
    CH_PLACEHOLDER,
    CH_ROMAN_CODE,
    CH_TEMPORAL,
    CH_TEXT,
    CH_TEXT_HASH_START,
    CH_TEXT_LEN,
    CH_UPPER_RATIO,
    FEATURE_CHANNELS,
    TEXT_HASH_DIM,
)

NUMBER_IN_TEXT_RE = re.compile(r"\d+(?:[.,]\d+)*")
NUMERIC_TEXT_RE = re.compile(
    r"^[-+]?(?:\d{1,3}(?:[.,]\d{3})+(?:[.,]\d+)?|\d+(?:[.,]\d+)?)%?$"
)
FORMULA_ERROR_RE = re.compile(
    r"^#(?:ERROR|VALUE|REF|DIV/0|NAME\?|N/A|NUM|NULL)!?$", re.IGNORECASE
)
PLACEHOLDER_RE = re.compile(r"^(?:[-–—]+|[xX]|…|\.{2,3})$")
PAREN_CODE_RE = re.compile(r"^\(\s*\d{1,3}\s*\)$")
LETTER_CODE_RE = re.compile(r"^[A-Za-z]{1,2}$")
CODE_TOKEN_NUM_RE = re.compile(r"^\(?-?(\d{1,3})\)?(?:\.0)?$")
ROMAN_CODE_RE = re.compile(
    r"^(?:M{0,3})(?:CM|CD|D?C{0,3})(?:XC|XL|L?X{0,3})(?:IX|IV|V?I{0,3})$",
    re.IGNORECASE,
)
DECIMAL_INDEX_RE = re.compile(r"^\d+(?:\.\d+)+$")
WORD_TOKEN_RE = re.compile(r"[a-z0-9<>]+")


def clean_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value if value is not None else "")).strip()


def fold_text(value: Any) -> str:
    text = unicodedata.normalize("NFD", clean_text(value).lower())
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return re.sub(r"\s+", " ", text.replace("đ", "d")).strip()


def json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else str(value)
    if isinstance(value, (date, datetime, time)):
        return value.isoformat()
    return str(value)


def cell_value(worksheet: Any, row: int, column: int) -> Any:
    cell = worksheet.cell(row, column)
    return None if isinstance(cell, MergedCell) else cell.value


def parse_integer(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str) and re.fullmatch(r"[-+]?\d+", value.strip()):
        return int(value.strip())
    return None


def is_formula_error(value: Any, data_type: str = "") -> bool:
    if data_type == "e":
        return True
    if isinstance(value, str) and value.startswith("#"):
        return bool(FORMULA_ERROR_RE.fullmatch(value.strip()))
    return False


def is_numeric_text(text: str) -> bool:
    return bool(text) and bool(NUMERIC_TEXT_RE.fullmatch(text))


def is_roman_numeral(text: str) -> bool:
    stripped = re.sub(r"[\s.):]+$", "", text.strip())
    if stripped.startswith("(") and stripped.endswith(")"):
        stripped = stripped[1:-1].strip()
    return bool(stripped) and len(stripped) <= 8 and bool(ROMAN_CODE_RE.fullmatch(stripped))


def value_kind(value: Any, data_type: str) -> str:
    if value is None or (isinstance(value, str) and not value.strip()):
        return "blank"
    if is_formula_error(value, data_type):
        return "error"
    if data_type == "f" or (isinstance(value, str) and value.startswith("=")):
        return "formula"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (date, datetime, time)):
        return "temporal"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return "numeric"
    return "text"


def text_hash(text: str, dim: int = TEXT_HASH_DIM) -> list[float]:
    """Deterministic value-safe word + char 3-gram feature hashing."""
    vector = [0.0] * dim
    normalized = NUMBER_IN_TEXT_RE.sub("<N>", fold_text(text))[:256]
    if not normalized:
        return vector

    tokens: list[str] = []
    # Whole-word tokens (weighted higher to preserve lexical cues without vocab files)
    for word in WORD_TOKEN_RE.findall(normalized):
        tokens.append(f"w:{word}")
        tokens.append(f"w:{word}")
    # Character 3-grams for morphological robustness
    padded = f"^{normalized}$"
    for index in range(max(1, len(padded) - 2)):
        tokens.append(f"c:{padded[index:index + 3]}")

    for token in tokens:
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=4).digest()
        number = int.from_bytes(digest, "little")
        vector[number % dim] += -1.0 if number & 1 else 1.0

    norm = math.sqrt(sum(v * v for v in vector))
    if norm > 1e-8:
        return [v / norm for v in vector]
    return vector


def row_has_code_sequence(values: list[Any]) -> bool:
    """Universal structural indicator: row consists of sequential column index codes
    such as (1),(2)... or -1,-2... or A,B,1,2... (order-agnostic for swapped cols)."""
    numbers: list[int] = []
    nonempty = 0
    for value in values:
        text = clean_text(value)
        if not text:
            continue
        nonempty += 1
        if LETTER_CODE_RE.fullmatch(text):
            continue
        match = CODE_TOKEN_NUM_RE.fullmatch(text)
        if not match:
            return False
        numbers.append(int(match.group(1)))
    if len(numbers) < 2:
        return False
    # Allow sparse gaps (e.g. merged col codes) if mostly consecutive from 1
    unique_sorted = sorted(set(numbers))
    if len(unique_sorted) != len(numbers):
        return False
    return unique_sorted[0] == 1 and unique_sorted[-1] <= len(numbers) + 2


def row_code_sequence_spans(row_items: list[tuple[int, Any]]) -> list[tuple[int, int]]:
    """Find contiguous horizontal column spans (1-based left, right) that form a column-code
    sequence such as (1),(2)... or -1,-2... or A,B,1,2... — works cleanly even when two tables
    sit side by side on the same sheet row."""
    if not row_items:
        return []
    ordered = sorted(row_items, key=lambda x: x[0])
    # Split into horizontal clusters separated by >= 2 blank columns (side-by-side tables)
    clusters: list[list[tuple[int, Any]]] = [[ordered[0]]]
    for col, val in ordered[1:]:
        if col - clusters[-1][-1][0] >= 3:
            clusters.append([(col, val)])
        else:
            clusters[-1].append((col, val))
    spans: list[tuple[int, int]] = []
    for cluster in clusters:
        vals = [v for _, v in cluster]
        if row_has_code_sequence(vals):
            spans.append((cluster[0][0], cluster[-1][0]))
    return spans


def actual_bounds(worksheet: Any) -> tuple[int, int]:
    max_row = 0
    max_column = 0
    for cell in getattr(worksheet, "_cells", {}).values():
        value = getattr(cell, "value", None)
        if value is not None and (not isinstance(value, str) or value.strip()):
            max_row = max(max_row, int(cell.row))
            max_column = max(max_column, int(cell.column))
    for merged_range in worksheet.merged_cells.ranges:
        _, _, right, bottom = range_boundaries(str(merged_range))
        max_row = max(max_row, bottom)
        max_column = max(max_column, right)
    return max_row, max_column


def encode_sheet(worksheet: Any, rows: int, columns: int) -> torch.Tensor:
    """Convert an Excel worksheet into a translation-invariant CxHxW float32 tensor.

    Optimized to inspect populated cells directly from openpyxl's sparse _cells dict
    so even 2,500-row sheets encode in milliseconds.
    """
    features = torch.zeros((FEATURE_CHANNELS, rows, columns), dtype=torch.float32)
    if rows == 0 or columns == 0:
        return features

    # Pre-index merged cells to skip MergedCell slaves cleanly and populate merge channels
    merged_slaves: set[tuple[int, int]] = set()
    for merged_range in worksheet.merged_cells.ranges:
        left, top, right, bottom = range_boundaries(str(merged_range))
        left, top = max(1, left), max(1, top)
        right, bottom = min(columns, right), min(rows, bottom)
        if left > right or top > bottom:
            continue
        features[CH_MERGED, top - 1:bottom, left - 1:right] = 1.0
        features[CH_MERGE_ANCHOR, top - 1, left - 1] = 1.0
        features[CH_MERGE_ROWSPAN, top - 1:bottom, left - 1:right] = min(bottom - top + 1, 20) / 20.0
        features[CH_MERGE_COLSPAN, top - 1:bottom, left - 1:right] = min(right - left + 1, 20) / 20.0
        for r in range(top, bottom + 1):
            for c in range(left, right + 1):
                if not (r == top and c == left):
                    merged_slaves.add((r, c))

    # Group populated cells by row from openpyxl's sparse cell store
    cells_by_row: dict[int, list[tuple[int, Any]]] = {}
    for (r, c), cell in getattr(worksheet, "_cells", {}).items():
        if 1 <= r <= rows and 1 <= c <= columns:
            cells_by_row.setdefault(r, []).append((c, cell))

    for r, row_cells in cells_by_row.items():
        row_index = r - 1
        row_items_for_code: list[tuple[int, Any]] = []
        for c, cell in row_cells:
            col_index = c - 1
            # Style features apply even to blank bordered cells!
            font = cell.font
            if font is not None and bool(getattr(font, "bold", False)):
                features[CH_BOLD, row_index, col_index] = 1.0
            alignment = cell.alignment
            if alignment is not None and getattr(alignment, "horizontal", None) in {
                "center",
                "centerContinuous",
            }:
                features[CH_CENTERED, row_index, col_index] = 1.0
            border = cell.border
            if border is not None:
                b_count = 0
                if getattr(getattr(border, "left", None), "style", None):
                    b_count += 1
                if getattr(getattr(border, "right", None), "style", None):
                    b_count += 1
                if getattr(getattr(border, "top", None), "style", None):
                    b_count += 1
                if getattr(getattr(border, "bottom", None), "style", None):
                    b_count += 1
                if b_count:
                    features[CH_BORDER, row_index, col_index] = b_count / 4.0

            if (r, c) in merged_slaves or isinstance(cell, MergedCell):
                continue

            value = cell.value
            data_type = getattr(cell, "data_type", "") or ""
            kind = value_kind(value, data_type)
            if kind == "blank":
                continue

            row_items_for_code.append((c, value))
            features[CH_NONEMPTY, row_index, col_index] = 1.0
            if kind == "text":
                features[CH_TEXT, row_index, col_index] = 1.0
            elif kind == "numeric":
                features[CH_NUMERIC, row_index, col_index] = 1.0
            elif kind == "formula":
                features[CH_FORMULA, row_index, col_index] = 1.0
            elif kind == "temporal":
                features[CH_TEMPORAL, row_index, col_index] = 1.0
            elif kind == "boolean":
                features[CH_BOOLEAN, row_index, col_index] = 1.0
            elif kind == "error":
                features[CH_FORMULA_ERROR, row_index, col_index] = 1.0

            integer = parse_integer(value)
            if integer is not None:
                if integer < 0:
                    features[CH_NEG_INT, row_index, col_index] = 1.0
                elif 1 <= integer <= 9999:
                    features[CH_INT_INDEX, row_index, col_index] = 1.0

            if kind == "text":
                text = clean_text(value)
                features[CH_TEXT_LEN, row_index, col_index] = min(len(text), 200) / 200.0
                if is_numeric_text(text):
                    features[CH_NUMERIC_TEXT, row_index, col_index] = 1.0
                if PLACEHOLDER_RE.fullmatch(text):
                    features[CH_PLACEHOLDER, row_index, col_index] = 1.0
                if PAREN_CODE_RE.fullmatch(text):
                    features[CH_PAREN_CODE, row_index, col_index] = 1.0
                if LETTER_CODE_RE.fullmatch(text):
                    features[CH_LETTER_CODE, row_index, col_index] = 1.0
                if is_roman_numeral(text):
                    features[CH_ROMAN_CODE, row_index, col_index] = 1.0
                if DECIMAL_INDEX_RE.fullmatch(re.sub(r"[\s.):]+$", "", text)):
                    features[CH_DECIMAL_INDEX, row_index, col_index] = 1.0

                alpha_chars = [ch for ch in text if ch.isalpha()]
                if text:
                    features[CH_ALPHA_RATIO, row_index, col_index] = len(alpha_chars) / len(text)
                if alpha_chars:
                    upper_count = sum(1 for ch in alpha_chars if ch.isupper())
                    features[CH_UPPER_RATIO, row_index, col_index] = upper_count / len(alpha_chars)
                if text.startswith(("*", "- ", "+ ", "•")):
                    features[CH_BULLET_START, row_index, col_index] = 1.0
                if ":" in text:
                    features[CH_HAS_COLON, row_index, col_index] = 1.0

                hashed = text_hash(text)
                features[CH_TEXT_HASH_START:, row_index, col_index] = torch.tensor(
                    hashed, dtype=torch.float32
                )

        if row_items_for_code:
            for span_left, span_right in row_code_sequence_spans(row_items_for_code):
                features[CH_CODE_SEQ_ROW, row_index, span_left - 1:span_right] = 1.0

    return features
