from __future__ import annotations

import argparse
import random
from pathlib import Path

from common import read_jsonl, set_seed, write_jsonl


PREFIXES = ["", "Chỉ tiêu ", "Thông tin ", "Số liệu "]
SUFFIXES = ["", " (báo cáo)", " năm nay", " - tổng hợp"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", default="../Data/synthetic/mapping_synthetic.jsonl")
    parser.add_argument("--per-record", type=int, default=3)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    set_seed(args.seed)
    records = read_jsonl([Path(args.input).resolve()])
    generated = []
    for item in records:
        seen = {item["source"]}
        for _ in range(args.per_record * 3):
            candidate = random.choice(PREFIXES) + item["source"] + random.choice(SUFFIXES)
            candidate = " ".join(candidate.split())
            if candidate not in seen:
                seen.add(candidate)
                generated.append({**item, "source": candidate, "synthetic": True})
            if len(seen) > args.per_record:
                break
    write_jsonl(Path(args.output).resolve(), generated)
    print(f"Đã tạo {len(generated)} mẫu; phải đánh giá trên tập thật, không đánh giá trên mẫu synthetic.")


if __name__ == "__main__":
    main()

