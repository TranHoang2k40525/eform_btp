from __future__ import annotations

import argparse
import json
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
    feedback = []
    with Path(args.approved_feedback).resolve().open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            raw = json.loads(line)
            if not raw.get("accepted"):
                continue
            target_id = raw.get("target_id") or raw.get("selected_field_id")
            source = raw.get("source") or raw.get("source_header")
            if not target_id or not source:
                continue
            feedback.append({"group_id": raw.get("group_id") or f"feedback-{raw.get('job_id', 'unknown')}",
                             "source": source, "target_id": target_id,
                             "target_text": raw.get("target_text") or target_id,
                             "from_feedback": True})
    if len(feedback) < args.minimum_new:
        raise ValueError(f"Chưa đủ {args.minimum_new} feedback đã duyệt; không nên train lại.")
    combined = {(item["source"].lower(), item["target_id"]): item for item in [*existing, *feedback]}
    output = Path(args.merged).resolve()
    write_jsonl(output, list(combined.values()))
    print(f"Đã tạo {output} gồm {len(combined)} mẫu. Chạy prepare_dataset, train_embedding, evaluate_model và compare_release.")


if __name__ == "__main__":
    main()
