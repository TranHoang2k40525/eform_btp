# BÁO CÁO PHÂN TÍCH CHI TIẾT
# AI TRÍCH XUẤT CẤU TRÚC VÀ DỮ LIỆU EXCEL PHỤC VỤ PREVIEW eFORM

**Tên mô hình đề xuất:** `EFormExcelStructureExtractor-v1`  
**Loại hệ thống:** mô hình AI local kết hợp parser Excel và hậu xử lý xác định  
**Phạm vi:** từ file Excel đến dữ liệu xem trước; dừng trước nút **Nhập dữ liệu**  
**Không sử dụng:** LLM, API AI bên ngoài, semantic mapping sang DataField

---

## 1. Tóm tắt điều hành

Hệ thống cần xây không phải chatbot và không phải mô hình sinh văn bản. Đây là một bộ trích xuất cấu trúc bảng Excel: nhận diện sheet/vùng bảng/header nhiều tầng/dòng dữ liệu/footer, sau đó để chương trình sao chép nguyên các giá trị ô thành JSON phục vụ màn hình preview Handsontable.

Mô hình không nhận `DocumentContent`, không hiểu `FormConfig`, không chọn DataField và không ghi dữ liệu vào eForm. Sau khi người dùng xem preview và bấm **Nhập dữ liệu**, giao diện hiện hữu mới thực hiện đối chiếu với biểu, kiểm tra required/readonly/rule và tạo `SourceData`/`ValueData`.

Kiến trúc này tận dụng đúng điểm mạnh của AI — nhận diện cấu trúc có biến thể — đồng thời giữ các thao tác cần chính xác tuyệt đối bằng code thông thường. Đặc biệt, số liệu báo cáo không được model tạo lại nên tránh nguy cơ đổi số hoặc bỏ ô.

---

## 2. Bài toán thực tế

### 2.1. Đầu vào

Các file `.xlsx/.xlsm` có dạng tương tự kho `Data/Raw`:

- Có thể có nhiều sheet.
- Có tiêu đề báo cáo và thông tin kỳ báo cáo phía trên bảng.
- Header có nhiều tầng và merged cells.
- Có dòng mã cột `A`, `B`, `(1)`, `(2)`, ...
- Có các dòng chỉ tiêu như `I`, `1`, `1.1`.
- Có footer, ghi chú, chữ ký hoặc bảng phụ phía dưới.
- Một sheet có thể có nhiều bảng.
- Giá trị có thể là number, text, date, percentage, boolean hoặc formula.

### 2.2. Đầu ra mong đợi

Trước khi người dùng bấm **Nhập dữ liệu**, hệ thống cần trả:

```json
{
  "schema_version": "1.0",
  "file_name": "bao-cao.xlsx",
  "sheets": [
    {
      "sheet_name": "9a",
      "tables": [
        {
          "table_id": "9a-table-1",
          "range": "A3:I7",
          "header_start_row": 3,
          "header_end_row": 6,
          "data_start_row": 7,
          "data_end_row": 7,
          "header_rows": [],
          "merged_cells": [],
          "columns": [],
          "rows": [],
          "confidence": 0.98,
          "issues": []
        }
      ]
    }
  ]
}
```

Đây là `PreviewData`, không phải `ValueData` eForm. Các dòng `rows` vẫn là mảng theo thứ tự cột nguồn để không mất dữ liệu khi nhiều header trùng tên.

---

## 3. Phân tích hệ thống cũ

### 3.1. Hai luồng Excel khác nhau

Hệ thống hiện tại có hai luồng không nên trộn lẫn:

1. **Import Excel để thiết kế biểu:** controller đọc vùng header/data do quản trị viên chọn và sinh `DefineFieldJson`, `DefineTypeJson`, `DefineValueJson`, sau đó tạo `FormConfig`.
2. **Import dữ liệu vào biểu đã có:** trang `document-import-excel*.html` đọc Excel, lấy cấu hình biểu từ `DocumentContents`, ghép dữ liệu vào các field rồi gửi `IMPORT_EXCEL_DONE`.

Dự án AI mới chỉ thay thế phần đọc và nhận diện bảng của luồng thứ hai.

### 3.2. Cách hệ thống cũ xác định dữ liệu

Trong luồng document import, số dòng header được suy ra từ:

```javascript
FormConfig.extra.headerSetting.length
```

Sau đó hệ thống:

1. Bỏ số dòng đầu tương ứng.
2. Lấy các cột eForm nhìn thấy từ `FormConfig.header`.
3. Tách ID thật bằng `fieldKey.split("!!")[0]`.
4. Ghép value Excel vào field theo vị trí cột.
5. Kiểm tra template code, số dòng, required và các rule.
6. Hiển thị Handsontable.
7. Khi xác nhận, gửi `rows` đã có DataField ID về `document.js`.

Hệ thống cũ không dùng giá trị như `2616` để hiểu ý nghĩa cột. Giá trị chỉ được đưa vào cột ở cùng vị trí và được validation sau đó.

### 3.3. Điểm mạnh của hệ thống cũ

- Đơn giản, nhanh và xác định khi file đúng template.
- Không cần dataset hoặc huấn luyện.
- Giá trị được đọc trực tiếp, không bị AI tạo lại.
- Đã có sẵn mapping, required, readonly, sum rule và luồng `IMPORT_EXCEL_DONE`.

### 3.4. Giới hạn của hệ thống cũ

- Phụ thuộc `DocumentContent/FormConfig` ngay từ lúc tách bảng.
- Giả định số dòng header Excel bằng số dòng header eForm.
- Dễ cắt sai khi có thêm tiêu đề, kỳ báo cáo hoặc ghi chú.
- Khó phát hiện nhiều bảng trong cùng sheet.
- Khó xử lý file có footer dài hoặc dòng trống bất thường.
- Preview thường đã gắn với biểu đích, làm khó phân biệt lỗi đọc Excel và lỗi mapping.
- Hai biến thể import thường/handsel có hành vi kiểm tra sheet/template không hoàn toàn đồng nhất.

---

## 4. Hướng AI mới

### 4.1. Phân chia trách nhiệm

| Thành phần | Trách nhiệm |
|---|---|
| Thư viện Excel | Đọc chính xác cell, type, formula, merge, style, hidden sheet |
| Model local | Dự đoán vai trò dòng/ô và ranh giới bảng |
| Hậu xử lý | Tạo table range, header path, merge, rows và cảnh báo |
| Preview UI | Hiển thị nội dung nguồn, cho người dùng chọn/sửa vùng |
| Giao diện eForm cũ | Mapping theo cấu hình biểu, validation và import sau xác nhận |

### 4.2. Luồng chính

```text
Người dùng chọn Excel
        ↓
Parser đọc workbook thành cell features
        ↓
EFormExcelStructureExtractor-v1
        ↓
Nhãn TITLE / HEADER / CODE / DATA / FOOTER
        ↓
Hậu xử lý xác định và copy nguyên value
        ↓
PreviewData JSON
        ↓
Handsontable hiển thị giống nội dung Excel
        ↓
Người dùng bấm "Nhập dữ liệu"
        ↓
Logic eForm cũ mapping + validation + IMPORT_EXCEL_DONE
```

### 4.3. Vì sao model không sinh giá trị

Mô hình chỉ dự đoán cấu trúc. Với một ô nguồn `(sheet="9a", row=7, col=1)` có giá trị `2616`, hậu xử lý đọc lại chính ô đó và đặt `2616` vào output. Model không có quyền thay `2616` bằng token dự đoán.

Nguyên tắc:

```text
Model chọn ô nào thuộc bảng.
Code quyết định giá trị chính xác của ô đó.
```

---

## 5. Mô hình AI đang xây là gì?

### 5.1. Tên và nhiệm vụ

`EFormExcelStructureExtractor-v1` là mô hình phân loại chuỗi dòng/ô trong sheet Excel.

Nó trả lời ba câu hỏi:

1. Bảng nằm ở đâu?
2. Dòng/ô đang có vai trò gì?
3. Header kết thúc và dữ liệu bắt đầu ở đâu?

Nó không trả lời “cột này thuộc DataField nào?”.

### 5.2. Kiến trúc đề xuất

Một model multi-task duy nhất:

```text
Cell features
  ↓ Cell Feature Encoder
Row representation
  ↓ Transformer Encoder 2-4 lớp
Contextual row/cell representation
  ├─ Row-role head
  ├─ Cell-role head
  └─ Boundary head
```

Quy mô mục tiêu nhỏ để có thể export ONNX và chạy CPU nội bộ. Không sử dụng LLM hoặc gọi mạng.

### 5.3. Nhãn dự đoán

| Nhãn | Ý nghĩa |
|---|---|
| `TITLE` | Tên biểu/tên báo cáo |
| `METADATA` | Đơn vị, kỳ báo cáo, biểu số |
| `HEADER` | Header thường hoặc header nhiều tầng |
| `COLUMN_CODE` | Dòng A, B, (1), (2), ... |
| `DATA` | Dòng dữ liệu thực tế |
| `NOTE` | Ghi chú không phải data |
| `FOOTER` | Chữ ký, người lập biểu, hướng dẫn cuối |
| `BLANK` | Dòng hoặc ô rỗng |
| `TABLE_SEPARATOR` | Ranh giới giữa các bảng |

### 5.4. Feature

- Row/column index tương đối.
- Text pattern, độ dài, tỷ lệ chữ/số.
- Kiểu dữ liệu Excel.
- Formula và number format.
- Merged span và vị trí trong merge.
- Bold, alignment, border, fill.
- Số ô không rỗng trong dòng.
- Tỷ lệ numeric/text/blank.
- Pattern `A`, `B`, `(1)`, `(2)`, `I`, `1`, `1.1`.
- Từ khóa cấu trúc như `Biểu số`, `Kỳ báo cáo`, `Người lập biểu`, `Ghi chú`.
- Ngữ cảnh các dòng lân cận.

Actual report values không được dùng như semantic feature; chỉ dùng loại giá trị và hình thái.

---

## 6. So sánh phương án mô hình

| Phương án | Phù hợp | Hạn chế | Quyết định |
|---|---|---|---|
| Rule-only | Rất tốt cho template cố định, baseline nhanh | Khó bao phủ biến thể phức tạp | Giữ làm baseline/fallback |
| BGE-M3/PhoBERT retrieval | Tốt cho ghép ngữ nghĩa header với DataField | Không giải quyết trực tiếp table boundary | Không chọn cho phạm vi mới |
| LayoutLMv3 từ ảnh | Hiểu bố cục tài liệu scan | Excel đã có cell/merge/type; render ảnh làm mất metadata | Không chọn |
| TAPAS/TaBERT | Hiểu nội dung của bảng đã được tách | Giả định bảng đã tồn tại | Không chọn |
| LLM sinh JSON | Linh hoạt | Nặng, có thể đổi số, cần model lớn/API | Không chọn |
| Row/cell classifier đơn giản | Nhẹ, dễ chạy CPU | Context liên dòng hạn chế | Baseline ML |
| Multi-task Transformer nhỏ | Học ngữ cảnh sheet, một model, chạy local | Cần nhãn cấu trúc tốt | Hướng chính |

---

## 7. Vì sao cần AI thay vì chỉ giữ hệ thống cũ?

| Tình huống | Hệ thống cũ | AI trích xuất cấu trúc | Lợi ích thực tế |
|---|---|---|---|
| Header thêm/bớt dòng | Dễ lấy nhầm data start | Tự dự đoán header/data boundary | Giảm cấu hình thủ công |
| Có tiêu đề/kỳ báo cáo phía trên | Phụ thuộc header count từ FormConfig | Nhận diện TITLE/METADATA | Không cắt nhầm metadata vào bảng |
| Header merged nhiều tầng | Phụ thuộc template khớp | Dùng merge + context để dựng header | Preview trung thực hơn |
| Nhiều bảng trong một sheet | Khó phân tách | Trả danh sách table region | Người dùng chọn đúng bảng |
| Nhiều sheet | Thường phải chọn thủ công | Phân tích và xếp confidence từng sheet | Giảm thao tác |
| Footer/chữ ký/ghi chú | Có thể bị tính thành data | Nhận diện NOTE/FOOTER | Row count chính xác |
| Biểu mới nhưng cùng quy ước | Có thể phải cấu hình lại cách cắt | Model học cấu trúc chung, không phụ thuộc DataField | Dễ mở rộng |
| Kiểm tra lỗi | Lỗi đọc và mapping bị trộn | Preview nguồn tách biệt | Debug rõ bước |
| Bảo mật | Không có dịch vụ ngoài | Model local, không gửi dữ liệu ra Internet | Phù hợp dữ liệu nội bộ |
| Độ chính xác value | Đọc trực tiếp | Vẫn đọc trực tiếp, model không sinh value | Không đánh đổi an toàn số liệu |

AI không cần thiết nếu mọi file luôn đúng tuyệt đối một template. AI tạo giá trị khi cần bao phủ các biến thể Raw có cùng quy ước nghiệp vụ nhưng khác vị trí, số dòng header, merge, sheet hoặc footer.

---

## 8. Dữ liệu hiện có và ý nghĩa

Kiểm kê tài liệu cũ ghi nhận:

- 1.232 workbook Raw.
- 1.231 file nhận diện được mã biểu.
- 27 DocTypeCode.
- 09a chiếm 722 file; 05b chiếm 139 file.
- Một số DocType chỉ có 1-6 file.
- Workbook tổng hợp đã kiểm tra có 77 sheet, 205 vùng bảng và 3.006 merged ranges.

Điều này cho thấy số file lớn nhưng số layout độc lập có thể nhỏ hơn nhiều. Không được coi 722 file 09a là 722 cấu trúc khác nhau. Cần tạo `layout_fingerprint` và duyệt theo family.

Phân bố mất cân bằng cũng có nghĩa accuracy tổng có thể rất cao chỉ vì model làm tốt 09a nhưng thất bại ở các biểu hiếm. Báo cáo bắt buộc có macro metric theo layout/DocType.

---

## 9. Khả năng áp dụng cho tất cả loại biểu

### Có thể áp dụng chung khi

- File là spreadsheet có cell grid thật.
- Header và data nằm trong vùng bảng tương đối liên tục.
- Merge/style/type còn được lưu trong workbook.
- Cấu trúc tương tự các family đã train: biểu số, header, mã cột, data, footer.
- Biểu mới khác nội dung nhưng giữ quy ước bố cục thống kê.

### Không được hứa áp dụng tuyệt đối khi

- Excel chỉ chứa ảnh chụp bảng.
- File scan/PDF đổi đuôi.
- Sheet được mã hóa hoặc hỏng.
- Macro sinh bảng động chưa được chạy.
- Dữ liệu rải rác không có ranh giới bảng.
- Một ô chứa cả bảng dưới dạng text.
- Layout hoàn toàn ngoài phân phối huấn luyện.

Vì model học cấu trúc thay vì DataField, một biểu mới không nhất thiết yêu cầu train lại. Nhưng layout hoàn toàn mới phải được phát hiện OOD, cho người dùng chọn vùng thủ công và đưa correction vào dataset phiên bản sau.

---

## 10. PreviewData chi tiết

Mỗi column:

```json
{
  "source_column": 0,
  "excel_column": "A",
  "header": "Tổng số",
  "header_path": [
    "Chứng thực bản sao từ bản chính",
    "Số lượng bản sao được chứng thực (Bản)",
    "Tổng số"
  ],
  "column_code": "(1)",
  "value_type": "integer"
}
```

Mỗi cell có thể giữ hai biểu diễn:

```json
{
  "raw_value": 0.125,
  "display_value": "12,5%",
  "value_type": "percentage",
  "formula": null,
  "source": {"sheet": "9a", "row": 7, "column": 5}
}
```

`raw_value` dùng cho bước nhập; `display_value` dùng cho preview. Mã như `00123` phải được giữ là text. Công thức phải lưu riêng, không được trả chuỗi công thức như một số bình thường.

---

## 11. Tích hợp với giao diện cũ

API model đề xuất:

```http
POST /api/excel/extract
Content-Type: multipart/form-data
file=<workbook>
```

Không bắt buộc `documentId` hoặc `DocumentContent` cho bước extract. Nếu backend cần `documentId` để log request thì đó là metadata điều phối, không phải input của model.

Frontend thực hiện:

1. Nhận `PreviewData`.
2. Chọn sheet/table.
3. Render `header_rows`, `merged_cells`, `columns`, `rows`.
4. Cho người dùng điều chỉnh vùng khi confidence thấp.
5. Khi bấm **Nhập dữ liệu**, lấy `FormConfig` của biểu đang mở.
6. Lọc cột hidden/readonly theo logic hiện tại.
7. Kiểm tra mã cột/số cột/header theo chính sách giao diện.
8. Ghép `rows[source_column]` vào DataField theo logic cũ.
9. Chạy required/type/sum/cross-form rules.
10. Gửi `IMPORT_EXCEL_DONE`.

Model dừng ở bước 3-4.

---

## 12. Kết quả mong đợi và tiêu chí nghiệm thu

Các con số dưới đây là mục tiêu cần đo trên Test, không phải kết quả đã đạt:

| Chỉ số | Mục tiêu v1 |
|---|---:|
| Cell value preservation | 100% |
| Header text preservation sau chọn đúng vùng | 100% |
| Table detection F1 | >= 0,98 |
| Header boundary exact match | >= 0,95 |
| Data boundary exact match | >= 0,95 |
| Column count exact match | >= 0,98 |
| Whole-table exact match | >= 0,95 |
| Tỷ lệ file lỗi bị phát hiện thay vì trả thành công giả | 100% trong bộ negative test |

Ngoài accuracy, cần đo latency và memory. Benchmark cũ cho thấy table detection là phần tốn thời gian chính: bảng tổng hợp 77 sheet/205 region mất khoảng 7,85 giây; synthetic 10.000 dòng mất khoảng 0,42 giây. Đây là baseline tham khảo, không phải tốc độ model sau cùng.

---

## 13. Lợi ích

### Với người dùng

- Xem đúng nội dung file trước khi nhập.
- Biết model chọn sheet/vùng nào.
- Có cảnh báo thay vì nhập âm thầm sai.
- Giảm khai báo thủ công dòng header/data.

### Với đội phát triển

- Tách lỗi extract khỏi lỗi mapping/validation.
- Một model dùng chung cho nhiều DocType.
- Không phải cập nhật model khi DataField thay đổi.
- Có thể test model độc lập bằng workbook và expected preview.

### Với hệ thống

- Không thay đổi luồng ghi document hiện hữu.
- Không gửi dữ liệu ra dịch vụ bên ngoài.
- Không cho AI quyền sửa số liệu hoặc database.
- Có fallback về chọn vùng thủ công.

---

## 14. Rủi ro và giới hạn

| Rủi ro | Cách kiểm soát |
|---|---|
| Dữ liệu train thiên lệch 09a | Chia/đánh giá theo layout family, class weight, macro metric |
| Silver label từ rule có lỗi | Human review trước khi thành gold |
| Model cắt thiếu dòng | Boundary loss, challenge set, source coordinate, manual fallback |
| Công thức không có cached result | Giữ formula, cảnh báo, không bịa value |
| File cực lớn | Streaming, window/chunk, giới hạn sheet/row/cell |
| Layout ngoài phân phối | OOD confidence và bắt buộc người dùng chọn vùng |
| Header trùng tên | Rows dạng array + source_column, không dùng header làm JSON key |
| Mất số 0 đầu | Bảo toàn raw/display value và number format |

---

## 15. Kết luận

Hướng mới phù hợp với mục tiêu hiện tại hơn kiến trúc BGE/LLM mapping vì đầu ra cần thiết chỉ là dữ liệu preview trung thực. AI được giới hạn ở quyết định khó nhưng có thể học được — nhận diện cấu trúc bảng — còn mọi thao tác liên quan đến giá trị và document vẫn do code/giao diện hiện hữu xử lý.

Sản phẩm v1 thành công khi người dùng có thể đưa một file Raw vào, xem đúng sheet, header, merge và values trên giao diện, sửa lựa chọn khi cần, rồi tiếp tục bấm **Nhập dữ liệu** bằng luồng cũ mà model không phải biết biểu đích là gì.
