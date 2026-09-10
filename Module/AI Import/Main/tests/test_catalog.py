import json

from ai_import.catalog import build_field_catalog, extract_snapshot_documents


def _content(content_id: int, field_name: str, title: str) -> dict:
    config = {
        "header": {f"{field_name}!!{title}": "int"},
        "extra": {"headerSetting": [["(1)"]], "columnSetting": {}},
    }
    return {
        "DocumentContentId": content_id,
        "ContentName": title,
        "FormId": f"form-{content_id}",
        "FormName": field_name,
        "FormConfig": json.dumps(config, ensure_ascii=False),
    }


def test_snapshot_keeps_multiple_forms_under_the_same_doc_type():
    first = _content(1, "tongso", "Tổng số")
    second = _content(2, "chitiet", "Chi tiết")
    third = _content(3, "ghichu", "Ghi chú")
    snapshot = (
        "mẫu 01d\n\"DocumentContents\": ["
        + json.dumps(first, ensure_ascii=False)
        + ","
        + json.dumps(second, ensure_ascii=False)
        + "],\n"
        + "mẫu 04b:\n\"DocumentContents\": ["
        + json.dumps(third, ensure_ascii=False)
        + "]"
    )

    groups = extract_snapshot_documents(snapshot)
    assert [(code, len(items)) for code, items in groups] == [("01d", 2), ("04b", 1)]

    records = build_field_catalog(snapshot)
    assert [(item["doc_type_code"], item["form_index"], item["field_name"]) for item in records] == [
        ("01d", 0, "tongso"),
        ("01d", 1, "chitiet"),
        ("04b", 0, "ghichu"),
    ]
    assert all(item["column_code"] == "(1)" for item in records)
