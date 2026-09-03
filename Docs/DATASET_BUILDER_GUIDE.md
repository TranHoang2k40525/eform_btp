# DatasetBuilder.ipynb — hướng dẫn chi tiết

## 1. Mục đích

Notebook biến Excel raw thành dữ liệu cho bài toán ánh xạ:

```text
Ngữ cảnh header Excel + DocTypeCode → DataField eForm
```

Nó không học các giá trị báo cáo như `0`, `12`, `500000`; các giá trị này chỉ dùng để suy luận kiểu dữ liệu.

## 2. Dữ liệu đầu vào

```text
Data/Raw/*.xlsx, *.xlsm
Data/Labels/eform_fields.jsonl
Data/Labels/mappings.jsonl (nếu đã có nhãn cũ)
```

Tên file raw có dạng `Tên đơn vị_DocTypeCode_Tên biểu.xlsx`. Ví dụ `_01d_` được tách thành `01d` bằng regex `_(\d{2}[a-z]?)_`; mã `17` cũng được hỗ trợ.

`eform_fields.jsonl` là schema field, ví dụ:

```json
{"data_field_id":"a3","field_name":"a3","field_title":"Số văn bản","doc_type_code":"01d","column_code":"(3)","data_type":"int"}
```

`DocumentContentId` đại diện chỉ là metadata, không phải ID của mọi báo cáo thực tế.

## 3. Luồng xử lý

```text
Raw Excel
  → lấy DocTypeCode từ tên file
  → đọc sheet, merged cell, header nhiều cấp
  → tìm dòng mã cột (1), (2), (3)
  → dựng header_path, sample_values, data_type
  → đối chiếu eform_fields
  → sinh candidate_fields
  → xác nhận target_data_field_id
  → verified=true
  → tạo Train/Validation/Test
```

## 4. Giải thích các cell

### Cell 1–3: cấu hình

Import thư viện, đặt `DATA_ROOT`, tạo `Raw`, `Labels`, `Train`, `Validation`, `Test`, thiết lập seed và giới hạn đọc.

### Cell 4: helper

Chuẩn hóa text, đọc/ghi JSONL, tạo `sample_id` ổn định và bỏ giá trị rỗng.

### Cell 5–6: parser Excel

`extract_workbook()` đọc từng sheet, merged cell, dòng mã cột, tiêu đề cha/con, sample value và kiểu dữ liệu. Một workbook có thể sinh nhiều sample; mỗi sample tương ứng một cột Excel.

### Cell 7: Manifest

Quét đệ quy `.xlsx/.xlsm`, bỏ file `~$`, tạo `Data/Manifest.jsonl` gồm `file`, `relative_path`, `doc_type_code`, `split`, `enabled`.

### Cell 8: mappings

Parse toàn bộ workbook, ghi `Data/Labels/mappings.jsonl`, đồng thời giữ nhãn cũ theo `sample_id` nếu đã tồn tại.

### Cell 9: preview

Hiển thị file, sheet, DocTypeCode, column code, header path, kiểu dữ liệu và candidate.

### Mapping với eform_fields

Notebook lọc field cùng DocTypeCode, so sánh `field_title`, `field_name`, `column_code` bằng RapidFuzz và lưu tối đa 5 candidate. Score chỉ là gợi ý, không tự chứng minh đáp án đúng.

### Build dataset

Chỉ record có cả hai điều kiện sau mới được dùng train:

```json
{"verified": true, "target_data_field_id": "field_name_chính_xác"}
```

Record chưa xác nhận là `Pending`; cột không nhập có thể đặt `ignore=true`.

## 5. Đầu ra

```text
Data/Manifest.jsonl
Data/Labels/mappings.jsonl
Data/Train/train.jsonl
Data/Validation/validation.jsonl
Data/Test/test.jsonl
Data/Test/ground_truth.jsonl
```

Dataset huấn luyện thường có:

```json
{"query":"[DOCTYPE] 01d [HEADER] Tổng số [CODE] (3)","positive":"[FIELD] Số văn bản ...","negative":["[FIELD] Số hồ sơ ..."]}
```

## 6. Vì sao Train có thể bằng 0?

Nếu thấy `Verified: 0`, `Pending: 14649`, `Train: 0` thì parser vẫn chạy bình thường; chỉ là chưa có ground truth. `eform_fields.jsonl` giúp sinh candidates nhưng không tự xác nhận target field.

## 7. Chạy đúng

Restart Kernel/Runtime rồi chọn **Run All**. Kiểm tra `Manifest` có DocTypeCode, `mappings` có candidates và các file JSONL đọc được. Không xóa `Raw` hoặc `eform_fields`; nếu chạy sạch chỉ xóa các file output mapping/train.

## 8. Đánh giá chất lượng

- JSONL hợp lệ, không có `sample_id` trùng.
- DocTypeCode khớp tên file.
- Không giao workbook giữa Train/Validation/Test.
- Verified record có `target_data_field_id`.
- Không có cùng query nhưng target khác nhau.
- Mỗi DocType quan trọng có sample.

Chỉ khi `Train`, `Validation`, `Test` đều có dữ liệu verified mới nên chạy `TrainAiImport.ipynb` trên Colab.

## 9. Trạng thái hiện tại

```text
Raw workbook: 1.232
DocTypeCode: 27
DocumentContent mẫu: 30
eform_fields: 434
Mapping candidates: 14.649
Verified: 0
```

Schema và candidates đã có; training dataset có nhãn vẫn chưa hoàn thành.
