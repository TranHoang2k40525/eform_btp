from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _flag(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    upload_dir: Path = Path(os.getenv("AI_IMPORT_UPLOAD_DIR", "./runtime/uploads")).resolve()
    max_file_bytes: int = int(os.getenv("AI_IMPORT_MAX_FILE_BYTES", 25 * 1024 * 1024))
    max_uncompressed_bytes: int = int(os.getenv("AI_IMPORT_MAX_UNCOMPRESSED_BYTES", 200 * 1024 * 1024))
    max_zip_ratio: int = int(os.getenv("AI_IMPORT_MAX_ZIP_RATIO", 100))
    max_rows: int = int(os.getenv("AI_IMPORT_MAX_ROWS", 50_000))
    max_columns: int = int(os.getenv("AI_IMPORT_MAX_COLUMNS", 500))
    embedding_enabled: bool = _flag("AI_IMPORT_EMBEDDING_ENABLED")
    embedding_model: str = os.getenv("AI_IMPORT_EMBEDDING_MODEL", "intfloat/multilingual-e5-base")
    embedding_cache_dir: str | None = os.getenv("AI_IMPORT_MODEL_CACHE")
    llm_enabled: bool = _flag("AI_IMPORT_LLM_ENABLED")
    llm_base_url: str = os.getenv("AI_IMPORT_LLM_BASE_URL", "http://127.0.0.1:8001/v1")
    llm_model: str = os.getenv("AI_IMPORT_LLM_MODEL", "Qwen/Qwen3-8B")
    auto_accept_threshold: float = float(os.getenv("AI_IMPORT_AUTO_ACCEPT_THRESHOLD", "0.88"))
    review_threshold: float = float(os.getenv("AI_IMPORT_REVIEW_THRESHOLD", "0.62"))


settings = Settings()

