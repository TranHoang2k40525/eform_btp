# THIẾT KẾ DATASET VÀ HUẤN LUYỆN
# EFormExcelStructureExtractor-v1

## 1. Mục tiêu học máy

Mô hình học nhận diện cấu trúc sheet Excel, không học ánh xạ sang DataField và không học sinh lại value.

Đơn vị dự đoán chính:

```text
Mỗi row/cell → vai trò cấu trúc
```

Từ các vai trò đó, hậu xử lý dựng:

```text
table range + header range + code row + data range + footer range
```

Giá trị output được copy lại từ workbook theo tọa độ model đã chọn.

---

## 2. Nguồn dữ liệu

### 2.1. Kho Raw hiện có

Kiểm kê hiện tại:

| Thuộc tính | Số lượng |
|---|---:|
| Workbook | 1.232 |
| Nhận diện được DocTypeCode | 1.231 |
| DocTypeCode | 27 |
| 09a | 722 |
| 05b | 139 |
| 01c | 46 |
| Các mã còn lại | Phân bố từ 1 đến 38 file/mã |

DocTypeCode chỉ dùng để báo cáo độ phủ và phân tầng đánh giá; model không cần DocType để hiểu DataField.

### 2.2. Workbook đặc biệt cần giữ trong test/challenge

- File một dòng, header nhiều tầng như `09a`.
- File phân cấp dài như `04c`.
- File một sheet chứa nhiều bảng như `01d`.
- Workbook tổng hợp 77 sheet, 205 table region, 3.006 merge.
- File có formula, percentage, date, mã text có số 0 đầu.
- File có hidden sheet, footer dài, dòng trống giữa bảng, cột ghi chú.

---

## 3. Không dùng 1.232 file như 1.232 cấu trúc độc lập

Nhiều file chỉ khác:

- Tên đơn vị.
- Kỳ báo cáo.
- Số liệu.
- Hậu tố `copy`.

Nhưng header, merge và bố cục giống nhau. Nếu chia ngẫu nhiên, cùng một template có thể xuất hiện ở Train và Test, tạo data leakage.

### 3.1. Layout fingerprint

Fingerprint đề xuất gồm:

```json
{
  "sheet_count": 1,
  "used_range_shape": [20, 9],
  "merge_geometry": ["A3:C3", "A4:B4"],
  "header_depth": 4,
  "column_codes": ["(1)", "(2)", "(3)"],
  "normalized_header_tokens": ["tong so", "trong do"],
  "style_signature": "..."
}
```

Hash fingerprint tạo `layout_family_id`. Có thể dùng clustering gần đúng để gom các template chỉ khác một dòng title.

### 3.2. Chia split

Khuyến nghị:

| Split | Tỷ lệ family | Mục đích |
|---|---:|---|
| Train | 70% | Học tham số |
| Validation | 15% | Chọn checkpoint/threshold |
| Test | 15% | Báo cáo cuối |
| Challenge | Bộ riêng | File cực lớn, layout hiếm, lỗi và OOD |

Mọi workbook/sheet/table của một family phải ở cùng split. Không điều chỉnh Test sau khi xem kết quả cuối.

---

## 4. Schema nhãn

### 4.1. Manifest workbook

```json
{
  "workbook_id": "sha256:...",
  "file_name": "...xlsx",
  "relative_path": "Raw/...xlsx",
  "layout_family_id": "layout-09a-v1",
  "doc_type_code": "09a",
  "split": "train",
  "sheet_count": 1,
  "enabled": true
}
```

### 4.2. Label theo sheet

```json
{
  "workbook_id": "sha256:...",
  "sheet": "9a",
  "max_row": 20,
  "max_column": 9,
  "tables": [
    {
      "table_id": "T1",
      "start_row": 3,
      "end_row": 7,
      "start_column": 1,
      "end_column": 9,
      "header_start_row": 3,
      "header_end_row": 6,
      "code_row": 6,
      "data_start_row": 7,
      "data_end_row": 7
    }
  ],
  "verification_method": "human",
  "verified": true
}
```

### 4.3. Label theo row

```json
{
  "workbook_id": "sha256:...",
  "sheet": "9a",
  "row": 6,
  "role": "COLUMN_CODE",
  "table_id": "T1",
  "verified": true
}
```

### 4.4. Label theo cell

Cell label chỉ cần cho các trường hợp khó hoặc cho head multi-task:

```json
{
  "workbook_id": "sha256:...",
  "sheet": "9a",
  "row": 3,
  "column": 1,
  "role": "HEADER",
  "table_id": "T1",
  "merge_anchor": true,
  "verified": true
}
```

### 4.5. Expected preview

Mỗi golden workbook cần một JSON kết quả mong đợi gồm:

- Table range.
- Header matrix.
- Merge definitions.
- Column code/header/header_path.
- Rows và source coordinate.
- Formula/type/display value.

Expected preview là test end-to-end quan trọng nhất.

---

## 5. Quy trình tạo nhãn

```text
Raw workbook
  ↓ Parser/rule hiện tại
Silver table/header/data suggestion
  ↓ Gom theo layout family
Người duyệt một mẫu đại diện
  ↓ Áp dụng cho các file cùng fingerprint
Spot-check ngẫu nhiên và file khác biệt
  ↓
Gold structure labels
```

### 5.1. Điều kiện gold

Chỉ coi là gold khi:

```json
{
  "verified": true,
  "verification_method": "human|reviewed|curated"
}
```

Rule hoặc model tự gán phải là `silver`, không được tự nâng thành gold.

### 5.2. Chiến lược giảm công duyệt

- Duyệt theo layout family thay vì từng workbook.
- Hiển thị overlay màu TITLE/HEADER/DATA/FOOTER.
- Cho sửa table boundary bằng kéo chọn.
- Áp dụng label cho các file fingerprint giống hoàn toàn.
- Spot-check tối thiểu một số file ở mỗi đơn vị/kỳ báo cáo.

---

## 6. Data augmentation

Chỉ augmentation cấu trúc, không bịa số liệu nghiệp vụ:

- Chèn/xóa một dòng trống phía trên bảng.
- Chèn title hoặc metadata giả vô hại.
- Thay đổi chiều cao dòng/độ rộng cột.
- Thay style bold/alignment nhưng giữ nội dung.
- Thêm footer/note từ tập mẫu đã tách.
- Ẩn/hiện sheet phụ.
- Thay đổi mật độ ô trống hợp lệ.
- Thêm một cột ghi chú ngoài bảng.

Không nên:

- Đảo cột làm thay đổi ý nghĩa template nếu expected output không cập nhật.
- Thay số liệu bằng chuỗi ngẫu nhiên làm mất kiểu.
- Dùng augmentation của Test để tạo Train.
- Tạo merged cells không hợp lệ.

---

## 7. Feature engineering

### 7.1. Cell features

| Nhóm | Feature |
|---|---|
| Vị trí | row, column, relative row/column, distance to used-range edge |
| Nội dung | char pattern, token count, text length, letter/digit ratio |
| Kiểu | blank, text, integer, decimal, date, month, year, percentage, boolean, formula |
| Bố cục | merged, rowspan, colspan, merge anchor |
| Style | bold, italic, alignment, border count, fill category, number format |
| Pattern | column code, Roman code, decimal hierarchy, report-title/footer keyword |

### 7.2. Row aggregate features

- Non-empty cell count.
- Numeric/text/formula/blank ratio.
- Số merge bắt đầu/kết thúc.
- Tỷ lệ ô bold/centered.
- Có dãy mã cột liên tục không.
- Độ tương đồng hình thái với dòng trước/sau.

### 7.3. Bảo vệ dữ liệu

- Có thể hash hoặc vocabulary hóa tên đơn vị nếu không cần cho cấu trúc.
- Không log toàn bộ value ở môi trường production.
- Model feature ưu tiên pattern/type, không học giá trị báo cáo cụ thể.

---

## 8. Kiến trúc model

### 8.1. Phiên bản v1

```text
Cell Feature Encoder
  - categorical embeddings
  - numeric projection
  - char/token encoder nhỏ
        ↓
Pooling theo row
        ↓
Transformer Encoder 2-4 lớp
        ↓
Row-role classification head
Boundary classification head
Optional cell-role head
```

Một model có thể có nhiều output head nhưng vẫn là một checkpoint duy nhất.

### 8.2. Loss

```text
TotalLoss = 1.0 * RowRoleLoss
          + 1.5 * BoundaryLoss
          + 0.5 * CellRoleLoss
          + 0.1 * SequenceConsistencyLoss
```

Hệ số phải được chọn trên Validation. Dùng class weights để `DATA`/`BLANK` không lấn át `COLUMN_CODE`/`TABLE_SEPARATOR`.

### 8.3. Windowing

Với sheet dài:

- Chia window 128-256 dòng với overlap.
- Giữ row index tuyệt đối.
- Hợp nhất xác suất ở vùng overlap.
- Không chia giữa một merge range nếu tránh được.

Với sheet rộng:

- Giữ aggregate feature của toàn dòng.
- Chỉ encode chi tiết tối đa N cell đại diện hoặc chia block cột.
- Table reconstruction vẫn dùng toàn bộ workbook gốc.

---

## 9. Huấn luyện

### 9.1. Quy trình

1. Kiểm tra schema và `verified`.
2. Fit vocabulary/normalizer chỉ trên Train.
3. Tạo dataloader theo workbook/layout family.
4. Train với balanced sampling.
5. Đánh giá Validation sau mỗi epoch.
6. Early stop theo whole-table exact match và boundary score.
7. Chọn threshold confidence/OOD trên Validation.
8. Khóa checkpoint.
9. Chạy Test đúng một lần để lập báo cáo.
10. Export ONNX và benchmark CPU.

### 9.2. Reproducibility

Mỗi model release phải lưu:

- Git commit.
- Dataset version/hash.
- Split manifest.
- Seed.
- Feature config.
- Hyperparameters.
- Label map.
- Threshold.
- Metric theo layout family/DocType.
- Danh sách failure case.

---

## 10. Đánh giá

### 10.1. Metric cấu trúc

| Metric | Ý nghĩa |
|---|---|
| Row-role macro F1 | Không để lớp phổ biến che lớp hiếm |
| Table region IoU/F1 | Vùng bảng được chọn đúng mức nào |
| Header boundary exact | Cả start và end đều đúng |
| Data boundary exact | Không thiếu/thừa dòng data |
| Column count exact | Không mất/thêm cột |
| Merge F1 | Merge header dựng đúng |
| Whole-table exact | Toàn bộ cấu trúc đúng cùng lúc |

### 10.2. Metric an toàn dữ liệu

| Metric | Yêu cầu |
|---|---:|
| Raw value preservation | 100% |
| Display value preservation | 100% khi không chủ động format lại |
| Formula preservation | 100% công thức thuộc vùng output |
| Source coordinate coverage | 100% output cell |

### 10.3. Báo cáo phân tầng

Phải báo cáo riêng:

- Single-sheet và multi-sheet.
- Single-table và multi-table.
- Header một tầng và nhiều tầng.
- Layout phổ biến và layout hiếm.
- Seen-style và unseen-family Test.
- Workbook nhỏ, trung bình và lớn.

Không dùng accuracy tổng duy nhất vì 09a chiếm phần lớn Raw.

---

## 11. Inference và hậu xử lý

```text
Workbook bytes
  ↓ Kiểm tra file/zip bomb/path/formula policy
openpyxl đọc cells + styles + merges
  ↓
Feature extraction
  ↓
ONNX model inference
  ↓ probabilities
Constrained decoder
  ↓
Table regions hợp lệ
  ↓
Copy cells từ workbook gốc
  ↓
PreviewData JSON
```

Constrained decoder phải chặn chuỗi vô lý và đảm bảo:

- `header_start <= header_end < data_start <= data_end`.
- Range nằm trong used range.
- Merge được cắt hoặc giữ theo chính sách rõ ràng.
- Không tạo source coordinate không tồn tại.
- Không tự tuyên bố thành công khi confidence thấp.

---

## 12. Fallback

Nếu model không chắc chắn, response vẫn trả workbook/sheet metadata và issue:

```json
{
  "code": "AMBIGUOUS_DATA_START",
  "message": "Có nhiều vị trí có thể là dòng bắt đầu dữ liệu",
  "candidates": [7, 9],
  "requires_user_selection": true
}
```

Giao diện cho người dùng chọn:

- Sheet.
- Header start/end.
- Data start/end.
- Table range.

Correction được lưu thành label mới sau khi loại bỏ dữ liệu nhạy cảm không cần thiết.

---

## 13. Acceptance checklist

- [ ] Split theo layout family, không leakage.
- [ ] Gold labels có provenance.
- [ ] Có negative/OOD/challenge set.
- [ ] Model không nhận DataField/FormConfig.
- [ ] Model không sinh lại raw value.
- [ ] Test tách biệt và không dùng chọn checkpoint.
- [ ] Có metric theo family/DocType.
- [ ] Value/formula/source coordinate đạt yêu cầu bảo toàn.
- [ ] Có fallback manual.
- [ ] Export model local và benchmark CPU.
- [ ] Có model card và danh sách giới hạn.
