from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from openpyxl.utils import get_column_letter
from openpyxl.utils.cell import range_boundaries

from eform_ai.encoder import cell_value, clean_text, is_formula_error, json_safe

CODE_NUMBER_RE = re.compile(r"^\(?-?(\d{1,3})\)?$")
ROW_CODE_TRIM_RE = re.compile(r"[\s.):]+$")


def _excel_color(value: Any) -> str | None:
    if value is None or getattr(value, "type", None) != "rgb":
        return None
    rgb = str(getattr(value, "rgb", "") or "")
    if len(rgb) == 8:
        rgb = rgb[2:]
    if len(rgb) != 6 or not re.fullmatch(r"[0-9a-fA-F]{6}", rgb):
        return None
    return f"#{rgb.upper()}"


def _column_width_px(worksheet: Any, column: int) -> int:
    width = worksheet.column_dimensions[get_column_letter(column)].width
    return max(56, min(420, round(float(width or 11.5) * 7 + 12)))


def _row_height_px(worksheet: Any, row: int, is_header: bool) -> int:
    height = worksheet.row_dimensions[row].height
    if height is None:
        return 40 if is_header else 28
    return max(24, min(180, round(float(height) * 96 / 72)))


def _normalized_row_code(value: Any) -> str:
    text = clean_text(value)
    if len(text) >= 2 and text[0] == "(" and text[-1] == ")":
        text = text[1:-1].strip()
    return ROW_CODE_TRIM_RE.sub("", text).strip()


def _header_paths(
    data: list[list[Any]],
    merges: list[dict[str, int]],
    header_rows: int,
    left: int,
    model_code_rows: list[int],
) -> list[dict[str, Any]]:
    if not data:
        return []
    resolved = [list(row) for row in data[:header_rows]]
    for merged in merges:
        anchor_row = int(merged["row"])
        anchor_column = int(merged["col"])
        if anchor_row >= header_rows:
            continue
        anchor = resolved[anchor_row][anchor_column]
        last_row = min(header_rows, anchor_row + int(merged["rowspan"]))
        last_column = min(len(resolved[0]), anchor_column + int(merged["colspan"]))
        for row in range(anchor_row, last_row):
            for column in range(anchor_column, last_column):
                resolved[row][column] = anchor

    col_count = len(resolved[0])
    column_codes = [""] * col_count
    code_row_set = set(model_code_rows)
    if code_row_set:
        code_row_idx = max(code_row_set)
        if 0 <= code_row_idx < header_rows:
            column_codes = [
                clean_text(v) if re.fullmatch(r"\(?-?\d{1,3}\)?|[A-Za-z]{1,2}", clean_text(v)) else ""
                for v in resolved[code_row_idx]
            ]

    result: list[dict[str, Any]] = []
    for column in range(col_count):
        path: list[str] = []
        for row in range(header_rows):
            if row in code_row_set:
                continue
            label = clean_text(resolved[row][column])
            if label and (not path or path[-1] != label):
                path.append(label)
        result.append({
            "columnIndex": column,
            "excelColumn": get_column_letter(left + column),
            "headerPath": path,
            "label": path[-1] if path else get_column_letter(left + column),
            "columnCode": column_codes[column],
        })
    return result


def _assemble_row_hierarchy(
    data: list[list[Any]],
    header_rows: int,
    top: int,
    code_column: int | None,
    label_column: int | None,
    predicted_row_types: list[tuple[str, float]],
    review_threshold: float = 0.65,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Assemble row hierarchy tree strictly from the neural model's rowType predictions
    and learned column identities (zero hardcoded keyword regexes)."""
    hierarchy: list[dict[str, Any]] = []
    stack: dict[int, dict[str, Any]] = {}
    counts: defaultdict[str, int] = defaultdict(int)

    for row_index in range(header_rows, len(data)):
        row = data[row_index]
        code = _normalized_row_code(row[code_column]) if code_column is not None and code_column < len(row) else ""
        label = clean_text(row[label_column]) if label_column is not None and label_column < len(row) else ""
        nonempty = sum(bool(clean_text(v)) for v in row)

        if nonempty == 0:
            row_type = "empty"
            confidence = 1.0
        elif row_index < len(predicted_row_types):
            row_type, confidence = predicted_row_types[row_index]
        else:
            row_type, confidence = "data", 0.5

        level: int | None = None
        if row_type == "grand_total":
            level = 0
        elif row_type == "section":
            level = 1
        elif row_type == "item":
            level = 2
        elif row_type == "subitem":
            level = 2 + max(1, code.count("."))
        elif row_type in {"detail", "unclassified"}:
            deepest = max(stack, default=0)
            level = deepest + 1 if stack else None

        requires_review = row_type == "unclassified" or confidence < review_threshold
        reason = (
            "Hàng trống được bảo toàn theo tệp Excel nguồn."
            if row_type == "empty"
            else f"Mô hình phân loại hàng là '{row_type}' (độ tin cậy {confidence:.2%})."
        )

        parent_row_index: int | None = None
        parent_path: list[str] = []
        if level is not None:
            parent_levels = [lvl for lvl in stack if lvl < level]
            if parent_levels:
                parent = stack[max(parent_levels)]
                parent_row_index = int(parent["rowIndex"])
                parent_path = list(parent["hierarchyPath"])
            for lvl in [lvl for lvl in stack if lvl >= level]:
                del stack[lvl]

        display_label = label or code
        hierarchy_path = [*parent_path, display_label] if display_label else parent_path
        item = {
            "rowIndex": row_index,
            "excelRow": top + row_index,
            "rowType": row_type,
            "level": level,
            "code": code,
            "label": label,
            "parentRowIndex": parent_row_index,
            "hierarchyPath": hierarchy_path,
            "mappingConfidence": round(float(confidence), 4),
            "requiresReview": requires_review,
            "reason": reason,
        }
        hierarchy.append(item)
        counts[row_type] += 1
        if requires_review:
            counts["requiresReview"] += 1
        if level is not None and row_type not in {"empty", "data", "unclassified"}:
            stack[level] = item

    return hierarchy, dict(sorted(counts.items()))


def _safety_column_checks(
    data: list[list[Any]],
    columns: list[dict[str, Any]],
    header_rows: int,
    label_column: int | None,
    col_mismatch_scores: list[float],
    mismatch_threshold: float = 0.55,
) -> tuple[list[str], list[str]]:
    """Combine learned column-mismatch predictions with deterministic safety guardrails
    (formula error cells and column code ordering)."""
    issues: list[str] = []
    notes: list[str] = []
    value_rows = data[header_rows:]
    if not value_rows:
        return issues, notes

    def col_desc(index: int) -> str:
        meta = columns[index] if index < len(columns) else {}
        letter = meta.get("excelColumn") or get_column_letter(index + 1)
        path = meta.get("headerPath") or []
        return f'{letter} "{path[-1]}"' if path else str(letter)

    # 1. Model-predicted column header vs content mismatch
    flagged_cols = [
        idx
        for idx, score in enumerate(col_mismatch_scores)
        if score >= mismatch_threshold and idx < len(columns)
    ]
    if flagged_cols:
        names = ", ".join(col_desc(idx) for idx in flagged_cols[:4])
        issues.append(
            f"Phát hiện cột có nội dung không khớp với tiêu đề ({names}); "
            "cần kiểm tra lại thứ tự cột trước khi nhập."
        )

    # 2. Deterministic guardrail: learned label column sits under a numbered numeric columnCode
    if label_column is not None and label_column < len(columns) and label_column not in flagged_cols:
        code_text = clean_text(columns[label_column].get("columnCode"))
        if CODE_NUMBER_RE.fullmatch(code_text):
            issues.append(
                f"Cột tên dòng đang nằm ở cột số liệu {col_desc(label_column)} (mã {code_text}); "
                "số liệu trong file không khớp với tiêu đề cột."
            )

    # 3. Deterministic guardrail: out-of-order numbered column codes (used by eForm auto-reorder)
    numbered: list[int] = []
    for column in columns:
        match = CODE_NUMBER_RE.fullmatch(clean_text(column.get("columnCode")))
        if match:
            numbered.append(int(match.group(1)))
    if len(numbered) >= 3 and len(set(numbered)) == len(numbered) and numbered != sorted(numbered):
        first_bad = next(i for i in range(1, len(numbered)) if numbered[i] < numbered[i - 1])
        notes.append(
            f"Thứ tự cột trong file khác thứ tự chuẩn của biểu mẫu (cột ({numbered[first_bad - 1]}) "
            f"đứng trước cột ({numbered[first_bad]})). Hãy kiểm tra lại trước khi nhập."
        )

    # 4. Deterministic guardrail: Excel formula errors
    error_cells = sum(
        1
        for row in value_rows
        for value in row
        if is_formula_error(value)
    )
    if error_cells:
        notes.append(f"Có {error_cells} ô bị lỗi công thức trong file (ví dụ #ERROR!).")

    return issues, notes


def extract_table_payload(
    worksheet: Any,
    table: dict[str, Any],
    value_worksheet: Any | None = None,
    mismatch_threshold: float = 0.55,
) -> dict[str, Any]:
    """Read verbatim data, formulas, styles, and merges for a model-predicted region."""
    top, left = int(table["top"]), int(table["left"])
    bottom, right = int(table["bottom"]), int(table["right"])
    header_rows = max(1, min(bottom - top + 1, int(table["header_bottom"]) - top + 1))

    data: list[list[Any]] = []
    formula_cells: list[dict[str, Any]] = []
    cell_styles: list[dict[str, Any]] = []

    for row in range(top, bottom + 1):
        output_row: list[Any] = []
        is_header = row < top + header_rows
        for column in range(left, right + 1):
            cell = worksheet.cell(row, column)
            source_value = cell_value(worksheet, row, column)
            output_value = source_value
            if getattr(cell, "data_type", "") == "f" and value_worksheet is not None:
                cached_value = cell_value(value_worksheet, row, column)
                if cached_value is not None:
                    output_value = cached_value
                formula_cells.append({
                    "row": row - top,
                    "col": column - left,
                    "formula": json_safe(source_value),
                    "cachedValue": json_safe(cached_value),
                })
            output_row.append(json_safe(output_value))

            alignment = cell.alignment
            fill = _excel_color(getattr(cell.fill, "fgColor", None)) if cell.fill and cell.fill.fill_type else None
            font_color = _excel_color(getattr(cell.font, "color", None)) if cell.font else None
            style = {
                "row": row - top,
                "col": column - left,
                "isHeader": is_header,
                "bold": bool(cell.font.bold) if cell.font else False,
                "italic": bool(cell.font.italic) if cell.font else False,
                "horizontal": alignment.horizontal if alignment else None,
                "vertical": alignment.vertical if alignment else None,
                "wrapText": bool(alignment.wrap_text) if alignment else False,
                "numberFormat": cell.number_format if cell.number_format != "General" else None,
                "fill": fill,
                "fontColor": font_color,
            }
            if is_header or any(
                v for k, v in style.items() if k not in {"row", "col", "isHeader"}
            ):
                cell_styles.append(style)
        data.append(output_row)

    merges: list[dict[str, int]] = []
    for merged_range in worksheet.merged_cells.ranges:
        merge_left, merge_top, merge_right, merge_bottom = range_boundaries(str(merged_range))
        clip_top, clip_left = max(top, merge_top), max(left, merge_left)
        clip_bottom, clip_right = min(bottom, merge_bottom), min(right, merge_right)
        if clip_top > clip_bottom or clip_left > clip_right:
            continue
        merge = {
            "row": clip_top - top,
            "col": clip_left - left,
            "rowspan": clip_bottom - clip_top + 1,
            "colspan": clip_right - clip_left + 1,
        }
        if merge["rowspan"] > 1 or merge["colspan"] > 1:
            merges.append(merge)
            if merge_top < top or merge_left < left:
                data[merge["row"]][merge["col"]] = json_safe(
                    cell_value(worksheet, merge_top, merge_left)
                )

    sorted_merges = sorted(merges, key=lambda item: (item["row"], item["col"]))
    rows = bottom - top + 1
    columns = right - left + 1

    column_metadata = _header_paths(
        data, sorted_merges, header_rows, left, list(table.get("code_rows", []))
    )
    code_column = table.get("code_col")
    label_column = table.get("label_col")
    row_metadata, hierarchy_summary = _assemble_row_hierarchy(
        data,
        header_rows,
        top,
        code_column,
        label_column,
        list(table.get("row_types", [])),
    )
    column_issues, column_notes = _safety_column_checks(
        data,
        column_metadata,
        header_rows,
        label_column,
        list(table.get("col_mismatch_scores", [])),
        mismatch_threshold=mismatch_threshold,
    )

    return {
        "sourceRange": f"{get_column_letter(left)}{top}:{get_column_letter(right)}{bottom}",
        "headerRows": header_rows,
        "rowCount": rows,
        "columnCount": columns,
        "valueRowCount": max(0, rows - header_rows),
        "data": data,
        "mergeCells": sorted_merges,
        "columns": column_metadata,
        "rows": row_metadata,
        "rowHierarchySummary": hierarchy_summary,
        "columnWidths": [_column_width_px(worksheet, col) for col in range(left, right + 1)],
        "rowHeights": [
            _row_height_px(worksheet, r, r < top + header_rows)
            for r in range(top, bottom + 1)
        ],
        "cellStyles": cell_styles,
        "formulaCells": formula_cells,
        "confidence": table.get("confidence"),
        "postprocessing": "neural-direct-v2",
        "trimmedHeaderRows": 0,
        "trimmedFooterRows": 0,
        "labelColumnIndex": label_column,
        "columnIssues": column_issues,
        "columnNotes": column_notes,
    }


def _row_text_signature(row: list[Any]) -> tuple[str, ...]:
    return tuple(clean_text(v).lower() for v in row)


def _strip_repeated_header_blocks(table: dict[str, Any]) -> dict[str, Any]:
    """Remove any verbatim repeated header block inside value rows (e.g. printed page-break
    header repeats that stayed inside one table or straddled a split boundary)."""
    hdr_n = int(table["headerRows"])
    data = table["data"]
    if hdr_n < 1 or len(data) <= hdr_n:
        return table

    hdr_sigs = [_row_text_signature(r) for r in data[:hdr_n]]
    keep_mask = [True] * len(data)
    r = hdr_n
    while r < len(data):
        # Match full repeated header block (all hdr_n rows identical to original header)
        if r + hdr_n <= len(data) and all(
            _row_text_signature(data[r + k]) == hdr_sigs[k] for k in range(hdr_n)
        ):
            for k in range(hdr_n):
                keep_mask[r + k] = False
            r += hdr_n
            continue
        r += 1

    # Also trim trailing partial prefix of the repeated header at the very end of a split fragment
    # (handled before/after merging when a repeated header sits right at bottom of table)
    if all(keep_mask):
        return table

    old_to_new: dict[int, int] = {}
    new_data: list[list[Any]] = []
    new_heights: list[int] = []
    for idx, keep in enumerate(keep_mask):
        if keep:
            old_to_new[idx] = len(new_data)
            new_data.append(data[idx])
            if idx < len(table["rowHeights"]):
                new_heights.append(table["rowHeights"][idx])

    table["data"] = new_data
    table["rowHeights"] = new_heights
    table["cellStyles"] = [
        dict(s, row=old_to_new[int(s["row"])])
        for s in table.get("cellStyles", [])
        if int(s["row"]) in old_to_new
    ]
    table["mergeCells"] = [
        dict(m, row=old_to_new[int(m["row"])])
        for m in table.get("mergeCells", [])
        if int(m["row"]) in old_to_new
    ]
    table["formulaCells"] = [
        dict(fc, row=old_to_new[int(fc["row"])])
        for fc in table.get("formulaCells", [])
        if int(fc["row"]) in old_to_new
    ]
    new_rows: list[dict[str, Any]] = []
    for rm in table.get("rows", []):
        old_idx = int(rm["rowIndex"])
        if old_idx not in old_to_new:
            continue
        copied = dict(rm, rowIndex=old_to_new[old_idx])
        p_idx = copied.get("parentRowIndex")
        copied["parentRowIndex"] = old_to_new.get(int(p_idx)) if p_idx is not None else None
        new_rows.append(copied)
    table["rows"] = new_rows
    summary: defaultdict[str, int] = defaultdict(int)
    for rm in new_rows:
        summary[rm["rowType"]] += 1
        if rm.get("requiresReview"):
            summary["requiresReview"] += 1
    table["rowHierarchySummary"] = dict(sorted(summary.items()))
    table["rowCount"] = len(new_data)
    table["valueRowCount"] = max(0, table["rowCount"] - hdr_n)
    return table


def _headers_match_for_continuation(first: dict[str, Any], second: dict[str, Any]) -> bool:
    """True when two vertically adjacent tables on the same columns share identical column
    headers or when the boundary across (first tail + second header) reproduces first's header."""
    cols_a = first.get("columns") or []
    cols_b = second.get("columns") or []
    if not cols_a or len(cols_a) != len(cols_b):
        return False
    if [c["excelColumn"] for c in cols_a] != [c["excelColumn"] for c in cols_b]:
        return False

    # Direct column header path/code match
    matches = 0
    for ca, cb in zip(cols_a, cols_b):
        pa = [clean_text(x).lower() for x in ca.get("headerPath", [])]
        pb = [clean_text(x).lower() for x in cb.get("headerPath", [])]
        code_a = clean_text(ca.get("columnCode")).lower()
        code_b = clean_text(cb.get("columnCode")).lower()
        if pa == pb and (not code_a or not code_b or code_a == code_b):
            matches += 1
        elif pa and pb and pa[-1] == pb[-1] and code_a == code_b:
            matches += 1
    if matches / len(cols_a) >= 0.85:
        return True

    # Boundary-straddling repeated header check: first's trailing k rows + second's leading (hdr_a - k) rows == first's header
    hdr_a = int(first["headerRows"])
    data_a = first["data"]
    data_b = second["data"]
    if hdr_a >= 2 and len(data_a) > hdr_a:
        hdr_sigs = [_row_text_signature(r) for r in data_a[:hdr_a]]
        for k in range(1, min(hdr_a, len(data_a) - hdr_a + 1)):
            tail_a = [_row_text_signature(r) for r in data_a[-k:]]
            need_b = hdr_a - k
            if need_b <= len(data_b):
                head_b = [_row_text_signature(r) for r in data_b[:need_b]]
                if tail_a + head_b == hdr_sigs:
                    return True
    return False


def merge_repeated_header_tables(tables: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Combine vertically adjacent multi-page table fragments whose headers repeat verbatim,
    dropping the repeated header block while keeping all value rows intact."""
    if not tables:
        return tables

    merged: list[dict[str, Any]] = []
    for table in tables:
        if not merged:
            merged.append(_strip_repeated_header_blocks(table))
            continue

        prev = merged[-1]
        p_left, p_top, p_right, p_bottom = range_boundaries(prev["sourceRange"])
        c_left, c_top, c_right, c_bottom = range_boundaries(table["sourceRange"])

        if (
            p_left == c_left
            and p_right == c_right
            and 0 <= (c_top - p_bottom) <= 4
            and _headers_match_for_continuation(prev, table)
        ):
            # Concatenate all rows of `table` and strip the exact repeated header block cleanly
            # (handles both clean splits AND splits shifted by 1-2 rows into `prev`!)
            hdr_a = int(prev["headerRows"])
            hdr_b = int(table["headerRows"])
            hdr_sigs = [_row_text_signature(r) for r in prev["data"][:hdr_a]]

            # Check if a repeated header straddles the split boundary:
            # either (k rows in prev tail + (hdr_a-k) in table head == hdr_sigs),
            # OR prev's trailing k rows verbatim match the leading k rows of prev's own header!
            straddle_k = 0
            for k in range(min(hdr_a - 1, len(prev["data"]) - hdr_a), 0, -1):
                tail_a = [_row_text_signature(r) for r in prev["data"][-k:]]
                if tail_a == hdr_sigs[:k]:
                    straddle_k = k
                    break

            if straddle_k > 0:
                keep_prev_len = len(prev["data"]) - straddle_k
                prev["data"] = prev["data"][:keep_prev_len]
                prev["rowHeights"] = prev["rowHeights"][:keep_prev_len]
                prev["cellStyles"] = [s for s in prev.get("cellStyles", []) if int(s["row"]) < keep_prev_len]
                prev["mergeCells"] = [m for m in prev.get("mergeCells", []) if int(m["row"]) < keep_prev_len]
                prev["formulaCells"] = [fc for fc in prev.get("formulaCells", []) if int(fc["row"]) < keep_prev_len]
                prev["rows"] = [r for r in prev.get("rows", []) if int(r["rowIndex"]) < keep_prev_len]
                skip_b = min(len(table["data"]), max(hdr_b, hdr_a - straddle_k))
            else:
                skip_b = hdr_b

            val_data = table["data"][skip_b:]
            row_offset = len(prev["data"])
            prev["data"] = prev["data"] + val_data
            prev["rowHeights"] = prev["rowHeights"] + table["rowHeights"][skip_b:]

            for style in table.get("cellStyles", []):
                if int(style["row"]) >= skip_b:
                    shifted = dict(style)
                    shifted["row"] = int(style["row"]) - skip_b + row_offset
                    shifted["isHeader"] = False
                    prev["cellStyles"].append(shifted)

            for m in table.get("mergeCells", []):
                if int(m["row"]) >= skip_b:
                    shifted_m = dict(m)
                    shifted_m["row"] = int(m["row"]) - skip_b + row_offset
                    prev["mergeCells"].append(shifted_m)

            for fc in table.get("formulaCells", []):
                if int(fc["row"]) >= skip_b:
                    shifted_fc = dict(fc)
                    shifted_fc["row"] = int(fc["row"]) - skip_b + row_offset
                    prev["formulaCells"].append(shifted_fc)

            for r_meta in table.get("rows", []):
                if int(r_meta["rowIndex"]) >= skip_b:
                    shifted_r = dict(r_meta)
                    shifted_r["rowIndex"] = int(r_meta["rowIndex"]) - skip_b + row_offset
                    if shifted_r.get("parentRowIndex") is not None:
                        shifted_r["parentRowIndex"] = int(shifted_r["parentRowIndex"]) - skip_b + row_offset
                    prev["rows"].append(shifted_r)

            summary: defaultdict[str, int] = defaultdict(int)
            for r_meta in prev["rows"]:
                summary[r_meta["rowType"]] += 1
                if r_meta.get("requiresReview"):
                    summary["requiresReview"] += 1
            prev["rowHierarchySummary"] = dict(sorted(summary.items()))
            prev["rowCount"] = len(prev["data"])
            prev["valueRowCount"] = max(0, prev["rowCount"] - hdr_a)
            prev["sourceRange"] = (
                f"{get_column_letter(p_left)}{p_top}:{get_column_letter(p_right)}{c_bottom}"
            )
            if prev.get("confidence") is not None and table.get("confidence") is not None:
                prev["confidence"] = round((float(prev["confidence"]) + float(table["confidence"])) / 2.0, 4)
            _strip_repeated_header_blocks(prev)
            continue

        merged.append(_strip_repeated_header_blocks(table))
    return merged
