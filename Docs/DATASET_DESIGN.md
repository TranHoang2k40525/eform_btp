# Thiết kế dataset

## Đơn vị dữ liệu

Một record mapping JSONL:

```json
{"group_id":"template-family-01","source":"Tên cơ quan thực hiện","target_id":"organization_name","target_text":"Tên đơn vị; Tên cơ quan; Đơn vị báo cáo","synthetic":false}
```

- `source`: header nguồn đã trim/NFKC, có thể giữ dấu tiếng Việt.
- `target_id`: ID field ổn định từ schema eForm, không dùng column index.
- `target_text`: label + description + alias đã kiểm duyệt.
- `group_id`: workbook/template family hoặc nguồn thu thập; dùng để chống leakage.
- `synthetic`: đánh dấu dữ liệu tạo thêm, không dùng làm test thật.

Seed trong repository chỉ để smoke test pipeline, không đủ train. Raw workbook không commit vào Git.

## Nguồn dữ liệu được phép

1. Schema/header/config do eForm xuất, không lấy cell value nếu không cần.
2. Mapping người dùng đã xác nhận và có quyền sử dụng cho cải thiện model.
3. Alias do chuyên gia nghiệp vụ duyệt.
4. Synthetic variation chỉ bổ trợ train.

Không đưa mật khẩu, token, tài khoản kết nối, cookie, số điện thoại/email hoặc nội dung văn bản cá nhân vào dataset. Workbook có sheet cấu hình/tài khoản phải loại toàn bộ sheet đó.

## Tiền xử lý

1. Parse cấu trúc nhưng chỉ xuất header/schema metadata.
2. Unicode NFKC, trim/thu gọn whitespace.
3. Scrub email, phone và chuỗi secret phổ biến.
4. Deduplicate theo `(normalized source, target_id)`.
5. Chuyên gia xử lý conflict cùng source nhưng nhiều target dựa theo form context.
6. Gắn source/template group.
7. Split group-isolated với seed cố định.

Với dữ liệu thật nên split theo `template_family`/workbook source để header gần như giống nhau không xuất hiện hai tập. Nếu cần đánh giá target đã biết, đảm bảo mỗi target vẫn có coverage nhưng các alias/template cụ thể không rò rỉ.

## Kích thước khuyến nghị

- `<20`: chỉ kiểm tra code, script cố ý không fine-tune.
- `20–499`: thí nghiệm, kết luận còn yếu.
- `>=500`: có thể fine-tune pilot nếu phủ đủ loại form.
- `>=2.000` và có hard negatives: phù hợp đánh giá nghiêm túc hơn.

Số lượng không thay thế độ phủ. Báo cáo distribution theo form code, field, đơn vị, kiểu header, merged level và confidence bucket.

## Negative/hard-negative

Multiple Negatives Ranking tận dụng target khác trong batch. Bổ sung hard negative như “Tổng số”, “Tổng số nữ”, “Tổng số đã xử lý” để model học khác biệt. Không tạo hard negative sai về nghiệp vụ; cần người duyệt.

## Versioning

Mỗi dataset release có manifest: version, created UTC, seed, source IDs, record count, split counts, scrub version, SHA-256 và người phê duyệt. Không sửa file release cũ; tạo version mới. Artifact registry giới hạn truy cập, retention theo chính sách dữ liệu.

## Drift/feedback

Theo dõi unknown/review/override rate theo tháng và form. Chỉ feedback `accepted=true` hoặc override đã xác nhận mới vào candidate dataset. Không retrain liên tục; gom batch tối thiểu 100 mẫu mới, chạy lại full evaluation và giữ test set cố định.

