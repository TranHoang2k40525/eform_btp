from __future__ import annotations

import copy
import json
import random
import re
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from openpyxl import load_workbook
from openpyxl.cell.cell import MergedCell
from openpyxl.styles import Alignment, Border, Font, Side
from openpyxl.utils.cell import range_boundaries

MODULE_ROOT_DEFAULT = Path(__file__).resolve().parent
if str(MODULE_ROOT_DEFAULT) not in sys.path:
    sys.path.insert(0, str(MODULE_ROOT_DEFAULT))

from dataset_builder import (  # noqa: E402
    BuildOptions,
    _actual_bounds,
    _cell_value,
    _write_atomic,
    build_base_records,
    clean_text,
    fold_text,
    stable_hash,
)
from eform_ai.encoder import row_has_code_sequence  # noqa: E402


FOOTER_TEMPLATES = [
    [
        'Ô có dấu "-" không phải báo cáo.',
        "- Cột (1), (2) tổng hợp theo số liệu thực tế trong kỳ báo cáo.",
        "- Số liệu đã được rà soát, đối chiếu trước khi gửi cơ quan chủ quản.",
        "* Ghi chú: Báo cáo gửi trước ngày 15 của tháng tiếp theo.",
        "Người lập biểu (Ký, ghi rõ họ tên)",
        "THỦ TRƯỞNG ĐƠN VỊ (Ký, đóng dấu)",
    ],
    [
        "Từ cột (1) đến cột (5) chỉ thống kê các hồ sơ đã hoàn thành trong kỳ.",
        "- Không cộng trùng số liệu giữa cấp tỉnh và cấp xã.",
        "Ghi chú: Các trường hợp phát sinh ngoài biểu đề nghị thuyết minh kèm theo.",
        "Người lập biểu",
        "Người kiểm tra",
        "GIÁM ĐỐC SỞ TƯ PHÁP (Ký, ghi rõ họ tên, đóng dấu)",
    ],
    [
        "* Ghi chú:",
        "- Số liệu báo cáo tính từ ngày 01/01 đến hết ngày 31/12.",
        "- Cột tổng số bằng tổng các cột thành phần theo quy định Thông tư.",
        "- Các ô trống biểu thị không phát sinh số liệu.",
        "…, ngày … tháng … năm 2026",
        "TM. ỦY BAN NHÂN DÂN — CHỦ TỊCH (Ký, đóng dấu)",
    ],
]

METADATA_TEMPLATES = [
    [
        "BỘ TƯ PHÁP",
        "BÁO CÁO THỐNG KÊ KẾT QUẢ CÔNG TÁC TRONG KỲ",
        "Biểu số: tổng hợp định kỳ | Đơn vị báo cáo: Sở Tư pháp",
        "Kỳ báo cáo: Từ ngày 01/01/2026 đến ngày 30/06/2026 | Đơn vị tính: Vụ việc / Đồng",
    ],
    [
        "ỦY BAN NHÂN DÂN TỈNH / THÀNH PHỐ",
        "KẾT QUẢ THỰC HIỆN NHIỆM VỤ CÔNG TÁC TƯ PHÁP",
        "Đơn vị nhận báo cáo: Cục Kế hoạch - Tài chính (Bộ Tư pháp)",
        "Ngày nhận báo cáo: 15/07/2026",
    ],
]

GUIDE_SHEET_TEMPLATES = [
    (
        "Huong dan",
        [
            "HƯỚNG DẪN NHẬP SỐ LIỆU BÁO CÁO THỐNG KÊ",
            "",
            "1. Cán bộ nhập số liệu đúng vào các cột theo mẫu đã ban hành.",
            "2. Không xóa công thức tổng hợp tự động ở dòng Tổng số.",
            "3. Các ô không có số liệu điền 0 hoặc ký hiệu '-'.",
            "4. Kiểm tra kỹ đơn vị tính trước khi gửi báo cáo lên hệ thống eForm.",
            "Lưu ý: Sheet này chỉ dùng để hướng dẫn, không chứa bảng số liệu báo cáo.",
        ],
    ),
    (
        "Thong tin chung",
        [
            "THÔNG TIN CHUNG VỀ KỲ BÁO CÁO",
            "Đơn vị báo cáo: Cơ quan Tư pháp địa phương",
            "Cán bộ phụ trách: Phòng Tổng hợp - Thống kê",
            "Điện thoại liên hệ: 024-3843-xxxx",
            "Ghi chú: Vui lòng chuyển sang sheet kế tiếp để xem bảng số liệu chi tiết.",
        ],
    ),
]

AUX_TABLE_TEMPLATES = [
    (
        ["Phân nhóm bổ sung", "Số lượng", "Tỷ lệ (%)"],
        [
            ["Nhóm đối tượng cấp tỉnh", 12, 40],
            ["Nhóm đối tượng cấp huyện/xã", 18, 60],
            ["Tổng cộng bảng phụ", 30, 100],
        ],
    ),
    (
        ["STT", "Chỉ tiêu đối chiếu bổ sung", "Kỳ trước", "Kỳ này"],
        [
            [1, "Hồ sơ chuyển kỳ trước sang", 45, 52],
            [2, "Hồ sơ tiếp nhận mới trong kỳ", 120, 138],
            [3, "Hồ sơ đã giải quyết xong", 110, 131],
        ],
    ),
]

NOTE_COL_HEADERS = ["Ghi chú nội bộ", "Ghi chú rà soát", "Nhận xét kiểm tra"]
NOTE_COL_VALUES = ["Đã đối chiếu", "Đúng mẫu", "Chờ duyệt", "Khớp kỳ trước", "Cần rà soát"]

THIN_SIDE = Side(style="thin", color="000000")
THIN_BORDER = Border(left=THIN_SIDE, right=THIN_SIDE, top=THIN_SIDE, bottom=THIN_SIDE)
EMPTY_BORDER = Border()

_LABEL_HDR_RE = re.compile(r"\b(chi tieu|noi dung|ten don vi|don vi|co quan|to chuc|loai hinh)\b")
_STT_HDR_RE = re.compile(r"\b(stt|so thu tu|ma so)\b")
_NOTE_HDR_RE = re.compile(r"\b(ghi chu|chu thich)\b")


def _extract_form_code(source_file: str) -> str:
    parts = Path(source_file).stem.split("_")
    if len(parts) >= 4:
        return "_".join(parts[1:4])
    return Path(source_file).stem[:24]


def _detect_col_indices(worksheet: Any, table: dict[str, int]) -> tuple[int | None, int | None, list[int]]:
    """Identify (code_col, label_col, data_cols) in 1-based Excel columns for clean variant synthesis."""
    top, left = table["top"], table["left"]
    bottom, right = table["bottom"], table["right"]
    hb = table["header_bottom"]
    merges = [range_boundaries(str(mr)) for mr in worksheet.merged_cells.ranges]

    hdr_texts: dict[int, str] = {}
    for c in range(left, right + 1):
        parts: list[str] = []
        for r in range(top, hb + 1):
            v = _cell_value(worksheet, r, c)
            if v is None:
                for ml, mt, mr, mb in merges:
                    if ml <= c <= mr and mt <= r <= mb:
                        v = _cell_value(worksheet, mt, ml)
                        break
            t = clean_text(v)
            if t:
                parts.append(t)
        hdr_texts[c] = fold_text(" ".join(parts))

    code_col: int | None = None
    label_col: int | None = None
    note_cols: set[int] = set()

    for c in range(left, right + 1):
        if _NOTE_HDR_RE.search(hdr_texts[c]):
            note_cols.add(c)
        elif code_col is None and c <= left + 2 and _STT_HDR_RE.search(hdr_texts[c]):
            code_col = c

    value_rows = list(range(hb + 1, bottom + 1))

    def label_count(c: int) -> tuple[float, int]:
        filled = 0
        labels = 0
        for r in value_rows:
            v = _cell_value(worksheet, r, c)
            t = clean_text(v)
            if t:
                filled += 1
                if isinstance(v, str) and len(t) >= 3 and sum(ch.isalpha() for ch in t) >= 2:
                    labels += 1
        return (labels / filled if filled else 0.0), labels

    for c in range(left, right + 1):
        if c == code_col or c in note_cols:
            continue
        share, cnt = label_count(c)
        if _LABEL_HDR_RE.search(hdr_texts[c]) and share >= 0.5 and cnt >= 1:
            label_col = c
            break
    if label_col is None and value_rows:
        best: tuple[int, int] | None = None
        for c in range(left, right + 1):
            if c == code_col or c in note_cols:
                continue
            share, cnt = label_count(c)
            if share >= 0.5 and cnt >= max(1, int(len(value_rows) * 0.3)):
                if best is None or cnt > best[1]:
                    best = (c, cnt)
        if best is not None:
            label_col = best[0]

    data_cols = [c for c in range(left, right + 1) if c not in {code_col, label_col} and c not in note_cols]
    return code_col, label_col, data_cols


def _unmerge_all(ws: Any) -> list[tuple[int, int, int, int]]:
    """Safely unmerge every merged cell range without hitting openpyxl KeyError,
    returning the original (left, top, right, bottom) boxes."""
    boxes = [range_boundaries(str(r)) for r in list(ws.merged_cells.ranges)]
    ws.merged_cells.ranges.clear()
    for (r, c), cell in list(ws._cells.items()):
        if isinstance(cell, MergedCell):
            ws._cells.pop((r, c), None)
    return boxes


def _remerge_boxes(ws: Any, boxes: list[tuple[int, int, int, int]]) -> None:
    for ml, mt, mr, mb in boxes:
        if ml <= mr and mt <= mb and (mr > ml or mb > mt):
            ws.merge_cells(start_row=mt, start_column=ml, end_row=mb, end_column=mr)


def _remove_all_borders(ws: Any) -> None:
    for cell in ws._cells.values():
        cell.border = EMPTY_BORDER


def _drop_code_row_if_present(ws: Any, table: dict[str, int]) -> dict[str, int] | None:
    top, left, bottom, right, hb = (
        table["top"], table["left"], table["bottom"], table["right"], table["header_bottom"]
    )
    if hb <= top:
        return None
    hb_vals = [_cell_value(ws, hb, c) for c in range(left, right + 1)]
    if not row_has_code_sequence(hb_vals):
        return None
    old_boxes = _unmerge_all(ws)
    ws.delete_rows(hb, 1)
    # Re-apply non-broken merges with rows below hb shifted up by 1
    shifted_boxes: list[tuple[int, int, int, int]] = []
    for ml, mt, mr, mb in old_boxes:
        if mt <= hb <= mb:
            if mt < hb and mb > hb:
                shifted_boxes.append((ml, mt, mr, mb - 1))
            elif mt < hb and mb == hb:
                shifted_boxes.append((ml, mt, mr, hb - 1))
            # else single-row merge on hb -> dropped
        elif mt > hb:
            shifted_boxes.append((ml, mt - 1, mr, mb - 1))
        else:
            shifted_boxes.append((ml, mt, mr, mb))
    _remerge_boxes(ws, shifted_boxes)
    return {
        "top": top,
        "left": left,
        "bottom": bottom - 1,
        "right": right,
        "header_bottom": hb - 1,
    }


def _convert_numbers_to_text(ws: Any, table: dict[str, int], rng: random.Random) -> bool:
    converted = 0
    for r in range(table["header_bottom"] + 1, table["bottom"] + 1):
        for c in range(table["left"], table["right"] + 1):
            v = ws.cell(r, c).value
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                if float(v).is_integer():
                    text = f"{int(v):,}".replace(",", ".") if rng.random() < 0.7 else str(int(v))
                else:
                    text = f"{v:.2f}".replace(".", ",")
                ws.cell(r, c).value = text
                ws.cell(r, c).number_format = "@"
                converted += 1
    return converted > 0


def _insert_blank_rows(ws: Any, table: dict[str, int], rng: random.Random) -> dict[str, int] | None:
    val_rows = table["bottom"] - table["header_bottom"]
    if val_rows < 2:
        return None
    n_inserts = 1 if val_rows < 6 else rng.choice([1, 2])
    candidates = list(range(table["header_bottom"] + 2, table["bottom"] + 1))
    if not candidates:
        return None
    positions = sorted(rng.sample(candidates, min(n_inserts, len(candidates))), reverse=True)
    boxes = _unmerge_all(ws)
    for pos in positions:
        ws.insert_rows(pos, 1)
        new_boxes = []
        for ml, mt, mr, mb in boxes:
            if mb < pos:
                new_boxes.append((ml, mt, mr, mb))
            elif mt >= pos:
                new_boxes.append((ml, mt + 1, mr, mb + 1))
            # else merge spanned across inserted blank row -> leave unmerged cleanly
        boxes = new_boxes
    _remerge_boxes(ws, boxes)
    return {
        **table,
        "bottom": table["bottom"] + len(positions),
    }


def _append_long_footer(ws: Any, table: dict[str, int], rng: random.Random) -> None:
    lines = rng.choice(FOOTER_TEMPLATES)
    start_row = table["bottom"] + rng.choice([1, 2])
    left = table["left"]
    for idx, line in enumerate(lines):
        cell = ws.cell(start_row + idx, left)
        cell.value = line
        cell.border = EMPTY_BORDER
        if idx >= len(lines) - 2:
            cell.font = Font(bold=True)


def _shift_sheet(ws: Any, tables: list[dict[str, int]], dr: int, dc: int, add_meta: bool, rng: random.Random) -> list[dict[str, int]]:
    old_merges = _unmerge_all(ws)
    if dr > 0:
        ws.insert_rows(1, dr)
    if dc > 0:
        ws.insert_cols(1, dc)
    _remerge_boxes(ws, [(ml + dc, mt + dr, mr + dc, mb + dr) for ml, mt, mr, mb in old_merges])
    if add_meta and dr >= 4:
        meta = rng.choice(METADATA_TEMPLATES)
        for idx, line in enumerate(meta[: dr - 1]):
            c = ws.cell(1 + idx, 1 + dc)
            c.value = line
            c.font = Font(bold=(idx <= 1))
    return [
        {
            "top": t["top"] + dr,
            "left": t["left"] + dc,
            "bottom": t["bottom"] + dr,
            "right": t["right"] + dc,
            "header_bottom": t["header_bottom"] + dr,
        }
        for t in tables
    ]


def _append_note_column(ws: Any, table: dict[str, int], rng: random.Random) -> dict[str, int]:
    nc = table["right"] + 1
    top, hb, bottom = table["top"], table["header_bottom"], table["bottom"]
    hdr_cell = ws.cell(top, nc)
    hdr_cell.value = rng.choice(NOTE_COL_HEADERS)
    hdr_cell.font = Font(bold=True)
    hdr_cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    if hb > top:
        ws.merge_cells(start_row=top, start_column=nc, end_row=hb, end_column=nc)
    ref_border = copy.copy(ws.cell(hb, table["right"]).border) or THIN_BORDER
    for r in range(top, bottom + 1):
        ws.cell(r, nc).border = copy.copy(ref_border)
    for r in range(hb + 1, bottom + 1):
        if rng.random() < 0.30:
            ws.cell(r, nc).value = rng.choice(NOTE_COL_VALUES)
    return {**table, "right": nc}


def _append_second_table(ws: Any, table: dict[str, int], rng: random.Random) -> dict[str, int]:
    headers, body = rng.choice(AUX_TABLE_TEMPLATES)
    max_r, _ = _actual_bounds(ws)
    t2_top = max(table["bottom"] + 3, max_r + 2)
    left = table["left"]
    for c_off, text in enumerate(headers):
        cell = ws.cell(t2_top, left + c_off)
        cell.value = text
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")
        cell.border = THIN_BORDER
    for r_off, row_vals in enumerate(body, 1):
        for c_off, val in enumerate(row_vals):
            cell = ws.cell(t2_top + r_off, left + c_off)
            cell.value = val
            cell.border = THIN_BORDER
    return {
        "top": t2_top,
        "left": left,
        "bottom": t2_top + len(body),
        "right": left + len(headers) - 1,
        "header_bottom": t2_top,
    }


def _select_balanced_seeds(
    base_records: list[dict[str, Any]],
    max_train_seeds: int,
    max_val_seeds: int,
    max_test_id_seeds: int,
    max_test_ood_seeds: int,
    seed: int,
) -> dict[str, list[dict[str, Any]]]:
    """Select balanced, form-diverse single-table seeds per split so rare forms get full
    variant coverage instead of letting 09a (525 files) dominate."""
    rng = random.Random(seed)
    quotas = {
        "train": max_train_seeds,
        "validation": max_val_seeds,
        "test_id": max_test_id_seeds,
        "test_ood": max_test_ood_seeds,
    }
    chosen: dict[str, list[dict[str, Any]]] = {}

    for split, limit in quotas.items():
        pool = [r for r in base_records if r["split"] == split and len(r["tables"]) == 1]
        # Group by (form_code, layout_group) so we sample round-robin across all 28 forms!
        by_form: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
        for rec in pool:
            by_form[_extract_form_code(rec["source_file"])].append(rec)

        # Within each form, prefer multi-row sheets (richer for blank_rows/col_mismatch) and unique layout_groups
        queues: dict[str, list[dict[str, Any]]] = {}
        for form, items in sorted(by_form.items()):
            rng.shuffle(items)
            items.sort(
                key=lambda r: (
                    -(r["tables"][0]["bottom"] - r["tables"][0]["header_bottom"] >= 3),
                    -(min(r["tables"][0]["bottom"] - r["tables"][0]["header_bottom"], 30)),
                )
            )
            # Pick distinct layout_groups first
            seen_lg: set[str] = set()
            first_pass, rest = [], []
            for it in items:
                if it["layout_group"] not in seen_lg:
                    seen_lg.add(it["layout_group"])
                    first_pass.append(it)
                else:
                    rest.append(it)
            queues[form] = first_pass + rest

        selected: list[dict[str, Any]] = []
        form_keys = sorted(queues.keys())
        while len(selected) < limit and form_keys:
            next_keys = []
            for fk in form_keys:
                if queues[fk] and len(selected) < limit:
                    selected.append(queues[fk].pop(0))
                if queues[fk]:
                    next_keys.append(fk)
            form_keys = next_keys
        chosen[split] = selected

    return chosen


def generate_raw_variants(
    module_root: Path,
    *,
    curated_labels: list[dict[str, Any]] | None = None,
    max_train_seeds: int = 85,
    max_val_seeds: int = 14,
    max_test_id_seeds: int = 20,
    max_test_ood_seeds: int = 16,
    seed: int = 20260913,
    clean_existing: bool = True,
    progress: bool = True,
) -> dict[str, Any]:
    """Generate genuine, inspectable .xlsx variant workbooks under Data/Raw_Variants/<split>/
    from diverse Data/Raw seeds, along with exact ground-truth variants_manifest.jsonl."""
    module_root = module_root.resolve()
    out_root = module_root / "Data" / "Raw_Variants"
    if clean_existing and out_root.exists():
        shutil.rmtree(out_root)
    out_root.mkdir(parents=True, exist_ok=True)

    base_records, _ = build_base_records(
        BuildOptions(module_root=module_root, include_raw_variants=False),
        curated_labels=curated_labels,
        progress=progress,
    )
    selected_by_split = _select_balanced_seeds(
        base_records,
        max_train_seeds=max_train_seeds,
        max_val_seeds=max_val_seeds,
        max_test_id_seeds=max_test_id_seeds,
        max_test_ood_seeds=max_test_ood_seeds,
        seed=seed,
    )

    manifest_entries: list[dict[str, Any]] = []
    counts_by_variant: Counter[str] = Counter()
    counts_by_split: Counter[str] = Counter()
    file_count = 0

    for split, seeds in selected_by_split.items():
        split_dir = out_root / split
        split_dir.mkdir(parents=True, exist_ok=True)
        # For train: generate rich coverage (up to 14 variants per seed);
        # For val/test: generate a balanced set across all 14 variant types so eval measures everything cleanly!
        for s_idx, rec in enumerate(seeds):
            rng = random.Random(seed + int(stable_hash([split, rec["sample_id"]], 8), 16))
            src_path = module_root / rec["source_file"]
            form_slug = re.sub(r"[^A-Za-z0-9_-]+", "", _extract_form_code(rec["source_file"]))[:20] or "form"
            short_id = rec["sample_id"][-8:]
            base_table = dict(rec["tables"][0])
            sheet_idx = int(rec["sheet_index"])

            def save_variant(
                variant_type: str,
                mutator: Any,
            ) -> None:
                nonlocal file_count
                wb = load_workbook(src_path, read_only=False, data_only=False, keep_links=False)
                try:
                    ws = wb.worksheets[sheet_idx]
                    out_spec = mutator(wb, ws, dict(base_table))
                    if out_spec is None:
                        return
                    filename = f"{variant_type}__{form_slug}__{short_id}.xlsx"
                    dst_path = split_dir / filename
                    wb.save(dst_path)
                finally:
                    wb.close()

                # Reload once to measure exact final openpyxl sheet_shape after mutation
                wb_check = load_workbook(dst_path, read_only=False, data_only=False, keep_links=False)
                try:
                    rel_path = dst_path.relative_to(module_root).as_posix()
                    file_count += 1
                    for sh_spec in out_spec:
                        s_i = int(sh_spec["sheet_index"])
                        ws_c = wb_check.worksheets[s_i]
                        rows_c, cols_c = _actual_bounds(ws_c)
                        manifest_entries.append({
                            "source_file": rel_path,
                            "parent_source_file": rec["source_file"],
                            "parent_sheet_index": sheet_idx,
                            "split": split,
                            "variant_type": sh_spec.get("variant_type", variant_type),
                            "sheet_index": s_i,
                            "sheet_name": ws_c.title,
                            "sheet_shape": [rows_c, cols_c],
                            "tables": sh_spec["tables"],
                            "col_mismatch_cols": sh_spec.get("col_mismatch_cols", []),
                        })
                        counts_by_variant[sh_spec.get("variant_type", variant_type)] += 1
                        counts_by_split[split] += 1
                finally:
                    wb_check.close()

            # Choose which variants to apply to this seed:
            # Train seeds get 9-12 variants each (rich coverage); eval seeds get 4-6 rotating variants each
            all_variants = [
                "unmerged",
                "borderless",
                "no_code_row",
                "numeric_text",
                "blank_rows",
                "long_footer",
                "shifted_pos",
                "extra_note_col",
                "two_tables",
                "multi_sheet_guide",
                "swapped_cols",
                "col_mismatch",
                "combo_unmerged_borderless_footer",
                "combo_nocode_numtext_shifted",
            ]
            if split == "train":
                chosen_variants = all_variants
            else:
                # Deterministic rotation so every eval split covers all 14 variant types evenly
                per_seed = 6
                offset = (s_idx * per_seed) % len(all_variants)
                chosen_variants = [all_variants[(offset + k) % len(all_variants)] for k in range(per_seed)]

            for v_name in chosen_variants:
                if v_name == "unmerged":
                    def _m_unmerged(wb, ws, tbl):
                        if not ws.merged_cells.ranges:
                            return None
                        _unmerge_all(ws)
                        return [{"sheet_index": sheet_idx, "tables": [tbl]}]
                    save_variant(v_name, _m_unmerged)

                elif v_name == "borderless":
                    def _m_borderless(wb, ws, tbl):
                        _remove_all_borders(ws)
                        return [{"sheet_index": sheet_idx, "tables": [tbl]}]
                    save_variant(v_name, _m_borderless)

                elif v_name == "no_code_row":
                    def _m_no_code(wb, ws, tbl):
                        updated = _drop_code_row_if_present(ws, tbl)
                        if updated is None:
                            return None
                        return [{"sheet_index": sheet_idx, "tables": [updated]}]
                    save_variant(v_name, _m_no_code)

                elif v_name == "numeric_text":
                    def _m_num_text(wb, ws, tbl):
                        if not _convert_numbers_to_text(ws, tbl, rng):
                            return None
                        return [{"sheet_index": sheet_idx, "tables": [tbl]}]
                    save_variant(v_name, _m_num_text)

                elif v_name == "blank_rows":
                    def _m_blank(wb, ws, tbl):
                        updated = _insert_blank_rows(ws, tbl, rng)
                        if updated is None:
                            return None
                        return [{"sheet_index": sheet_idx, "tables": [updated]}]
                    save_variant(v_name, _m_blank)

                elif v_name == "long_footer":
                    def _m_footer(wb, ws, tbl):
                        _append_long_footer(ws, tbl, rng)
                        return [{"sheet_index": sheet_idx, "tables": [tbl]}]
                    save_variant(v_name, _m_footer)

                elif v_name == "shifted_pos":
                    def _m_shift(wb, ws, tbl):
                        dr = rng.randint(3, 8)
                        dc = rng.randint(2, 5)
                        shifted = _shift_sheet(ws, [tbl], dr, dc, add_meta=True, rng=rng)
                        return [{"sheet_index": sheet_idx, "tables": shifted}]
                    save_variant(v_name, _m_shift)

                elif v_name == "extra_note_col":
                    def _m_note_col(wb, ws, tbl):
                        updated = _append_note_column(ws, tbl, rng)
                        return [{"sheet_index": sheet_idx, "tables": [updated]}]
                    save_variant(v_name, _m_note_col)

                elif v_name == "two_tables":
                    def _m_two(wb, ws, tbl):
                        t2 = _append_second_table(ws, tbl, rng)
                        return [{"sheet_index": sheet_idx, "tables": [tbl, t2]}]
                    save_variant(v_name, _m_two)

                elif v_name == "multi_sheet_guide":
                    def _m_guide(wb, ws, tbl):
                        title, lines = rng.choice(GUIDE_SHEET_TEMPLATES)
                        guide = wb.create_sheet(title=title, index=0)
                        for idx, text in enumerate(lines, 1):
                            c = guide.cell(idx, 1)
                            c.value = text
                            if idx == 1:
                                c.font = Font(bold=True)
                        return [
                            {"sheet_index": 0, "tables": [], "variant_type": "no_table_guide_sheet"},
                            {"sheet_index": sheet_idx + 1, "tables": [tbl], "variant_type": "multi_sheet_data"},
                        ]
                    save_variant(v_name, _m_guide)

                elif v_name == "swapped_cols":
                    def _m_swap(wb, ws, tbl):
                        _, _, data_cols = _detect_col_indices(ws, tbl)
                        if len(data_cols) < 2:
                            return None
                        c1, c2 = data_cols[-2], data_cols[-1]
                        boxes = _unmerge_all(ws)
                        kept_boxes = [
                            (ml, mt, mr, mb) for ml, mt, mr, mb in boxes
                            if not ((ml <= c1 <= mr) or (ml <= c2 <= mr))
                        ]
                        for r in range(tbl["top"], tbl["bottom"] + 1):
                            v1, v2 = ws.cell(r, c1).value, ws.cell(r, c2).value
                            ws.cell(r, c1).value, ws.cell(r, c2).value = v2, v1
                        _remerge_boxes(ws, kept_boxes)
                        return [{"sheet_index": sheet_idx, "tables": [tbl]}]
                    save_variant(v_name, _m_swap)

                elif v_name == "col_mismatch":
                    def _m_mismatch(wb, ws, tbl):
                        if tbl["bottom"] - tbl["header_bottom"] < 2:
                            return None
                        _, label_col, data_cols = _detect_col_indices(ws, tbl)
                        if label_col is None or not data_cols:
                            return None
                        target_c = data_cols[-1]
                        for r in range(tbl["header_bottom"] + 1, tbl["bottom"] + 1):
                            v1, v2 = ws.cell(r, label_col).value, ws.cell(r, target_c).value
                            ws.cell(r, label_col).value, ws.cell(r, target_c).value = v2, v1
                        return [{
                            "sheet_index": sheet_idx,
                            "tables": [tbl],
                            "col_mismatch_cols": [label_col, target_c],
                        }]
                    save_variant(v_name, _m_mismatch)

                elif v_name == "combo_unmerged_borderless_footer":
                    def _m_combo1(wb, ws, tbl):
                        _unmerge_all(ws)
                        _remove_all_borders(ws)
                        _append_long_footer(ws, tbl, rng)
                        dr = rng.randint(2, 5)
                        dc = rng.randint(1, 3)
                        shifted = _shift_sheet(ws, [tbl], dr, dc, add_meta=False, rng=rng)
                        return [{"sheet_index": sheet_idx, "tables": shifted}]
                    save_variant(v_name, _m_combo1)

                elif v_name == "combo_nocode_numtext_shifted":
                    def _m_combo2(wb, ws, tbl):
                        updated = _drop_code_row_if_present(ws, tbl)
                        if updated is None:
                            return None
                        _convert_numbers_to_text(ws, updated, rng)
                        _unmerge_all(ws)
                        dr = rng.randint(2, 6)
                        dc = rng.randint(1, 4)
                        shifted = _shift_sheet(ws, [updated], dr, dc, add_meta=True, rng=rng)
                        return [{"sheet_index": sheet_idx, "tables": shifted}]
                    save_variant(v_name, _m_combo2)

            if progress and ((s_idx + 1) % 20 == 0 or (s_idx + 1) == len(seeds)):
                print(f"  [{split}] Đã sinh biến thể từ {s_idx + 1}/{len(seeds)} workbook hạt giống ({file_count} file .xlsx)...")

    manifest_path = out_root / "variants_manifest.jsonl"
    jsonl = "".join(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n" for item in manifest_entries)
    _write_atomic(manifest_path, jsonl)

    summary = {
        "output_dir": str(out_root),
        "manifest_file": str(manifest_path),
        "generated_workbook_files": file_count,
        "generated_sheet_records": len(manifest_entries),
        "seeds_used_per_split": {k: len(v) for k, v in selected_by_split.items()},
        "records_per_split": dict(sorted(counts_by_split.items())),
        "records_per_variant": dict(sorted(counts_by_variant.items())),
    }
    if progress:
        print(f"Hoàn tất sinh biến thể: {file_count} file .xlsx ({len(manifest_entries)} sheet) -> {out_root}")
    return summary


if __name__ == "__main__":
    summary = generate_raw_variants(MODULE_ROOT_DEFAULT, progress=True)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
