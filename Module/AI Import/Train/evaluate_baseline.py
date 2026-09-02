from __future__ import annotations

import argparse
import json
from pathlib import Path

from ai_import.config import Settings
from ai_import.mapping import HybridFieldMapper
from ai_import.models import TargetFieldDto

from common import read_jsonl, retrieval_metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", default="../Data/processed/test.jsonl")
    parser.add_argument("--output", default="../Models/baseline-evaluation.json")
    args = parser.parse_args()
    records = read_jsonl([Path(args.test).resolve()])
    target_texts = {item["target_id"]: item["target_text"] for item in records}
    targets = [TargetFieldDto(field_id=field_id, label=text.split(";")[0].strip(),
                              aliases=[part.strip() for part in text.split(";")[1:] if part.strip()])
               for field_id, text in sorted(target_texts.items())]
    mapper = HybridFieldMapper(Settings(embedding_enabled=False))
    rankings = []
    for record in records:
        scored = sorted((mapper._lexical(record["source"], target) for target in targets),
                        key=lambda item: item.score, reverse=True)
        rankings.append([item.field.field_id for item in scored])
    metrics = retrieval_metrics([item["target_id"] for item in records], rankings)
    metrics.update({"model": "lexical-baseline-v1", "test_examples": len(records), "target_count": len(targets)})
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

