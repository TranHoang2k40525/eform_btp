from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

from .models import TargetFieldDto, TargetIndicatorDto
from .text import fold_vietnamese


_COLUMN_CODE_RE = re.compile(r"^(?:\(\s*\d+\s*\)|[A-Z]{1,3})$")
_INDICATOR_CODE_RE = re.compile(r"^(?:[IVXLCDM]+\.?|\d+(?:\.\d+)*|[-–—])$", re.IGNORECASE)


@dataclass
class ParsedTargetSchema:
    fields: list[TargetFieldDto] = field(default_factory=list)
    indicators: list[TargetIndicatorDto] = field(default_factory=list)
    doc_type_code: str = ""
    report_title: str = ""


def _json_value(value: Any, name: str) -> Any:
    current = value
    for _ in range(3):
        if not isinstance(current, str):
            return current
        text = current.strip().lstrip("\ufeff")
        if not text:
            return None
        try:
            current = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{name} không phải JSON hợp lệ: {exc.msg}.") from exc
    return current


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _field_from_dict(item: dict[str, Any], form_index: int = 0) -> TargetFieldDto:
    field_id = _clean(item.get("field_id") or item.get("data_field_id") or item.get("id") or item.get("field_name"))
    label = _clean(item.get("label") or item.get("field_title") or item.get("title") or field_id)
    if not field_id:
        raise ValueError("Field trong target schema thiếu field_id/data_field_id/field_name.")
    aliases = [_clean(value) for value in item.get("aliases", []) if _clean(value)]
    return TargetFieldDto(
        field_id=field_id,
        field_name=_clean(item.get("field_name") or field_id),
        label=label,
        aliases=list(dict.fromkeys([*aliases, field_id, label])),
        data_type=_clean(item.get("data_type") or item.get("type") or "string"),
        required=bool(item.get("required", False)),
        description=_clean(item.get("description")),
        doc_type_code=_clean(item.get("doc_type_code")),
        form_id=_clean(item.get("form_id")),
        form_index=int(item.get("form_index", form_index) or 0),
        column_code=_clean(item.get("column_code")),
        header_path=[_clean(value) for value in item.get("header_path", []) if _clean(value)],
        read_only=bool(item.get("read_only", False)),
        hidden=bool(item.get("hidden", False)),
    )


def _column_code(config_row: Any, header_setting: list[Any], index: int) -> str:
    values = config_row if isinstance(config_row, list) else []
    normalized = [_clean(value) for value in values]
    for value in normalized:
        if re.fullmatch(r"\(\s*\d+\s*\)", value):
            return value
    for value in normalized:
        if re.fullmatch(r"[A-Z]{1,3}", value):
            return value
    for row in reversed(header_setting):
        if isinstance(row, list) and index < len(row):
            value = _clean(row[index])
            if _COLUMN_CODE_RE.fullmatch(value):
                return value
    return ""


def _header_path(title: str, header_setting: list[Any], index: int, code: str) -> list[str]:
    # FormConfig lưu title theo chính đường dẫn nghiệp vụ, ngăn bằng " - ".
    title_parts = [_clean(value) for value in re.split(r"\s+-\s+", title) if _clean(value)]
    grid_parts: list[str] = []
    for row in header_setting:
        if not isinstance(row, list) or index >= len(row):
            continue
        value = _clean(row[index])
        if value and value != code and not _COLUMN_CODE_RE.fullmatch(value):
            if not grid_parts or fold_vietnamese(grid_parts[-1]) != fold_vietnamese(value):
                grid_parts.append(value)
    return title_parts if len(title_parts) > 1 else (grid_parts or title_parts)


def _rows_from_content(content: dict[str, Any], config: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("SourceData", "ValueData", "DefineValueJson"):
        if content.get(key) not in (None, ""):
            value = _json_value(content[key], key)
            if isinstance(value, list):
                return [row for row in value if isinstance(row, dict)]
    rows = config.get("data", [])
    return [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []


def _indicator_columns(fields: list[TargetFieldDto], rows: list[dict[str, Any]]) -> tuple[str | None, str | None]:
    if not rows or not fields:
        return None, None
    keys = [item.field_name or item.field_id for item in fields]
    titles = {item.field_name or item.field_id: fold_vietnamese(item.label) for item in fields}

    marker_key = next((key for key in keys if "stt" in fold_vietnamese(key) or titles.get(key) in {"stt", "so thu tu"}), None)
    if marker_key is None:
        for key in keys[:3]:
            values = [_clean(row.get(key)) for row in rows if _clean(row.get(key))]
            if values and sum(bool(_INDICATOR_CODE_RE.fullmatch(value)) for value in values) / len(values) >= 0.70:
                marker_key = key
                break

    label_terms = ("chi tiet", "noi dung", "ten don vi", "phan theo", "chi tieu")
    label_key = next(
        (key for key in keys if key != marker_key and any(term in (fold_vietnamese(key) + " " + titles.get(key, "")) for term in label_terms)),
        None,
    )
    if label_key is None and marker_key in keys:
        marker_index = keys.index(marker_key)
        label_key = keys[marker_index + 1] if marker_index + 1 < len(keys) else None
    if label_key is None:
        for key in keys[:2]:
            values = [_clean(row.get(key)) for row in rows if _clean(row.get(key))]
            if values and sum(any(ch.isalpha() for ch in value) for value in values) / len(values) >= 0.70:
                label_key = key
                break
    return marker_key, label_key


def _parse_form(
    content: dict[str, Any],
    form_index: int,
    doc_type_code: str,
) -> tuple[list[TargetFieldDto], list[TargetIndicatorDto]]:
    raw_config = content.get("FormConfig") if content.get("FormConfig") not in (None, "") else content.get("FormCode")
    config = _json_value(raw_config, "FormConfig/FormCode")
    if not isinstance(config, dict):
        raise ValueError(f"Form {form_index} thiếu FormConfig/FormCode dạng object.")
    header = config.get("header", {})
    if not isinstance(header, dict):
        raise ValueError(f"Form {form_index} có FormConfig.header không hợp lệ.")
    extra = config.get("extra", {}) if isinstance(config.get("extra"), dict) else {}
    column_setting = extra.get("columnSetting", {}) if isinstance(extra.get("columnSetting"), dict) else {}
    header_setting = extra.get("headerSetting", []) if isinstance(extra.get("headerSetting"), list) else []
    define_config = _json_value(content.get("DefineConfigJson"), "DefineConfigJson") if content.get("DefineConfigJson") else {}
    config_rows = define_config.get("data", []) if isinstance(define_config, dict) else []
    form_id = _clean(content.get("FormId"))

    fields: list[TargetFieldDto] = []
    for index, (raw_key, raw_type) in enumerate(header.items()):
        field_name, separator, raw_title = str(raw_key).partition("!!")
        field_name, title = _clean(field_name), _clean(raw_title if separator else field_name)
        meta = column_setting.get(raw_key, {}) if isinstance(column_setting.get(raw_key), dict) else {}
        code = _column_code(config_rows[index] if index < len(config_rows) else [], header_setting, index)
        aliases = list(dict.fromkeys([field_name, title, *[part for part in re.split(r"\s+-\s+", title) if part]]))
        fields.append(TargetFieldDto(
            field_id=field_name,
            field_name=field_name,
            label=title,
            aliases=aliases,
            data_type=_clean(raw_type or meta.get("TypeName") or "string"),
            required=bool(meta.get("Required", False)),
            description=_clean(content.get("ContentName")),
            doc_type_code=doc_type_code,
            form_id=form_id,
            form_index=form_index,
            column_code=code,
            header_path=_header_path(title, header_setting, index, code),
            read_only=bool(meta.get("ReadOnly", False)),
            hidden=bool(meta.get("Hidden", False)),
        ))

    rows = _rows_from_content(content, config)
    marker_key, label_key = _indicator_columns(fields, rows)
    indicators: list[TargetIndicatorDto] = []
    if label_key and (len(rows) > 1 or any("tong" in fold_vietnamese(row.get(label_key)) for row in rows)):
        for index, row in enumerate(rows):
            label = _clean(row.get(label_key))
            code = _clean(row.get(marker_key)) if marker_key else ""
            if not label:
                continue
            indicators.append(TargetIndicatorDto(
                target_ref=f"form:{form_index}:row:{index + 1}",
                target_row=index + 1,
                code=code,
                label=label,
            ))
    return fields, indicators


def parse_target_schema(raw_json: str, form_index: int = 0) -> ParsedTargetSchema:
    payload = _json_value(raw_json, "target_schema_json")
    if isinstance(payload, list):
        return ParsedTargetSchema(fields=[_field_from_dict(item, form_index) for item in payload if isinstance(item, dict)])
    if not isinstance(payload, dict):
        raise ValueError("target_schema_json phải là object hoặc array.")

    if isinstance(payload.get("fields"), list):
        fields = [_field_from_dict(item, form_index) for item in payload["fields"] if isinstance(item, dict)]
        indicators = [TargetIndicatorDto.model_validate(item) for item in payload.get("indicators", [])]
        return ParsedTargetSchema(
            fields=fields,
            indicators=indicators,
            doc_type_code=_clean(payload.get("doc_type_code")),
            report_title=_clean(payload.get("report_title")),
        )

    document = payload.get("document") if isinstance(payload.get("document"), dict) else payload
    contents = document.get("DocumentContents") if isinstance(document, dict) else None
    if isinstance(contents, list):
        if form_index >= len(contents):
            raise ValueError(f"form_index={form_index} vượt số DocumentContents={len(contents)}.")
        content = contents[form_index]
        if not isinstance(content, dict):
            raise ValueError(f"DocumentContents[{form_index}] không phải object.")
        doc_type_code = _clean(document.get("DocTypeCode"))
        fields, indicators = _parse_form(content, form_index, doc_type_code)
        return ParsedTargetSchema(
            fields=fields,
            indicators=indicators,
            doc_type_code=doc_type_code,
            report_title=_clean(content.get("ContentName")),
        )

    if "header" in payload:
        fields, indicators = _parse_form({"FormConfig": payload}, form_index, _clean(payload.get("doc_type_code")))
        return ParsedTargetSchema(fields=fields, indicators=indicators, doc_type_code=_clean(payload.get("doc_type_code")))

    # Cho phép một field object duy nhất, nhưng không âm thầm nhận schema không rõ dạng.
    if any(key in payload for key in ("field_id", "data_field_id", "field_name")):
        return ParsedTargetSchema(fields=[_field_from_dict(payload, form_index)])
    raise ValueError("Không nhận diện được target schema: cần fields hoặc DocumentContents/FormConfig.header.")
