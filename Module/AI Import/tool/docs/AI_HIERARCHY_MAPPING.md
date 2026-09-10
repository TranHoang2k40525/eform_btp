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

Mã STT có độ ưu tiên cao hơn từ khóa trong nhãn: dòng mang mã `1` và nhãn `Tổng số hồ sơ...` vẫn là `group`, không bị kéo lên `total`. Nhãn chỉ chứa số nhưng không có mã phân cấp (ví dụ `664`, `66464` trong dữ liệu tham chiếu) được gắn `SUSPECTED_SHIFTED_VALUE` và bắt buộc duyệt vì có khả năng lệch cột.

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

Contract đầy đủ của gói tool ở `../Prompts/hierarchy-mapping-output.schema.json`. Server từ chối output nếu:

- JSON lỗi, có field thừa hoặc text thừa;
- thiếu/thừa/trùng `source_ref`;
- `target_ref` không thuộc schema hoặc bị dùng hai lần;
- `total` bị map sang `section/group/detail`;
- `level` hoặc quan hệ parent bị đổi.

LLM lỗi không làm hỏng response API: kết quả bị gắn `LLM_OUTPUT_REJECTED`, `requires_review=true` và fallback về baseline deterministic.

LLM chỉ là lớp đề xuất bổ sung: việc LLM đồng ý không được nâng một mapping mà baseline đánh dấu `review` thành `auto`; việc LLM trả `null` cũng không âm thầm xóa một mapping baseline đã tự động xác nhận.

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

File request mẫu: `../runtime/examples/hierarchy-map-request.json`.

Kết quả kiểm chứng ngày 10/09/2026, chỉ dùng hai workbook Raw theo phạm vi rà soát:

- `04b`, form 0: 19/19 cột `auto`, không có cột `review/unmapped`, JSON hợp lệ.
- `01d`, form 0: 3/3 cột `auto`; form 1: 14/14 cột và 2/2 dòng chỉ tiêu `auto`, JSON hợp lệ.
- Đối chiếu 149 dòng `04c` từ `mới 1.txt` với schema hiện hữu: 145 `auto`, 3 `review` có mã `SUSPECTED_SHIFTED_VALUE` (`43555`, `664`, `66464`) và 1 marker `- / ...` được bỏ qua.
- Bộ test tự động: 19 test đạt.
