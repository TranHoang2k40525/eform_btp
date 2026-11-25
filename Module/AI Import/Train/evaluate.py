from __future__ import annotations

import argparse
import copy
import json
import sys
import tempfile
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

TRAIN_DIR = Path(__file__).resolve().parent
MODULE_DIR = TRAIN_DIR.parent
if str(MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_DIR))
if str(TRAIN_DIR) not in sys.path:
    sys.path.insert(0, str(TRAIN_DIR))

from openpyxl import load_workbook
from openpyxl.styles import Border, Font
from openpyxl.utils.cell import range_boundaries

from dataset_cache import build_or_load_cache
from eform_ai.encoder import row_has_code_sequence
from eform_ai.predictor import EFormPredictor
from eform_ai.schema import COL_DATA, COL_LABEL, MODEL_FILENAME


def _clone_wb(path: Path, dst: Path) -> Any:
    wb = load_workbook(path, read_only=False, data_only=False, keep_links=False)
    wb.save(dst)
    wb.close()
    return load_workbook(dst, read_only=False, data_only=False, keep_links=False)


def _select_unseen_test_samples(cache: dict[str, Any], max_samples: int = 12) -> list[dict[str, Any]]:
    """Pick diverse UNSEEN sheets from test_id & test_ood (different layout groups, single table)."""
    candidates = [
        s for s in cache["samples"]
        if s["split"] in {"test_id", "test_ood"}
        and s.get("variant_type", "original") == "original"
        and len(s["tables"]) == 1
    ]
    # Prefer sheets with at least 2 value rows and diverse layout groups
    by_lg: dict[str, dict[str, Any]] = {}
    for s in sorted(candidates, key=lambda x: -(x["tables"][0]["bottom"] - x["tables"][0]["header_bottom"])):
        lg = s["layout_group"]
        if lg not in by_lg:
            by_lg[lg] = s
    selected = list(by_lg.values())[:max_samples]
    return selected


def _make_variant_workbooks(
    module_root: Path, sample: dict[str, Any], tmp_dir: Path
) -> list[tuple[str, Path, dict[str, Any]]]:
    """Generate 13 realistic Excel perturbations on an UNSEEN test workbook."""
    src = module_root / sample["source_file"]
    t = dict(sample["tables"][0])
    top, left, bottom, right, hb = t["top"], t["left"], t["bottom"], t["right"], t["header_bottom"]
    col_role = sample["col_role"].tolist()
    val_rows = bottom - hb
    variants: list[tuple[str, Path, dict[str, Any]]] = []

    # 1. Original
    variants.append(("01_original", src, {"tables": [t], "expect_issue": False, "expect_note": False}))

    # 2. Unmerge all ("Bỏ ô gộp")
    p = tmp_dir / "v02_unmerged.xlsx"
    wb = _clone_wb(src, p)
    ws = wb.worksheets[sample["sheet_index"]]
    for rng_str in [str(r) for r in list(ws.merged_cells.ranges)]:
        ws.unmerge_cells(rng_str)
    wb.save(p)
    wb.close()
    variants.append(("02_unmerged", p, {"tables": [t], "expect_issue": False, "expect_note": False}))

    # 3. Borderless ("Không kẻ khung")
    p = tmp_dir / "v03_borderless.xlsx"
    wb = _clone_wb(src, p)
    ws = wb.worksheets[sample["sheet_index"]]
    empty_border = Border()
    for cell in ws._cells.values():
        cell.border = empty_border
    wb.save(p)
    wb.close()
    variants.append(("03_borderless", p, {"tables": [t], "expect_issue": False, "expect_note": False}))

    # 4. Drop code row ("Không có dòng số thứ tự cột")
    p = tmp_dir / "v04_no_code_row.xlsx"
    wb = _clone_wb(src, p)
    ws = wb.worksheets[sample["sheet_index"]]
    hb_vals = [ws.cell(hb, c).value for c in range(left, right + 1)]
    if hb > top and row_has_code_sequence(hb_vals):
        # Unmerge ranges touching hb before deleting row
        for rng_str in [str(r) for r in list(ws.merged_cells.ranges)]:
            ml, mt, mr, mb = range_boundaries(rng_str)
            if mt <= hb <= mb:
                ws.unmerge_cells(rng_str)
        ws.delete_rows(hb, 1)
        wb.save(p)
        wb.close()
        variants.append((
            "04_no_code_row",
            p,
            {
                "tables": [{"top": top, "left": left, "bottom": bottom - 1, "right": right, "header_bottom": hb - 1}],
                "expect_issue": False,
                "expect_note": False,
            },
        ))
    else:
        wb.close()

    # 5. Numbers stored as strings ("Số dạng chữ")
    p = tmp_dir / "v05_numeric_text.xlsx"
    wb = _clone_wb(src, p)
    ws = wb.worksheets[sample["sheet_index"]]
    for r in range(hb + 1, bottom + 1):
        for c in range(left, right + 1):
            v = ws.cell(r, c).value
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                ws.cell(r, c).value = f"{int(v):,}".replace(",", ".") if float(v).is_integer() else str(v).replace(".", ",")
    wb.save(p)
    wb.close()
    variants.append(("05_numeric_text", p, {"tables": [t], "expect_issue": False, "expect_note": False}))

    # 6. Interleaved blank row ("Dòng trống xen kẽ")
    if val_rows >= 2:
        p = tmp_dir / "v06_blank_row.xlsx"
        wb = _clone_wb(src, p)
        ws = wb.worksheets[sample["sheet_index"]]
        ins = hb + 2
        ws.insert_rows(ins, 1)
        wb.save(p)
        wb.close()
        variants.append((
            "06_blank_row",
            p,
            {
                "tables": [{"top": top, "left": left, "bottom": bottom + 1, "right": right, "header_bottom": hb}],
                "expect_issue": False,
                "expect_note": False,
            },
        ))

    # 7. Long footer ("Chân trang dài")
    p = tmp_dir / "v07_long_footer.xlsx"
    wb = _clone_wb(src, p)
    ws = wb.worksheets[sample["sheet_index"]]
    base_r = bottom + 1
    notes = [
        'Ô có dấu "-" không phải báo cáo.',
        "- Cột (1), (2) tổng hợp theo số liệu thực tế trong kỳ.",
        "- Số liệu đã được đối chiếu với cơ quan chủ quản.",
        "* Ghi chú: Báo cáo gửi trước ngày 15 hàng tháng.",
        "Người lập biểu (Ký, ghi rõ họ tên)",
        "THỦ TRƯỞNG ĐƠN VỊ (Ký, đóng dấu)",
    ]
    for idx, line in enumerate(notes):
        ws.cell(base_r + idx, left).value = line
    wb.save(p)
    wb.close()
    variants.append(("07_long_footer", p, {"tables": [t], "expect_issue": False, "expect_note": False}))

    # 8. Shifted position to C6 ("Dịch vị trí")
    p = tmp_dir / "v08_shifted_C6.xlsx"
    wb = _clone_wb(src, p)
    ws = wb.worksheets[sample["sheet_index"]]
    dr, dc = 5, 2
    old_merges = [range_boundaries(str(r)) for r in list(ws.merged_cells.ranges)]
    for rng_str in [str(r) for r in list(ws.merged_cells.ranges)]:
        ws.unmerge_cells(rng_str)
    ws.insert_rows(1, dr)
    ws.insert_cols(1, dc)
    for ml, mt, mr, mb in old_merges:
        ws.merge_cells(start_row=mt + dr, start_column=ml + dc, end_row=mb + dr, end_column=mr + dc)
    wb.save(p)
    wb.close()
    variants.append((
        "08_shifted_C6",
        p,
        {
            "tables": [{
                "top": top + dr,
                "left": left + dc,
                "bottom": bottom + dr,
                "right": right + dc,
                "header_bottom": hb + dr,
            }],
            "expect_issue": False,
            "expect_note": False,
        },
    ))

    # 9. Extra note column on right ("Thêm cột ghi chú")
    p = tmp_dir / "v09_extra_note_col.xlsx"
    wb = _clone_wb(src, p)
    ws = wb.worksheets[sample["sheet_index"]]
    nc = right + 1
    ws.cell(top, nc).value = "Ghi chú nội bộ"
    ws.cell(top, nc).font = Font(bold=True)
    for r in range(top, bottom + 1):
        ws.cell(r, nc).border = copy.copy(ws.cell(r, right).border)
    if val_rows >= 1:
        ws.cell(hb + 1, nc).value = "Đã kiểm tra"
    wb.save(p)
    wb.close()
    variants.append((
        "09_extra_note_col",
        p,
        {
            "tables": [{"top": top, "left": left, "bottom": bottom, "right": right + 1, "header_bottom": hb}],
            "expect_issue": False,
            "expect_note": False,
        },
    ))

    # 10. Two stacked tables ("Hai bảng")
    p = tmp_dir / "v10_two_tables.xlsx"
    wb = _clone_wb(src, p)
    ws = wb.worksheets[sample["sheet_index"]]
    t2_top = max(bottom + 4, ws.max_row + 3)
    ws.cell(t2_top, left).value = "Chỉ tiêu phụ"
    ws.cell(t2_top, left + 1).value = "Số lượng"
    ws.cell(t2_top, left + 2).value = "Tỷ lệ"
    for c in range(left, left + 3):
        ws.cell(t2_top, c).font = Font(bold=True)
        ws.cell(t2_top, c).border = copy.copy(ws.cell(hb, left).border)
    for i in range(1, 4):
        ws.cell(t2_top + i, left).value = f"Nội dung phụ {i}"
        ws.cell(t2_top + i, left + 1).value = i * 10
        ws.cell(t2_top + i, left + 2).value = i * 5
        for c in range(left, left + 3):
            ws.cell(t2_top + i, c).border = copy.copy(ws.cell(hb, left).border)
    wb.save(p)
    wb.close()
    variants.append((
        "10_two_tables",
        p,
        {
            "tables": [
                t,
                {"top": t2_top, "left": left, "bottom": t2_top + 3, "right": left + 2, "header_bottom": t2_top},
            ],
            "expect_issue": False,
            "expect_note": False,
        },
    ))

    # 11. Multi-sheet with leading instruction sheet ("Nhiều sheet")
    p = tmp_dir / "v11_multi_sheet.xlsx"
    wb = _clone_wb(src, p)
    guide = wb.create_sheet(title="Huong dan", index=0)
    guide.cell(1, 1).value = "HƯỚNG DẪN NHẬP BÁO CÁO THỐNG KÊ"
    guide.cell(3, 1).value = "1. Điền đầy đủ số liệu vào các ô theo biểu mẫu."
    guide.cell(4, 1).value = "2. Không thay đổi cấu trúc cột."
    guide.cell(5, 1).value = "3. Kiểm tra lại tổng số trước khi nộp."
    wb.save(p)
    wb.close()
    variants.append((
        "11_multi_sheet",
        p,
        {"tables": [t], "target_sheet_index": sample["sheet_index"] + 1, "guide_sheet_index": 0},
    ))

    # 12. Swapped adjacent data columns ("Đảo cột" - header + code + body move together)
    data_cols = [c + 1 for c, r in enumerate(col_role) if r == COL_DATA and left <= c + 1 <= right]
    if len(data_cols) >= 2:
        c1, c2 = data_cols[-2], data_cols[-1]
        p = tmp_dir / "v12_swapped_cols.xlsx"
        wb = _clone_wb(src, p)
        ws = wb.worksheets[sample["sheet_index"]]
        # Unmerge ranges touching c1 or c2 so swap is clean
        for rng_str in [str(r) for r in list(ws.merged_cells.ranges)]:
            ml, mt, mr, mb = range_boundaries(rng_str)
            if (ml <= c1 <= mr) or (ml <= c2 <= mr):
                ws.unmerge_cells(rng_str)
        for r in range(top, bottom + 1):
            v1, v2 = ws.cell(r, c1).value, ws.cell(r, c2).value
            ws.cell(r, c1).value, ws.cell(r, c2).value = v2, v1
        wb.save(p)
        wb.close()
        variants.append(("12_swapped_cols", p, {"tables": [t], "expect_issue": False, "expect_note": True}))

    # 13. Body-only column mismatch (File B of 11b: row labels moved under a data column!)
    label_cols = [c + 1 for c, r in enumerate(col_role) if r == COL_LABEL and left <= c + 1 <= right]
    if label_cols and data_cols and val_rows >= 2:
        lc = label_cols[0]
        dc = data_cols[-1]
        p = tmp_dir / "v13_col_mismatch_11b.xlsx"
        wb = _clone_wb(src, p)
        ws = wb.worksheets[sample["sheet_index"]]
        for r in range(hb + 1, bottom + 1):
            v1, v2 = ws.cell(r, lc).value, ws.cell(r, dc).value
            ws.cell(r, lc).value, ws.cell(r, dc).value = v2, v1
        wb.save(p)
        wb.close()
        variants.append(("13_col_mismatch_11b", p, {"tables": [t], "expect_issue": True, "expect_note": False}))

    return variants


def _box_iou(a: dict[str, int], b: dict[str, int]) -> float:
    it = max(a["top"], b["top"])
    il = max(a["left"], b["left"])
    ib = min(a["bottom"], b["bottom"])
    ir = min(a["right"], b["right"])
    inter = max(0, ib - it + 1) * max(0, ir - il + 1)
    a1 = (a["bottom"] - a["top"] + 1) * (a["right"] - a["left"] + 1)
    a2 = (b["bottom"] - b["top"] + 1) * (b["right"] - b["left"] + 1)
    return inter / max(1, a1 + a2 - inter)


def _range_to_box(source_range: str, header_rows: int) -> dict[str, int]:
    left, top, right, bottom = range_boundaries(source_range)
    return {
        "top": top,
        "left": left,
        "bottom": bottom,
        "right": right,
        "header_bottom": top + header_rows - 1,
    }


def run_stress_evaluation(
    module_root: Path,
    model_path: Path,
    max_workbooks: int = 10,
) -> dict[str, Any]:
    cache = build_or_load_cache(module_root)
    predictor = EFormPredictor(model_path, device_name="cpu")
    selected = _select_unseen_test_samples(cache, max_samples=max_workbooks)

    per_variant: defaultdict[str, dict[str, Any]] = defaultdict(
        lambda: {"total": 0, "passed": 0, "box_ious": [], "exact_region": 0, "failures": []}
    )
    latencies_ms: list[float] = []

    with tempfile.TemporaryDirectory(prefix="eform-stress-") as tmp_root:
        for s_idx, sample in enumerate(selected):
            sub_dir = Path(tmp_root) / f"s{s_idx:02d}"
            sub_dir.mkdir(parents=True, exist_ok=True)
            variants = _make_variant_workbooks(module_root, sample, sub_dir)

            for v_name, wb_path, spec in variants:
                t0 = time.perf_counter()
                result = predictor.predict(wb_path)
                latencies_ms.append((time.perf_counter() - t0) * 1000.0)

                sheet_idx = spec.get("target_sheet_index", sample["sheet_index"])
                sheet_tables = result["sheets"][sheet_idx]["tables"]
                pred_boxes = [_range_to_box(tbl["sourceRange"], tbl["headerRows"]) for tbl in sheet_tables]
                gold_tables = spec["tables"]

                stats = per_variant[v_name]
                stats["total"] += 1

                # Match primary table (and secondary if two_tables)
                if not pred_boxes:
                    best_iou = 0.0
                    exact = False
                else:
                    best_iou = _box_iou(pred_boxes[0], gold_tables[0])
                    exact = all(
                        pred_boxes[0][k] == gold_tables[0][k]
                        for k in ("top", "left", "bottom", "right", "header_bottom")
                    )

                passed = best_iou >= 0.90
                if v_name == "10_two_tables":
                    passed = len(pred_boxes) >= 2 and best_iou >= 0.90
                elif v_name == "11_multi_sheet":
                    guide_tables = result["sheets"][spec["guide_sheet_index"]]["tables"]
                    passed = best_iou >= 0.90 and len(guide_tables) == 0
                elif v_name == "12_swapped_cols":
                    has_note = bool(sheet_tables and sheet_tables[0].get("columnNotes"))
                    passed = best_iou >= 0.90 and has_note
                elif v_name == "13_col_mismatch_11b":
                    has_issue = bool(sheet_tables and sheet_tables[0].get("columnIssues"))
                    passed = best_iou >= 0.90 and has_issue

                stats["box_ious"].append(best_iou)
                if exact:
                    stats["exact_region"] += 1
                if passed:
                    stats["passed"] += 1
                else:
                    stats["failures"].append({
                        "file": sample["source_file"],
                        "expected": gold_tables,
                        "predicted": pred_boxes,
                        "issues": sheet_tables[0]["columnIssues"] if sheet_tables else [],
                        "notes": sheet_tables[0]["columnNotes"] if sheet_tables else [],
                        "guide_tables": (
                            len(result["sheets"][spec["guide_sheet_index"]]["tables"])
                            if "guide_sheet_index" in spec else None
                        ),
                    })

    summary: dict[str, Any] = {
        "model": predictor.model_info,
        "unseen_workbooks_tested": len(selected),
        "avg_latency_ms": round(sum(latencies_ms) / max(1, len(latencies_ms)), 1),
        "variants": {},
        "total_cases": 0,
        "total_passed": 0,
    }
    for v_name in sorted(per_variant):
        s = per_variant[v_name]
        summary["total_cases"] += s["total"]
        summary["total_passed"] += s["passed"]
        summary["variants"][v_name] = {
            "passed": f"{s['passed']}/{s['total']}",
            "avg_box_iou": round(sum(s["box_ious"]) / max(1, len(s["box_ious"])), 4),
            "exact_region": f"{s['exact_region']}/{s['total']}",
            "failure_samples": s["failures"][:2],
        }

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stress-test TorchScript model on unseen 13-variant benchmark")
    parser.add_argument("--module-root", type=Path, default=MODULE_DIR)
    parser.add_argument("--model-path", type=Path, default=TRAIN_DIR / "Output_Local" / MODEL_FILENAME)
    parser.add_argument("--max-workbooks", type=int, default=10)
    args = parser.parse_args()
    run_stress_evaluation(args.module_root, args.model_path, args.max_workbooks)
