from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

from .schema import parse_target_schema


# File snapshot nghiep vu co dang "mau 04b" + JSON fragment, khong phai mot
# JSON document hoan chinh. Regex chi dung ASCII cho phan nhan de khong phu
# thuoc encoding cua tu "mau" trong file xuat tu he thong cu.
_SAMPLE_MARKER_RE = re.compile(
    r"(?im)^m[^\r\n]*?(?P<doc_type>[0-9]{2}[a-z]?)\s*:?[ \t]*$"
)
_CONTENT_ID_TOKEN = '"DocumentContentId"'


def extract_snapshot_documents(raw_text: str) -> list[tuple[str, list[dict[str, Any]]]]:
    """Doc cac DocumentContent va giu dung DocType/form_index cua tung block."""

    markers = list(_SAMPLE_MARKER_RE.finditer(raw_text.lstrip("\ufeff")))
    if not markers:
        raise ValueError("Snapshot khong co marker 'mau <DocTypeCode>'.")

    decoder = json.JSONDecoder()
    result: list[tuple[str, list[dict[str, Any]]]] = []
    for index, marker in enumerate(markers):
        end = markers[index + 1].start() if index + 1 < len(markers) else len(raw_text)
        block = raw_text[marker.end():end]
        cursor = 0
        contents: list[dict[str, Any]] = []
        while True:
            token_at = block.find(_CONTENT_ID_TOKEN, cursor)
            if token_at < 0:
                break
            object_at = block.rfind("{", 0, token_at)
            if object_at < 0:
                cursor = token_at + len(_CONTENT_ID_TOKEN)
                continue
            try:
                value, consumed = decoder.raw_decode(block[object_at:])
            except json.JSONDecodeError:
                cursor = token_at + len(_CONTENT_ID_TOKEN)
                continue
            cursor = object_at + consumed
            if isinstance(value, dict) and (value.get("FormConfig") or value.get("FormCode")):
                contents.append(value)
        if contents:
            result.append((marker.group("doc_type").lower(), contents))
    if not result:
        raise ValueError("Snapshot khong chua DocumentContent co FormConfig/FormCode hop le.")
    return result


def build_field_catalog(raw_text: str, source_name: str = "snapshot.txt") -> list[dict[str, Any]]:
    """Chuyen snapshot cu thanh catalog field co DocType va form_index chinh xac."""

    records: list[dict[str, Any]] = []
    for doc_type_code, contents in extract_snapshot_documents(raw_text):
        document = {"DocTypeCode": doc_type_code, "DocumentContents": contents}
        document_json = json.dumps(document, ensure_ascii=False)
        for form_index, content in enumerate(contents):
            parsed = parse_target_schema(document_json, form_index=form_index)
            for field in parsed.fields:
                records.append({
                    "id": field.field_id,
                    "data_field_id": field.field_id,
                    "field_name": field.field_name,
                    "field_title": field.label,
                    "aliases": field.aliases,
                    "document_content_id_representative": content.get("DocumentContentId"),
                    "content_name": content.get("ContentName") or "",
                    "form_name": content.get("FormName") or "",
                    "form_id": field.form_id,
                    "form_index": form_index,
                    "doc_type_code": doc_type_code,
                    "column_code": field.column_code,
                    "header_path": field.header_path,
                    "data_type": field.data_type,
                    "required": field.required,
                    "read_only": field.read_only,
                    "hidden": field.hidden,
                    "source": source_name,
                })
    return records


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(json.dumps(item, ensure_ascii=False, allow_nan=False) + "\n" for item in records)
    path.write_text(payload, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Tao eform_fields.jsonl tu snapshot eForm cu.")
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    text = args.snapshot.read_text(encoding="utf-8-sig")
    records = build_field_catalog(text, source_name=args.snapshot.name)
    write_jsonl(args.output, records)
    print(json.dumps({"output": str(args.output), "fields": len(records)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
