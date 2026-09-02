from __future__ import annotations

import hashlib
import json
import random
import re
from pathlib import Path
from typing import Iterable


EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE = re.compile(r"(?<!\d)(?:\+?84|0)\d{8,10}(?!\d)")
ACCOUNT = re.compile(r"(?i)(api[_ -]?key|token|password|secret)\s*[:=]\s*\S+")


def set_seed(seed: int) -> None:
    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass


def scrub(text: str) -> str:
    text = EMAIL.sub("[EMAIL]", text)
    text = PHONE.sub("[PHONE]", text)
    return ACCOUNT.sub("[SECRET_REMOVED]", text)


def read_jsonl(paths: Iterable[Path]) -> list[dict]:
    records: list[dict] = []
    for path in paths:
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                record = json.loads(line)
                for key in ("source", "target_id", "target_text"):
                    if key not in record:
                        raise ValueError(f"{path}:{line_number} thiếu trường {key}")
                record["source"] = scrub(str(record["source"]))
                record["target_text"] = scrub(str(record["target_text"]))
                records.append(record)
    return records


def write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def retrieval_metrics(expected: list[str], rankings: list[list[str]], ks=(1, 3, 5)) -> dict[str, float]:
    if not expected:
        raise ValueError("Tập đánh giá rỗng.")
    result = {}
    for k in ks:
        result[f"top{k}_accuracy"] = sum(label in rank[:k] for label, rank in zip(expected, rankings)) / len(expected)
    reciprocal = []
    for label, rank in zip(expected, rankings):
        try:
            reciprocal.append(1.0 / (rank.index(label) + 1))
        except ValueError:
            reciprocal.append(0.0)
    result["mrr"] = sum(reciprocal) / len(reciprocal)
    return result

