from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Chặn release khi model mới kém baseline hoặc không đạt ngưỡng.")
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--min-top1", type=float, default=0.85)
    parser.add_argument("--min-top3", type=float, default=0.95)
    args = parser.parse_args()
    baseline = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    candidate = json.loads(Path(args.candidate).read_text(encoding="utf-8"))
    checks = {
        "top1_gate": candidate["top1_accuracy"] >= args.min_top1,
        "top3_gate": candidate["top3_accuracy"] >= args.min_top3,
        "no_top1_regression": candidate["top1_accuracy"] >= baseline["top1_accuracy"],
        "no_mrr_regression": candidate["mrr"] >= baseline["mrr"],
    }
    print(json.dumps(checks, indent=2))
    sys.exit(0 if all(checks.values()) else 2)


if __name__ == "__main__":
    main()

