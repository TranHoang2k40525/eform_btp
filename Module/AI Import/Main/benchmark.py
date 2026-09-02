from __future__ import annotations

import argparse
import json
import tempfile
import time
from pathlib import Path

from openpyxl import Workbook

from ai_import.config import settings
from ai_import.service import ImportAiService


def create_workbook(path: Path, rows: int, sheets: int = 1) -> None:
    workbook = Workbook(write_only=False)
    for index in range(sheets):
        sheet = workbook.active if index == 0 else workbook.create_sheet()
        sheet.title = f"Bieu {index + 1}"
        sheet.append(["STT", "Tên đơn vị", "Năm báo cáo", "Tổng số", "Ghi chú"])
        for row in range(rows):
            sheet.append([row + 1, f"Đơn vị {row + 1}", 2026, row * 2, ""])
    workbook.save(path)
    workbook.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, nargs="+", default=[100, 1000, 10000])
    parser.add_argument("--sheets", type=int, default=1)
    parser.add_argument("--output", default="benchmark-result.json")
    args = parser.parse_args()
    results = []
    with tempfile.TemporaryDirectory(prefix="eform-benchmark-") as directory:
        for count in args.rows:
            path = Path(directory) / f"benchmark-{count}.xlsx"
            create_workbook(path, count, args.sheets)
            started = time.perf_counter()
            analysis = ImportAiService(settings).analyze(str(path), preview_rows=100)
            elapsed = (time.perf_counter() - started) * 1000
            results.append({"rows": count, "sheets": args.sheets, "total_ms": round(elapsed, 2),
                            "service_elapsed_ms": analysis.elapsed_ms,
                            "regions": sum(len(sheet.regions) for sheet in analysis.sheets)})
    Path(args.output).write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

