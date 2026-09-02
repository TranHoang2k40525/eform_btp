from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from common import read_jsonl, write_jsonl


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--approved-feedback", required=True)
    parser.add_argument("--existing", required=True)
    parser.add_argument("--merged", default="../Data/processed/incremental-train.jsonl")
    parser.add_argument("--minimum-new", type=int, default=100)
    args = parser.parse_args()
    existing = read_jsonl([Path(args.existing).resolve()])
    feedback = [item for item in read_jsonl([Path(args.approved_feedback).resolve()]) if item.get("accepted")]
    if len(feedback) < args.minimum_new:
        raise ValueError(f"Chưa đủ {args.minimum_new} feedback đã duyệt; không nên train lại.")
    combined = {(item["source"].lower(), item["target_id"]): item for item in [*existing, *feedback]}
    output = Path(args.merged).resolve()
    write_jsonl(output, list(combined.values()))
    print(f"Đã tạo {output} gồm {len(combined)} mẫu. Chạy prepare_dataset, train_embedding, evaluate_model và compare_release.")


if __name__ == "__main__":
    main()

