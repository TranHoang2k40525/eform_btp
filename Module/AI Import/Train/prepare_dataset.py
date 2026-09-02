from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

from common import read_jsonl, set_seed, write_jsonl


def grouped_split(records: list[dict], seed: int) -> tuple[list[dict], list[dict], list[dict]]:
    """Keep the same semantic field group in one split to prevent alias leakage."""
    groups: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        groups[str(record.get("group_id") or record["target_id"])].append(record)
    keys = sorted(groups)
    random.Random(seed).shuffle(keys)
    if len(keys) < 3:
        raise ValueError("Cần ít nhất 3 group_id để tạo train/validation/test không rò rỉ.")
    validation_size = max(1, round(len(keys) * 0.2))
    test_size = max(1, round(len(keys) * 0.2))
    test_keys = set(keys[:test_size])
    validation_keys = set(keys[test_size:test_size + validation_size])
    train_keys = set(keys) - test_keys - validation_keys
    collect = lambda selected: [item for key in sorted(selected) for item in groups[key]]
    return collect(train_keys), collect(validation_keys), collect(test_keys)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", action="append", required=True, help="JSONL; có thể truyền nhiều lần")
    parser.add_argument("--output", default="../Data/processed")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    set_seed(args.seed)
    records = read_jsonl(Path(item).resolve() for item in args.input)
    unique = {(item["source"].strip().lower(), item["target_id"]): item for item in records}
    train, validation, test = grouped_split(list(unique.values()), args.seed)
    output = Path(args.output).resolve()
    write_jsonl(output / "train.jsonl", train)
    write_jsonl(output / "validation.jsonl", validation)
    write_jsonl(output / "test.jsonl", test)
    manifest = {"seed": args.seed, "total": len(unique), "train": len(train),
                "validation": len(validation), "test": len(test),
                "split_rule": "group_id-isolated"}
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

