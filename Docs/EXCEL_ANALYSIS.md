# Phân tích ba workbook Excel

## 1. Phương pháp và giới hạn

Ba workbook được đọc trực tiếp từ cấu trúc Open XML. Phân tích bao gồm workbook metadata, trạng thái sheet, ô có dữ liệu, merged ranges, style index, độ rộng/cao, công thức và cached value. Toàn bộ entry media/drawing và mọi ảnh đều bị bỏ qua theo yêu cầu của người dùng.

Vì không đọc ảnh kết quả mong đợi, tài liệu này không khẳng định độ giống giao diện theo pixel. Việc đối chiếu chỉ dựa trên Excel, schema eForm và contract dữ liệu của Handsontable.

Các khái niệm dùng trong tài liệu:

- `physical cells`: ô có node XML; có thể chỉ mang style nhưng không có dữ liệu;
- `non-empty`: ô có value, inline string hoặc formula;
- `used`: biên nhỏ nhất/lớn nhất của các ô non-empty;
- cached value của formula chỉ là kết quả Excel lưu lần cuối, không được coi là nguồn chân lý nghiệp vụ.

## 2. Workbook 1 — báo cáo 01a của UBND Phường Láng

Tên tệp: `UBND Phường Láng_01a_TP_TĐ-BH_Số dự thảo (DT) văn bản quy phạm pháp luật (V(...).xlsx`

### 2.1. Metadata

| Thuộc tính | Giá trị |
|---|---|
| Kích thước | 12.895 byte |
| Số sheet | 1 |
| Sheet | `Sheet1` |
| Vùng Excel khai báo | `A1:Z12` |
| Vùng có dữ liệu | hàng 1–12, cột A–K |
| Physical cells | 286 |
| Non-empty cells | 42 |
| Shared strings | 30 |
| Cell styles | 42 |
| Merged ranges | 19 |
| Formula | 0 |
| Hidden row/column | 0/0 |

### 2.2. Table candidate

Vùng bảng nghiệp vụ chính là `A3:I8`:

- hàng 3–6: header phân cấp nhiều tầng;
- hàng 7: mã cột `(1)` đến `(9)`;
- hàng 8: một hàng dữ liệu;
- hàng 1: tên biểu, tiêu đề báo cáo, đơn vị báo cáo/nhận;
- hàng 11: ghi chú;
- hàng 12: khu vực chữ ký.

Các merge quan trọng gồm `A3:F3`, `G3:I3`, `A4:C4`, `D4:F4`, `G4:G6`, `H4:I4`, `A5:A6`, `B5:C5`, `D5:D6`, `E5:F5`, `H5:H6`, `I5:I6`.

### 2.3. Header đã diễn giải

| Cột | Mã | Ý nghĩa leaf header |
|---|---:|---|
| A | (1) | Tổng số dự thảo VBQPPL đã được thẩm định |
| B | (2) | Số dự thảo Nghị quyết của HĐND |
| C | (3) | Số dự thảo Quyết định của UBND |
| D | (4) | Tổng số TTHC tại dự thảo đã được thẩm định |
| E | (5) | TTHC tại dự thảo Nghị quyết của HĐND |
| F | (6) | TTHC tại dự thảo Quyết định của UBND |
| G | (7) | Tổng số VBQPPL đã ban hành |
| H | (8) | Số Nghị quyết của HĐND đã ban hành |
| I | (9) | Số Quyết định của UBND đã ban hành |

### 2.4. Values, note và formula

Hàng 8 có giá trị:

```text
(1)..(9) = 11, 4, 7, 10, 3, 7, 7, 2, 5
```

Các quan hệ cộng đều đúng:

- `(1) = (2) + (3)` → `11 = 4 + 7`;
- `(4) = (5) + (6)` → `10 = 3 + 7`;
- `(7) = (8) + (9)` → `7 = 2 + 5`.

Ô `K8 = "s"` nằm ngoài vùng bảng A:I, là nhiễu cần bị region detector loại bỏ. Workbook không chứa công thức; mọi con số là literal.

## 3. Workbook 2 — `ví dụ 2.xlsx`

### 3.1. Metadata

| Thuộc tính | Giá trị |
|---|---|
| Kích thước | 11.319 byte |
| Số sheet | 1 |
| Sheet | `Trang_tính1` |
| Vùng Excel khai báo | `A1:Z12` |
| Vùng có dữ liệu | hàng 3–11, cột A–K |
| Physical cells | 286 |
| Non-empty cells | 36 |
| Shared strings | 24 |
| Cell styles | 40 |
| Merged ranges | 13 |
| Formula | 0 |
| Hidden row/column | 0/0 |

### 3.2. Table candidate

Vùng `A3:I8` có cùng header và cùng hàng giá trị với workbook 1. Khác biệt:

- không có metadata/tên biểu ở hàng 1;
- không có khu vực chữ ký hàng 12;
- vẫn có hàng ghi chú 11;
- số merge ít hơn vì thiếu title/footer;
- tên sheet khác hoàn toàn;
- style index khác dù hình học bảng giống;
- cũng có nhiễu `K8 = "s"`.

Đây là ví dụ tốt cho thấy không được nhận diện biểu bằng filename, sheet name hoặc tọa độ header cố định. Nội dung header phân cấp và các quan hệ cột mới là tín hiệu bền vững.

### 3.3. Values, note và formula

Hàng dữ liệu vẫn là `11, 4, 7, 10, 3, 7, 7, 2, 5`; không có formula. Công thức nghiệp vụ phải lấy từ schema/rule eForm, không được suy ra rằng mọi file có cùng con số mẫu.

## 4. So sánh workbook 1 và 2

| Đặc điểm | Workbook 1 | Workbook 2 | Ý nghĩa cho analyzer |
|---|---|---|---|
| Tên sheet | `Sheet1` | `Trang_tính1` | Không dùng tên sheet làm khóa |
| Metadata biểu | Có | Không | DocType matcher phải chịu được thiếu metadata |
| Header `A3:I7` | Giống | Giống | Header path là tín hiệu chính |
| Data row | Giống | Giống | Dùng để kiểm thử mapping/validation, không hard-code |
| Footer chữ ký | Có | Không | Phải tách table region khỏi footer |
| Nhiễu K8 | Có | Có | Region detector phải chặn cột rời ngoài bảng |
| Formula | Không | Không | Rule eForm kiểm tra quan hệ, không phụ thuộc formula Excel |

## 5. Workbook 3 — `Tổng hợp biểu mẫu_KHTC.BTP.xlsx`

### 5.1. Metadata tổng thể

| Thuộc tính | Giá trị |
|---|---|
| Kích thước | 3.722.738 byte |
| Số sheet | 77 |
| Visible/hidden | 67/10 |
| Shared strings | 28.866 |
| Cell styles | 1.981 |
| Physical cells | 796.448 |
| Non-empty cells | 116.630 |
| Formula cells | 449 |
| Merged ranges | 3.006 |

Nhiều sheet có khoảng 999–1.001 row XML nhưng chỉ vài chục hàng có nội dung. Đây chủ yếu là style được áp trước xuống vùng trống; analyzer phải dựa trên non-empty bounds thay vì `maxRow`/dimension thô để tránh tạo hàng rác.

### 5.2. Phân nhóm sheet

| Nhóm | Sheet | Vai trò quan sát |
|---|---|---|
| Dữ liệu tổng hợp ẩn | 1, 2 | Dữ liệu địa phương/toàn quốc và formula tổng |
| Danh mục vận hành | 3, 4 | Mã biểu tổng hợp/nguồn, kỳ, bảng vật lý, function, trạng thái |
| Workflow | 5 | Đơn vị gửi/nhận và các node xử lý |
| Tài khoản | 6, 8 | Dữ liệu tài khoản; sheet 8 ghi “bỏ” |
| Theo dõi lỗi/dev | 9–11 | Lỗi chung, tổng hợp ẩn và mapping dev |
| Template biểu nhập | 7, 12–49, 54–66, 68–77 | 62 sheet mẫu mã biểu thông thường |
| Tổng hợp chuyên biệt | 50–53, 67 | Nhóm 15A/B/C, tổng hợp 18, 17THCN |

Sheet tài khoản chứa dữ liệu nhạy cảm dạng rõ. Nội dung không được sao chép vào tài liệu này, không được đưa vào dataset và không được gửi sang model. Nếu đây là tài khoản còn hiệu lực, cần đổi secret và tách chúng khỏi workbook mẫu.

### 5.3. Kiểm kê toàn bộ 77 sheet

`Used` có dạng `hàng đầu-hàng cuối/cột đầu-cột cuối`.

| # | Sheet | State | Used | Non-empty | Formula | Merge |
|---:|---|---|---|---:|---:|---:|
| 1 | Kết quả đăng ký khai sinh, khai | hidden | 1-53/1-19 | 394 | 18 | 36 |
| 2 | Phổ biến GD PL | hidden | 2-58/1-21 | 492 | 89 | 64 |
| 3 | Biểu cả nước | visible | 1-133/1-17 | 1.201 | 0 | 172 |
| 4 | Biểu xã, sở, bộ ngành | visible | 1-187/1-13 | 1.579 | 0 | 142 |
| 5 | Quy trình | visible | 1-30/1-12 | 239 | 0 | 0 |
| 6 | DS.acc | visible | 1-11749/1-9 | 58.019 | 0 | 0 |
| 7 | 1a | visible | 1-14/1-9 | 35 | 0 | 20 |
| 8 | Danh sách acc (bỏ) | hidden | 1-10722/1-4 | 42.878 | 0 | 0 |
| 9 | Lỗi chung | hidden | 1-119/1-9 | 301 | 42 | 0 |
| 10 | TH(ẩn) | hidden | 1-211/1-39 | 2.730 | 0 | 458 |
| 11 | TH_Biểu_dev | hidden | 1-194/1-33 | 1.288 | 12 | 353 |
| 12 | 04a | visible | 1-26/1-19 | 92 | 0 | 32 |
| 13 | 05b | visible | 1-29/1-25 | 291 | 167 | 27 |
| 14 | 6a | visible | 1-26/1-23 | 129 | 1 | 76 |
| 15 | 8a | visible | 1-11/1-10 | 44 | 0 | 17 |
| 16 | 9a | visible | 1-13/1-9 | 33 | 0 | 20 |
| 17 | 04b | visible | 1-23/1-19 | 71 | 0 | 32 |
| 18 | 1b | visible | 1-19/1-20 | 108 | 0 | 34 |
| 19 | 1c | visible | 1-19/1-12 | 72 | 0 | 22 |
| 20 | 1d | visible | 1-27/1-14 | 50 | 0 | 25 |
| 21 | 1e | visible | 1-29/1-16 | 81 | 0 | 20 |
| 22 | 1g | visible | 1-12/1-14 | 42 | 0 | 14 |
| 23 | 2a | visible | 1-12/1-14 | 63 | 0 | 24 |
| 24 | 3a | visible | 1-15/1-7 | 36 | 0 | 13 |
| 25 | 2b | visible | 1-20/1-17 | 69 | 0 | 29 |
| 26 | 3b | visible | 1-17/1-9 | 45 | 0 | 17 |
| 27 | 3c | visible | 1-12/1-6 | 35 | 0 | 24 |
| 28 | 04c | visible | 1-56/1-24 | 290 | 0 | 38 |
| 29 | 04d | visible | 1-22/1-19 | 69 | 0 | 32 |
| 30 | 05a | visible | 1-15/1-13 | 39 | 0 | 16 |
| 31 | 6b | visible | 1-30/1-25 | 132 | 0 | 94 |
| 32 | 05c | visible | 1-17/1-26 | 111 | 0 | 29 |
| 33 | 6c | visible | 1-17/1-14 | 64 | 0 | 31 |
| 34 | 6d | visible | 1-24/1-15 | 79 | 0 | 38 |
| 35 | 7 | visible | 1-11/1-10 | 17 | 0 | 19 |
| 36 | 8b | visible | 1-15/1-13 | 47 | 0 | 19 |
| 37 | 8c | visible | 1-23/1-13 | 83 | 0 | 39 |
| 38 | 8d | visible | 1-16/1-12 | 48 | 0 | 19 |
| 39 | 9b | visible | 1-15/1-12 | 47 | 0 | 22 |
| 40 | 9c | visible | 2-17/1-7 | 29 | 0 | 17 |
| 41 | 10a | visible | 1-20/1-18 | 64 | 0 | 33 |
| 42 | 10b | visible | 1-39/1-21 | 82 | 2 | 42 |
| 43 | 11a | visible | 1-12/1-8 | 28 | 0 | 14 |
| 44 | 11b | visible | 1-23/1-14 | 54 | 1 | 17 |
| 45 | 11c | visible | 1-16/1-6 | 32 | 1 | 9 |
| 46 | 12a | visible | 1-16/1-14 | 46 | 0 | 18 |
| 47 | 12b | visible | 1-17/1-10 | 34 | 0 | 19 |
| 48 | 12c | visible | 1-69/1-23 | 441 | 0 | 65 |
| 49 | 12d | visible | 1-17/1-21 | 67 | 0 | 26 |
| 50 | 15ATHTGPL-1 | hidden | 2-45/1-25 | 229 | 44 | 18 |
| 51 | 15BTHTGPL-2 | visible | 2-46/1-26 | 365 | 0 | 38 |
| 52 | 15CTHTGPL-3 | hidden | 1-44/1-31 | 416 | 0 | 30 |
| 53 | Tổng hợp CN 18 | hidden | 1-293/1-18 | 1.679 | 0 | 26 |
| 54 | 13a | visible | 1-10/1-22 | 60 | 0 | 22 |
| 55 | 13b | visible | 1-19/1-25 | 77 | 0 | 27 |
| 56 | 14a | visible | 1-11/1-13 | 32 | 0 | 16 |
| 57 | 14b | visible | 1-19/1-20 | 62 | 0 | 21 |
| 58 | 15a | visible | 1-32/1-26 | 198 | 69 | 27 |
| 59 | 15b | visible | 1-32/1-19 | 96 | 0 | 28 |
| 60 | 15c | visible | 1-21/1-19 | 135 | 0 | 36 |
| 61 | 16a | visible | 1-12/1-13 | 41 | 0 | 16 |
| 62 | 16b | visible | 1-12/1-13 | 41 | 0 | 16 |
| 63 | 16c | visible | 1-12/1-12 | 39 | 0 | 26 |
| 64 | 16d | visible | 1-12/1-13 | 41 | 0 | 16 |
| 65 | 16e | visible | 1-12/1-10 | 28 | 0 | 12 |
| 66 | 17 | visible | 1-27/1-15 | 89 | 0 | 42 |
| 67 | 17THCN | hidden | 1-15/1-10 | 50 | 2 | 19 |
| 68 | 18a | visible | 1-12/1-13 | 37 | 0 | 22 |
| 69 | 18b | visible | 1-26/1-18 | 96 | 0 | 33 |
| 70 | 18c | visible | 1-40/1-18 | 124 | 0 | 31 |
| 71 | 18d | visible | 2-25/1-20 | 77 | 0 | 29 |
| 72 | 19a | visible | 1-9/1-12 | 28 | 0 | 16 |
| 73 | 19b | visible | 1-55/1-15 | 79 | 0 | 31 |
| 74 | 20a | visible | 1-11/1-8 | 25 | 0 | 13 |
| 75 | 20b | visible | 1-17/1-13 | 47 | 0 | 15 |
| 76 | 21a | visible | 1-15/1-13 | 57 | 0 | 25 |
| 77 | 21b | visible | 1-21/1-16 | 62 | 1 | 28 |

### 5.4. Header và table patterns

Các template có những pattern chung nhưng không đồng nhất:

- title và metadata có thể nằm trên cùng hoặc ngoài table;
- header thường 2–6 tầng, dùng merge ngang/dọc;
- leaf column đôi khi chỉ có mã `(1)`, `(2)`, ...; semantic đầy đủ phải ghép toàn bộ ancestor path;
- row label có thể là `Tổng số`, `I`, `II`, `1`, `2`, dấu `-`, dấu ba chấm hoặc tên đơn vị;
- có sheet một hàng dữ liệu và sheet nhiều section/subtable;
- note, chữ ký và bảng thuyết minh có thể nằm dưới table chính;
- một số sheet có nhiều table candidate hoặc bảng tổng hợp lặp lại theo cấp đơn vị;
- style, border và merge là tín hiệu region/header mạnh, nhưng không đủ để quyết định semantic.

`Biểu cả nước` và `Biểu xã, sở, bộ ngành` cung cấp mapping vận hành giữa mã biểu, kỳ báo cáo, đơn vị gửi/nhận, bảng fact và function tổng hợp. Đây là metadata hữu ích để tạo candidate index, nhưng các tên bảng/function là dữ liệu triển khai cụ thể, không được hard-code vào model.

### 5.5. Formulas

449 formula xuất hiện chủ yếu trong các sheet tổng hợp/ẩn và một số template. Pattern gồm:

- cộng cột/hàng: `H5=I5+J5`, `A22=B22+C22+F22+G22`;
- tổng vùng: `SUM(B25:B58)`;
- tỷ lệ phần trăm: `(O9/(O9+P9))*100`;
- cộng nhiều section có xử lý ô trống bằng `IF(OR(...))`;
- lookup metadata: `VLOOKUP(...,'Quy trình'!...)`;
- nối mã: `Q20&R20`.

Có dấu hiệu formula không đáng tin tuyệt đối:

- formula chỉ còn `SUM` mà không có range;
- tham chiếu dạng `E$` thiếu row;
- công thức hằng như `198/21`;
- shared formula continuation có node `<f>` rỗng và phải resolve từ master formula;
- cached value có thể cũ nếu workbook chưa recalculate.

Pipeline phải giữ cả `raw_formula`, `cached_value`, `computed_value` và provenance. Không thực thi formula tùy ý bằng `eval`; chỉ hỗ trợ allow-list hàm cần thiết hoặc coi formula là tín hiệu cấu trúc.

### 5.6. Đối chiếu với rule SQL

Workbook có 62 template biểu nhập thông thường. SQL gán rule cho 54 mã. Tám template không có mã tương ứng trong script:

```text
6c, 6d, 7, 9c, 11a, 17, 19b, 20a
```

Điều này không tự động có nghĩa tám biểu thiếu validation: rule có thể nằm ở JSON hiện tại, JavaScript đặc thù hoặc DB khác. Tuy nhiên đây là checklist bắt buộc khi snapshot schema và viết regression test.

Mã workbook dùng cả `1a` và metadata `01a/...`; SQL cũng hỗ trợ biến thể thêm/bỏ số 0 đầu. Normalizer cần tách:

- base code (`01a` ↔ `1a`);
- suffix lĩnh vực (`/TP/TĐ-BH`);
- part (`I`, `II`);
- level/summary (`TH`, chữ hoa/thường);
- period/action level.

### 5.7. Ví dụ mapping 01a

Mapping không được dựa riêng vào vị trí A:I. Candidate features cho mỗi cột gồm:

```text
normalized leaf text
+ full ancestor header path
+ unit
+ ordinal marker (1)..(9)
+ neighboring headers
+ inferred type
+ formula/rule relations
+ DocType/Form context
```

Với hai workbook mẫu, rule của nhóm 1a xác nhận ba quan hệ tổng và hai cảnh báo quan hệ `(8) <= (2)`, `(9) <= (3)`. Đây là bằng chứng tốt để rerank candidate, nhưng rule không được dùng để “ép” mapping nếu header semantic mâu thuẫn.

## 6. Kết quả Handsontable mong đợi

Đầu ra sau phân tích/mapping phải là contract trung gian, chưa ghi DB:

```json
{
  "documentContext": {
    "documentCopyId": 0,
    "documentId": "...",
    "docTypeId": "...",
    "formId": "...",
    "schemaVersion": "..."
  },
  "tables": [
    {
      "sheet": "...",
      "region": "A3:I8",
      "headerRows": [3, 4, 5, 6, 7],
      "dataRows": [8],
      "fieldMappings": [
        {
          "sourceHeaderPath": ["..."],
          "sourceColumn": "A",
          "targetField": "server-resolved-field-key",
          "confidence": 0.0,
          "method": "exact|normalized|fuzzy|embedding|llm",
          "reasons": []
        }
      ],
      "sourceData": [],
      "valueData": [],
      "validation": { "errors": [], "warnings": [] }
    }
  ]
}
```

Sau khi người dùng xác nhận, `.NET ImportDocument` mới chuyển contract này thành đúng `DocumentContent.SourceData` và `ValueData` theo thứ tự `FormConfig.columns[].data`. `FormConfig`/`FormStyle` không được AI tự chế lại nếu schema hiện tại đã tồn tại.

## 7. Yêu cầu cho Excel analyzer

1. Kiểm tra signature ZIP/Open XML thay vì chỉ extension.
2. Giới hạn byte, sheet, physical cell, non-empty cell, merge, shared string, formula và thời gian xử lý.
3. Không đọc/giải nén media, macro, OLE hoặc external link vào môi trường thực thi.
4. Tính non-empty bounds thay vì tin `dimension`/max row.
5. Tách sheet metadata/control khỏi table nghiệp vụ bằng classifier có giải thích.
6. Phát hiện region từ mật độ ô + border/style + merge + text/type transition.
7. Dựng header tree và full header path cho từng leaf.
8. Nhận diện row hierarchy và nhiều table trong một sheet.
9. Giữ provenance ở cấp workbook/sheet/cell/range.
10. Bảo toàn raw value, displayed/cached value và formula riêng biệt.
11. Loại secret/PII khỏi log, prompt, dataset và telemetry.
12. Không hard-code filename, sheet name hay `header_row = 8`.

## 8. Bộ test rút ra từ ba workbook

| Test | Kỳ vọng |
|---|---|
| Cùng bảng, khác tên sheet | Nhận cùng DocType/Form candidate |
| Thiếu title/footer | Vẫn nhận đúng table từ header path |
| Ô nhiễu K8 ngoài A:I | Không tạo DataField giả |
| Header nhiều tầng/merge | Dựng đúng 9 leaf paths của 01a |
| Styled blank tới row 1001 | Không sinh hàng rỗng |
| Workbook 77 sheet | Phân tích trong quota, trả progress |
| Sheet hidden | Ghi nhận nhưng không tự import nếu chưa có policy |
| Sheet tài khoản | Phân loại nhạy cảm và loại khỏi dataset/log |
| Formula shared/malformed | Không crash, không `eval`, ghi warning |
| Mã `01a`/`1a` | Normalize nhưng vẫn giữ original |
| Mục I/II | Không trộn form/section |
| Tám biểu chưa thấy SQL rule | Gắn cờ schema coverage, không tự bịa rule |

## 9. Kết luận Excel analysis

Hai file nhỏ chứng minh nhu cầu generalization trước biến thể tên sheet và thiếu metadata. Workbook 77 sheet chứng minh bài toán thật gồm phân loại sheet, nhiều region, header tree, template/summary distinction, công thức, dữ liệu vận hành và dữ liệu nhạy cảm. Baseline chỉ map theo cột hoặc chọn sheet thủ công sẽ không đủ; tuy nhiên AI cũng không được thay thế schema/rule. Kiến trúc phù hợp là analyzer xác định cấu trúc trước, candidate retrieval từ eForm sau, rồi semantic reranking có confidence và xác nhận người dùng.
