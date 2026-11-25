from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

import torch
from openpyxl import load_workbook
from openpyxl.utils.cell import range_boundaries

from eform_ai.encoder import (
    cell_value,
    clean_text,
    encode_sheet,
    fold_text,
    is_numeric_text,
    is_roman_numeral,
    row_has_code_sequence,
)
from eform_ai.schema import (
    CELL_HEADER_CODE,
    CELL_HEADER_TITLE,
    CELL_OUTSIDE,
    CELL_VALUE,
    COL_CODE,
    COL_DATA,
    COL_LABEL,
    COL_NOTE,
    COL_OUTSIDE,
    FEATURE_CHANNELS,
    ROW_DATA,
    ROW_DETAIL,
    ROW_EMPTY,
    ROW_GRAND_TOTAL,
    ROW_ITEM,
    ROW_OUTSIDE_OR_HEADER,
    ROW_SECTION,
    ROW_SUBITEM,
    ROW_UNCLASSIFIED,
)

# Offline-only supervision helpers for column roles and row types during dataset caching.
_OFFLINE_TOTAL_RE = re.compile(r"^(tong so|tong cong|cong chung)(?:\b|$)")
_OFFLINE_SECTION_LABEL_RE = re.compile(r"^(?:muc|phan)\s+([ivxlcdm]+)(?:\b|$)")
_OFFLINE_LABEL_HDR_RE = re.compile(r"\b(chi tieu|noi dung|ten don vi|don vi|co quan|to chuc|loai hinh)\b")
_OFFLINE_NOTE_HDR_RE = re.compile(r"\b(ghi chu|chu thich|nhan xet)\b")
_OFFLINE_STT_HDR_RE = re.compile(r"\b(stt|so thu tu|ma so)\b")
_OFFLINE_INT_RE = re.compile(r"^\d+$")
_OFFLINE_DEC_RE = re.compile(r"^\d+(?:\.\d+)+$")

CACHE_VERSION = "cache-v2.2-enriched"


def _is_label_text_offline(value: Any) -> bool:
    if value is None or isinstance(value, (int, float, bool)):
        return False
    text = clean_text(value)
    if len(text) < 3 or text.startswith("#") or is_numeric_text(text):
        return False
    return sum(ch.isalpha() for ch in text) >= 2


def _build_col_roles_offline(
    worksheet: Any, table: dict[str, int], cols: int
) -> tuple[torch.Tensor, int | None, int | None]:
    roles = torch.full((cols,), COL_OUTSIDE, dtype=torch.long)
    top, left = table["top"], table["left"]
    bottom, right = table["bottom"], table["right"]
    hb = table["header_bottom"]

    roles[left - 1:right] = COL_DATA

    hdr_texts: dict[int, str] = {}
    merges = [range_boundaries(str(mr)) for mr in worksheet.merged_cells.ranges]
    for c in range(left, right + 1):
        parts: list[str] = []
        for r in range(top, hb + 1):
            val = cell_value(worksheet, r, c)
            if val is None:
                for ml, mt, mr, mb in merges:
                    if ml <= c <= mr and mt <= r <= mb:
                        val = cell_value(worksheet, mt, ml)
                        break
            t = clean_text(val)
            if t:
                parts.append(t)
        hdr_texts[c] = fold_text(" ".join(parts))

    value_rows = list(range(hb + 1, bottom + 1))

    def col_label_stats(c: int) -> tuple[float, int, int]:
        filled = 0
        labels = 0
        distinct: set[str] = set()
        for r in value_rows:
            v = cell_value(worksheet, r, c)
            if clean_text(v):
                filled += 1
                if _is_label_text_offline(v):
                    labels += 1
                    distinct.add(fold_text(v))
        return (labels / filled if filled else 0.0), labels, len(distinct)

    code_col: int | None = None
    label_col: int | None = None

    for c in range(left, right + 1):
        if _OFFLINE_NOTE_HDR_RE.search(hdr_texts[c]):
            roles[c - 1] = COL_NOTE

    for c in range(left, min(right + 1, left + 3)):
        if _OFFLINE_STT_HDR_RE.search(hdr_texts[c]):
            code_col = c
            break
    if code_col is None and value_rows:
        for c in range(left, min(right + 1, left + 2)):
            matches = 0
            for r in value_rows:
                raw = re.sub(r"[\s.):]+$", "", clean_text(cell_value(worksheet, r, c)))
                if raw.startswith("(") and raw.endswith(")"):
                    raw = raw[1:-1].strip()
                if is_roman_numeral(raw) or _OFFLINE_INT_RE.fullmatch(raw) or _OFFLINE_DEC_RE.fullmatch(raw):
                    matches += 1
            if matches >= max(2, math.ceil(len(value_rows) * 0.15)):
                code_col = c
                break

    for c in range(left, right + 1):
        if c == code_col or roles[c - 1] == COL_NOTE:
            continue
        share, count, distinct = col_label_stats(c)
        is_content_label = (
            (not value_rows and _OFFLINE_LABEL_HDR_RE.search(hdr_texts[c]))
            or (
                share >= 0.50
                and count >= max(1, math.ceil(len(value_rows) * 0.30))
                and distinct >= max(1, math.ceil(count * 0.45))
            )
        )
        if _OFFLINE_LABEL_HDR_RE.search(hdr_texts[c]) and is_content_label:
            label_col = c
            break

    if label_col is None and value_rows:
        best: tuple[int, int] | None = None
        for c in range(left, right + 1):
            if c == code_col:
                continue
            share, count, distinct = col_label_stats(c)
            if (
                share >= 0.50
                and count >= max(1, math.ceil(len(value_rows) * 0.30))
                and distinct >= max(1, math.ceil(count * 0.45))
            ):
                if best is None or count > best[1]:
                    best = (c, count)
        if best is not None:
            label_col = best[0]

    if code_col is not None:
        roles[code_col - 1] = COL_CODE
    if label_col is not None and label_col != code_col:
        roles[label_col - 1] = COL_LABEL

    return roles, code_col, label_col


def _build_row_types_offline(
    worksheet: Any,
    table: dict[str, int],
    rows: int,
    code_col: int | None,
    label_col: int | None,
) -> torch.Tensor:
    row_types = torch.full((rows,), ROW_OUTSIDE_OR_HEADER, dtype=torch.long)
    left, right = table["left"], table["right"]
    hb, bottom = table["header_bottom"], table["bottom"]

    for r in range(hb + 1, bottom + 1):
        vals = [cell_value(worksheet, r, c) for c in range(left, right + 1)]
        nonempty = sum(bool(clean_text(v)) for v in vals)
        code = ""
        if code_col is not None:
            code = re.sub(r"[\s.):]+$", "", clean_text(cell_value(worksheet, r, code_col)))
            if code.startswith("(") and code.endswith(")"):
                code = code[1:-1].strip()
        label = clean_text(cell_value(worksheet, r, label_col)) if label_col is not None else ""
        folded = fold_text(label)

        if nonempty == 0:
            rt = ROW_EMPTY
        elif _OFFLINE_TOTAL_RE.search(folded):
            rt = ROW_GRAND_TOTAL
        else:
            sec_match = _OFFLINE_SECTION_LABEL_RE.search(folded)
            if sec_match and not code:
                code = sec_match.group(1).upper()
            if is_roman_numeral(code):
                rt = ROW_SECTION
            elif _OFFLINE_DEC_RE.fullmatch(code):
                rt = ROW_SUBITEM
            elif _OFFLINE_INT_RE.fullmatch(code):
                rt = ROW_ITEM
            elif label:
                rt = ROW_DETAIL if not code else ROW_UNCLASSIFIED
            else:
                rt = ROW_DATA
        row_types[r - 1] = rt

    return row_types


def _build_sheet_targets(
    worksheet: Any,
    rows: int,
    cols: int,
    tables: list[dict[str, int]],
    col_mismatch_cols: list[int],
) -> dict[str, torch.Tensor]:
    cell_target = torch.full((rows, cols), CELL_OUTSIDE, dtype=torch.long)
    table_start = torch.zeros((rows,), dtype=torch.float32)
    col_role = torch.full((cols,), COL_OUTSIDE, dtype=torch.long)
    col_mismatch = torch.zeros((cols,), dtype=torch.float32)
    row_type = torch.full((rows,), ROW_OUTSIDE_OR_HEADER, dtype=torch.long)

    for col_1based in col_mismatch_cols:
        if 1 <= int(col_1based) <= cols:
            col_mismatch[int(col_1based) - 1] = 1.0

    if not tables:
        return {
            "cell_target": cell_target,
            "table_start": table_start,
            "col_role": col_role,
            "col_mismatch": col_mismatch,
            "row_type": row_type,
        }

    sorted_for_col = sorted(
        tables,
        key=lambda t: (t["bottom"] - t["top"] + 1) * (t["right"] - t["left"] + 1),
    )

    for table in sorted_for_col:
        top, left = table["top"], table["left"]
        bottom, right = table["bottom"], table["right"]
        hb = table["header_bottom"]

        table_start[top - 1] = 1.0

        hb_vals = [cell_value(worksheet, hb, c) for c in range(left, right + 1)]
        has_code_row = hb > top and row_has_code_sequence(hb_vals)

        if has_code_row:
            cell_target[top - 1:hb - 1, left - 1:right] = CELL_HEADER_TITLE
            cell_target[hb - 1, left - 1:right] = CELL_HEADER_CODE
        else:
            cell_target[top - 1:hb, left - 1:right] = CELL_HEADER_TITLE

        if hb < bottom:
            cell_target[hb:bottom, left - 1:right] = CELL_VALUE

        t_col_role, code_col, label_col = _build_col_roles_offline(worksheet, table, cols)
        mask = t_col_role != COL_OUTSIDE
        col_role[mask] = t_col_role[mask]

        t_row_type = _build_row_types_offline(worksheet, table, rows, code_col, label_col)
        rt_mask = t_row_type != ROW_OUTSIDE_OR_HEADER
        row_type[rt_mask] = t_row_type[rt_mask]

    return {
        "cell_target": cell_target,
        "table_start": table_start,
        "col_role": col_role,
        "col_mismatch": col_mismatch,
        "row_type": row_type,
    }


def build_or_load_cache(
    module_root: Path,
    cache_path: Path | None = None,
    force_rebuild: bool = False,
) -> dict[str, Any]:
    """Encode all workbooks (clean Raw + physical Raw_Variants) in Data/dataset.jsonl ONCE
    into a fast PyTorch tensor cache."""
    module_root = module_root.resolve()
    dataset_path = module_root / "Data" / "dataset.jsonl"
    report_path = module_root / "Data" / "dataset_report.json"
    if not dataset_path.is_file() or not report_path.is_file():
        raise FileNotFoundError("Thiếu Data/dataset.jsonl hoặc Data/dataset_report.json. Hãy chạy BuildDataset.ipynb trước.")

    dataset_report = json.loads(report_path.read_text(encoding="utf-8"))
    dataset_sha = dataset_report["dataset_sha256"]

    if cache_path is None:
        cache_path = module_root / "Train" / ".cache" / "encoded_dataset_v2.pt"

    if not force_rebuild and cache_path.is_file():
        cached = torch.load(cache_path, map_location="cpu", weights_only=False)
        if (
            cached.get("cache_version") == CACHE_VERSION
            and cached.get("dataset_sha256") == dataset_sha
            and cached.get("feature_channels") == FEATURE_CHANNELS
        ):
            print(f"Loaded pre-encoded cache: {cache_path} ({len(cached['samples'])} samples)")
            return cached

    records = [
        json.loads(line)
        for line in dataset_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    # Group records by workbook file so multi-sheet workbooks are opened only ONCE
    records_by_file: dict[str, list[dict[str, Any]]] = {}
    for rec in records:
        records_by_file.setdefault(rec["source_file"], []).append(rec)

    samples: list[dict[str, Any]] = []
    top_outside_pool: list[torch.Tensor] = []
    bottom_outside_pool: list[torch.Tensor] = []

    print(f"Building pre-encoded tensor cache for {len(records)} sheets ({len(records_by_file)} workbooks)...")
    processed_sheets = 0
    for source_file, file_records in records_by_file.items():
        wb = load_workbook(
            module_root / source_file,
            read_only=False,
            data_only=False,
            keep_links=False,
        )
        try:
            for record in file_records:
                ws = wb.worksheets[record["sheet_index"]]
                rows, cols = record["sheet_shape"]
                if rows == 0 or cols == 0:
                    continue
                features = encode_sheet(ws, rows, cols)
                tables = record["tables"]
                col_mismatch_cols = record.get("col_mismatch_cols", [])
                targets = _build_sheet_targets(ws, rows, cols, tables, col_mismatch_cols)

                # Harvest real outside rows ONLY from train originals (zero leakage!)
                if record["split"] == "train" and record.get("variant_type", "original") == "original" and tables:
                    first_top = min(t["top"] for t in tables) - 1
                    last_bottom = max(t["bottom"] for t in tables)
                    for r in range(0, first_top):
                        row_feat = features[:, r, :]
                        if float(row_feat[0].sum()) > 0:
                            top_outside_pool.append(row_feat.half())
                    for r in range(last_bottom, rows):
                        row_feat = features[:, r, :]
                        if float(row_feat[0].sum()) > 0:
                            bottom_outside_pool.append(row_feat.half())

                samples.append({
                    "sample_id": record["sample_id"],
                    "source_file": source_file,
                    "sheet_index": record["sheet_index"],
                    "split": record["split"],
                    "layout_group": record["layout_group"],
                    "variant_type": record.get("variant_type", "original"),
                    "shape": (rows, cols),
                    "tables": tables,
                    "features": features.half(),
                    "cell_target": targets["cell_target"].to(torch.uint8),
                    "table_start": targets["table_start"].to(torch.uint8),
                    "col_role": targets["col_role"].to(torch.uint8),
                    "col_mismatch": targets["col_mismatch"].to(torch.uint8),
                    "row_type": targets["row_type"].to(torch.uint8),
                })
                processed_sheets += 1
                if processed_sheets % 400 == 0 or processed_sheets == len(records):
                    print(f"  Encoded {processed_sheets}/{len(records)} sheets...")
        finally:
            wb.close()

    if len(top_outside_pool) > 1500:
        step = len(top_outside_pool) // 1500
        top_outside_pool = top_outside_pool[::max(1, step)][:1500]
    if len(bottom_outside_pool) > 2500:
        step = len(bottom_outside_pool) // 2500
        bottom_outside_pool = bottom_outside_pool[::max(1, step)][:2500]

    payload = {
        "cache_version": CACHE_VERSION,
        "dataset_sha256": dataset_sha,
        "feature_channels": FEATURE_CHANNELS,
        "clean_summary": dataset_report.get("label_cleaning_summary", {}),
        "variant_type_counts": dataset_report.get("variant_type_counts", {}),
        "samples": samples,
        "top_outside_pool": top_outside_pool,
        "bottom_outside_pool": bottom_outside_pool,
    }
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(payload, cache_path)
    print(
        f"Saved cache -> {cache_path} ({len(samples)} sheets) | "
        f"top_pool={len(top_outside_pool)}, bottom_pool={len(bottom_outside_pool)}"
    )
    return payload
