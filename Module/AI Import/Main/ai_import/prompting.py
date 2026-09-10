from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

from .hierarchy import enrich_indicators
from .models import HierarchyMapRequest


SYSTEM_PROMPT = """Bạn là bộ ánh xạ chỉ tiêu thống kê Excel sang cấu trúc eForm.

Quy tắc bắt buộc:
1. Chỉ chọn target_ref có trong TARGET_INDICATORS. Không tự tạo ID, nhãn hoặc dòng mới.
2. Giữ đúng quan hệ phân cấp. 'Tổng số' không có mã STT là cấp tổng; I/II/III là Mục; 1/2/3 là con trực tiếp của Mục gần nhất; 1.1/1.2 là con của dòng 1 trong cùng Mục. Nếu nhãn bắt đầu bằng 'Tổng số' nhưng có mã 1/2/3 thì mã STT quyết định và dòng vẫn là cấp con.
3. Mã 1 có thể lặp lại sau Mục II; phải dùng toàn bộ path cha/con, không ánh xạ chỉ bằng chữ 'Tổng số' hoặc riêng con số.
4. Không ánh xạ dòng marker '-', '...', '…'. Với dòng không chắc chắn, target_ref phải là null.
5. Mỗi source_ref xuất hiện đúng một lần. Một target_ref chỉ được dùng tối đa một lần.
6. Không sử dụng giá trị thống kê để đoán đích; chỉ dùng DocType, biểu, mã cấp, nhãn, level, kind và path.
7. Nhãn chỉ chứa số liệu như '664' hoặc '66464' nhưng không có mã phân cấp hợp lệ là dấu hiệu lệch cột; không tự động xác nhận, hãy trả target_ref=null nếu thiếu ngữ cảnh chắc chắn.
8. Trả về duy nhất một JSON object đúng schema. Không Markdown, không giải thích ngoài JSON.
"""


_OUTPUT_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "eForm hierarchy mapping output",
    "type": "object",
    "additionalProperties": False,
    "required": ["schema_version", "mappings"],
    "properties": {
        "schema_version": {"type": "string", "const": "1.0"},
        "mappings": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["source_ref", "target_ref", "confidence"],
                "properties": {
                    "source_ref": {"type": "string", "minLength": 1},
                    "target_ref": {
                        "anyOf": [
                            {"type": "string", "minLength": 1},
                            {"type": "null"},
                        ]
                    },
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                },
            },
        },
    },
}


def hierarchy_output_schema() -> dict[str, Any]:
    return deepcopy(_OUTPUT_SCHEMA)


def _source_payload(request: HierarchyMapRequest) -> list[dict[str, Any]]:
    return [
        {
            "source_ref": item.source_ref,
            "code": item.code,
            "label": item.label,
            "kind": item.kind,
            "level": item.level,
            "parent_ref": item.parent_ref,
            "path": item.path,
        }
        for item in enrich_indicators(request.source_indicators)
        if item.kind != "marker"
    ]


def _target_payload(request: HierarchyMapRequest) -> list[dict[str, Any]]:
    return [
        {
            "target_ref": item.target_ref,
            "code": item.code,
            "label": item.label,
            "kind": item.kind,
            "level": item.level,
            "parent_ref": item.parent_ref,
            "path": item.path,
        }
        for item in enrich_indicators(request.target_indicators)
        if item.kind != "marker"
    ]


def build_hierarchy_messages(request: HierarchyMapRequest) -> list[dict[str, str]]:
    payload = {
        "task": "map_statistical_indicator_hierarchy",
        "doc_type_code": request.doc_type_code,
        "report_title": request.report_title,
        "form_index": request.form_index,
        "source_indicators": _source_payload(request),
        "target_indicators": _target_payload(request),
    }
    user_prompt = (
        "Ánh xạ từng source_ref sang target_ref phù hợp. "
        "Nếu có nhiều nhãn giống nhau, bắt buộc so sánh parent_ref và path.\n"
        "INPUT_JSON:\n"
        + json.dumps(payload, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT.strip()},
        {"role": "user", "content": user_prompt},
    ]
