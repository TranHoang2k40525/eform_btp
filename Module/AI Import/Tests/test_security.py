from pathlib import Path

import pytest

from ai_import.config import Settings
from ai_import.security import UnsafeWorkbookError, validate_workbook_path


def test_rejects_non_office_signature(tmp_path: Path):
    path = tmp_path / "gia.xlsx"
    path.write_bytes(b"not an excel file")
    with pytest.raises(UnsafeWorkbookError):
        validate_workbook_path(str(path), Settings())


def test_rejects_legacy_xls(tmp_path: Path):
    path = tmp_path / "cu.xls"
    path.write_bytes(b"legacy")
    with pytest.raises(UnsafeWorkbookError):
        validate_workbook_path(str(path), Settings())

