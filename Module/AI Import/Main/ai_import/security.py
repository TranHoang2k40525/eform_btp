from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

from .config import Settings


ALLOWED_EXTENSIONS = {".xlsx", ".xlsm"}


class UnsafeWorkbookError(ValueError):
    pass


def validate_workbook_path(raw_path: str, config: Settings) -> tuple[Path, str]:
    path = Path(raw_path).expanduser().resolve(strict=True)
    if not path.is_file():
        raise UnsafeWorkbookError("Đường dẫn không phải là tệp.")
    if path.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise UnsafeWorkbookError("Chỉ hỗ trợ .xlsx và .xlsm; .xls cần được chuyển đổi trước.")
    size = path.stat().st_size
    if size <= 0 or size > config.max_file_bytes:
        raise UnsafeWorkbookError(f"Kích thước tệp không hợp lệ hoặc vượt {config.max_file_bytes} byte.")
    with path.open("rb") as stream:
        signature = stream.read(4)
    if signature != b"PK\x03\x04":
        raise UnsafeWorkbookError("Chữ ký tệp không phải Office Open XML.")
    total = 0
    with zipfile.ZipFile(path, "r") as archive:
        for info in archive.infolist():
            total += info.file_size
            if info.compress_size == 0 and info.file_size > 0:
                raise UnsafeWorkbookError("Phát hiện ZIP entry bất thường.")
            if info.compress_size and info.file_size / info.compress_size > config.max_zip_ratio:
                raise UnsafeWorkbookError("Tệp có tỷ lệ nén bất thường (nguy cơ zip bomb).")
        if total > config.max_uncompressed_bytes:
            raise UnsafeWorkbookError("Dung lượng giải nén vượt giới hạn.")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return path, digest.hexdigest()

