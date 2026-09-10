# Ánh xạ chỉ tiêu phân cấp và JSON contract

## Mục tiêu

Module tách hai bài toán độc lập:

1. Ánh xạ cột theo `DocType + form_index + header_path + column_code + data_type`.
2. Ánh xạ hàng theo `code + label + kind + level + parent_ref + path`.

Không dùng số liệu báo cáo làm đặc trưng. Rule tổng, required, readonly và marker vẫn được xử lý deterministic.

## Quy ước cấp hàng

| Dạng | kind | level điển hình |
|---|---|---:|
| `Tổng số`, `Tổng cộng` | `total` | 0 |
| `I`, `II`, `III` | `section` | 1 |
| `1`, `2`, `3` dưới một Mục | `group` | 2 |
| `1.1`, `1.2` | `detail` | 3 |
| `-`, `...`, `…` không có nội dung nghiệp vụ | `marker` | không map |

Khi sang Mục II, mã `1` phải nhận parent là Mục II; không được nối tiếp parent của Mục I. Nhãn chung như `Tổng số` chỉ được auto-map khi path cha và/hoặc mã cột xác nhận được ngữ cảnh.

## Structured output

LLM chỉ trả:

```json
{
  "schema_version": "1.0",
  "mappings": [
    {"source_ref": "R8", "target_ref": "form:0:row:1", "confidence": 0.99}
  ]
}
```

Contract đầy đủ ở `Module/AI Import/Prompts/hierarchy-mapping-output.schema.json`. Server từ chối output nếu:

- JSON lỗi, có field thừa hoặc text thừa;
- thiếu/thừa/trùng `source_ref`;
- `target_ref` không thuộc schema hoặc bị dùng hai lần;
- `total` bị map sang `section/group/detail`;
- `level` hoặc quan hệ parent bị đổi.

LLM lỗi không làm hỏng response API: kết quả bị gắn `LLM_OUTPUT_REJECTED`, `requires_review=true` và fallback về baseline deterministic.

## Tương thích hệ thống import hiện tại

Schema eForm được đọc trực tiếp từ `DocumentContents`:

- `FormConfig` hoặc `FormCode`: thứ tự field, title, `headerSetting`, `columnSetting`;
- `DefineConfigJson`: mã cột `A`, `B`, `(1)`, `(2)`;
- `SourceData`, `ValueData` hoặc `DefineValueJson`: các dòng cố định và nhãn chỉ tiêu;
- `form_index`: biểu/sheet tương ứng trong document nhiều biểu.

Marker `-`, `—`, `...`, `…` được coi là hợp lệ giống giao diện Handsontable. Service không thay thế các cấu hình `_SUM_VALIDATE_CONFIG`, `_ROWSUM_VALIDATE_CONFIG`, `_READONLY_COL_CONFIG` và `_COL_DATA_REQUIRED_CONFIG`.

Lưu ý từ bộ file tham chiếu: `sum-row-config.js` được cung cấp hiện có cùng SHA-256 và cùng global `_SUM_VALIDATE_CONFIG` với `sum-col-config.js`; vì vậy nó không khai báo `_ROWSUM_VALIDATE_CONFIG`. Cần thay bằng đúng file row-sum ở phía giao diện nếu muốn `checkRowSumRules()` chạy.

## Chạy kiểm tra

```powershell
cd '.\Module\AI Import\Main'
python -m pytest -q
```

File request mẫu: `Module/AI Import/Main/examples/hierarchy-map-request.json`.
