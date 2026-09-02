from __future__ import annotations

import argparse
import json

from .config import settings
from .service import ImportAiService


def main() -> None:
    parser = argparse.ArgumentParser(description="Phân tích workbook Excel cho eForm.")
    parser.add_argument("path")
    parser.add_argument("--include-hidden", action="store_true")
    parser.add_argument("--preview-rows", type=int, default=25)
    args = parser.parse_args()
    result = ImportAiService(settings).analyze(args.path, args.include_hidden, args.preview_rows)
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()

