from __future__ import annotations

import argparse
import json
import tempfile
import time
from dataclasses import replace
from pathlib import Path

from openpyxl import Workbook

from ai_import.config import settings
from ai_import.models import MapRequest, TargetFieldDto, ValidateRequest
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
            service = ImportAiService(replace(settings, enforce_upload_root=False))
            analysis = service.analyze(str(path), preview_rows=100)
            region = next((region for sheet in analysis.sheets for region in sheet.regions), None)
            mapping_ms = validation_ms = 0.0
            if region:
                target_fields = [TargetFieldDto(field_id=f"field_{index}", label=header)
                                 for index, header in enumerate(region.headers)]
                map_started = time.perf_counter()
                mapped = service.map(MapRequest(headers=region.headers, target_fields=target_fields,
                                                sample_rows=region.rows[:10]))
                mapping_ms = (time.perf_counter() - map_started) * 1000
                validation_started = time.perf_counter()
                service.validate(ValidateRequest(headers=region.headers, rows=region.rows,
                                                 mappings=mapped.mappings, target_fields=target_fields))
                validation_ms = (time.perf_counter() - validation_started) * 1000
            elapsed = (time.perf_counter() - started) * 1000
            results.append({"rows": count, "sheets": args.sheets, "total_ms": round(elapsed, 2),
                            "service_elapsed_ms": analysis.elapsed_ms,
                            "security_ms": analysis.timings_ms.get("security", 0),
                            "parse_ms": analysis.timings_ms.get("parse", 0),
                            "table_detection_ms": analysis.timings_ms.get("table_detection", 0),
                            "mapping_ms": round(mapping_ms, 2),
                            "inference_ms": None if settings.embedding_enabled else 0.0,
                            "validation_ms": round(validation_ms, 2),
                            "regions": sum(len(sheet.regions) for sheet in analysis.sheets)})
    Path(args.output).write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
