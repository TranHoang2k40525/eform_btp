from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from openpyxl import load_workbook

MODULE_ROOT = Path(__file__).resolve().parents[1]
API_ROOT = MODULE_ROOT / "API"
MODEL_PATH = API_ROOT / "models" / "eform_excel_table_extractor_v2.eformmodel"

if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))


def test_api_does_not_import_training_code() -> None:
    """Verify FastAPI loads the TorchScript model without importing Train/ or plotting libs."""
    before = set(sys.modules.keys())
    import main as api_main  # noqa: F401

    newly_loaded = set(sys.modules.keys()) - before
    for forbidden in ("training_core", "train", "augmentations", "dataset_cache", "model", "matplotlib"):
        assert forbidden not in newly_loaded, f"API unexpectedly imported training module: {forbidden}"
    train_dir = str((MODULE_ROOT / "Train").resolve()).lower()
    for mod_name in newly_loaded:
        mod = sys.modules.get(mod_name)
        mod_file = getattr(mod, "__file__", None) or ""
        assert not mod_file.lower().startswith(train_dir), f"API imported module from Train/: {mod_name}"


def test_fastapi_endpoints_schema_and_guardrails(monkeypatch: pytest.MonkeyPatch) -> None:
    assert MODEL_PATH.is_file(), f"Missing deployed model: {MODEL_PATH}"
    monkeypatch.setenv("EFORM_MODEL_PATH", str(MODEL_PATH))

    import main as api_main

    dataset_path = MODULE_ROOT / "Data" / "dataset.jsonl"
    records = [
        json.loads(line)
        for line in dataset_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    sample = next(
        r for r in records
        if r["split"] == "test_id" and len(r["tables"]) == 1
        and (r["tables"][0]["bottom"] - r["tables"][0]["header_bottom"]) >= 3
    )
    excel_file = MODULE_ROOT / sample["source_file"]

    with TestClient(api_main.app) as client:
        # 1. Health check
        health = client.get("/health")
        assert health.status_code == 200
        h_json = health.json()
        assert h_json["status"] == "ready"
        assert h_json["model"]["format"] == "eformmodel-2.0"
        assert h_json["model"]["artifact"] == MODEL_PATH.name

        # 2. Model info
        info = client.get("/api/eform/model")
        assert info.status_code == 200
        assert info.json()["format"] == "eformmodel-2.0"

        # 3. Extract valid unseen Excel workbook
        with excel_file.open("rb") as fh:
            resp = client.post(
                "/api/eform/extract",
                files={"file": (excel_file.name, fh, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                data={"originalFileName": excel_file.name},
            )
        assert resp.status_code == 200, resp.text
        payload = resp.json()
        assert payload["schemaVersion"] == "2.0"
        assert payload["modelFormat"] == "eformmodel-2.0"
        assert payload["summary"]["tableCount"] >= 1
        table = payload["sheets"][sample["sheet_index"]]["tables"][0]
        assert table["postprocessing"] == "neural-direct-v2"
        assert table["rowCount"] >= 2
        assert table["columnCount"] >= 2
        assert len(table["data"]) == table["rowCount"]
        assert len(table["columns"]) == table["columnCount"]
        assert table["columnIssues"] == []

        # 4. Verify learned column-mismatch blocks bad file (11b File-B style)
        label_col = table["labelColumnIndex"]
        if label_col is not None and table["columnCount"] >= 4:
            t = sample["tables"][0]
            with tempfile.TemporaryDirectory() as td:
                bad_path = Path(td) / "mismatch.xlsx"
                wb = load_workbook(excel_file, data_only=False)
                ws = wb.worksheets[sample["sheet_index"]]
                src_c = t["left"] + label_col
                dst_c = t["right"]
                if dst_c == src_c:
                    dst_c = t["right"] - 1
                for r in range(t["header_bottom"] + 1, t["bottom"] + 1):
                    v1, v2 = ws.cell(r, src_c).value, ws.cell(r, dst_c).value
                    ws.cell(r, src_c).value, ws.cell(r, dst_c).value = v2, v1
                wb.save(bad_path)
                wb.close()
                with bad_path.open("rb") as fh:
                    bad_resp = client.post(
                        "/api/eform/extract",
                        files={"file": ("mismatch.xlsx", fh, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                    )
                assert bad_resp.status_code == 200
                bad_json = bad_resp.json()
                assert bad_json["requiresReview"] is True
                assert bad_json["summary"]["columnIssueCount"] >= 1

        # 5. Reject invalid extension (415)
        bad_ext = client.post(
            "/api/eform/extract",
            files={"file": ("bad.csv", b"a,b\n1,2\n", "text/csv")},
        )
        assert bad_ext.status_code == 415

        # 6. Reject empty file (400)
        empty = client.post(
            "/api/eform/extract",
            files={"file": ("empty.xlsx", b"", "application/octet-stream")},
        )
        assert empty.status_code == 400

        # 7. Reject corrupted zip (422)
        bad_zip = client.post(
            "/api/eform/extract",
            files={"file": ("corrupt.xlsx", b"not-a-zip-file", "application/octet-stream")},
        )
        assert bad_zip.status_code == 422
