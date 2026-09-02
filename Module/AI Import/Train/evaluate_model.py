from __future__ import annotations

import argparse
import json
from pathlib import Path

from sentence_transformers import SentenceTransformer

from common import read_jsonl, retrieval_metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--test", default="../Data/processed/test.jsonl")
    parser.add_argument("--output", default="../Models/evaluation.json")
    args = parser.parse_args()
    records = read_jsonl([Path(args.test).resolve()])
    targets = {}
    for item in records:
        targets[item["target_id"]] = item["target_text"]
    if len(targets) < 2:
        raise ValueError("Tập test phải có ít nhất hai target_id.")
    target_ids = sorted(targets)
    model = SentenceTransformer(args.model)
    query_vectors = model.encode([f"query: {item['source']}" for item in records], normalize_embeddings=True)
    target_vectors = model.encode([f"passage: {targets[item]}" for item in target_ids], normalize_embeddings=True)
    scores = query_vectors @ target_vectors.T
    rankings = [[target_ids[index] for index in row.argsort()[::-1]] for row in scores]
    metrics = retrieval_metrics([item["target_id"] for item in records], rankings)
    metrics.update({"model": args.model, "test_examples": len(records), "target_count": len(targets)})
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

