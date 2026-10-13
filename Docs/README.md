# Tài liệu báo cáo thực tập

Thư mục này gồm các báo cáo và tài liệu mô tả quá trình thực hiện module nhập
dữ liệu từ tệp Excel.

## Tài liệu dùng để nộp và trình bày

| Tài liệu | Nội dung |
|---|---|
| `Báo cáo tổng hợp thực tập tuần 8-10.md` | Tổng hợp mục tiêu, công việc, kết quả và hướng phát triển |
| `Tuần 8/Báo cáo thực tập tuần 8.md` | Hoàn thiện giao diện chọn tệp và xem trước bảng |
| `Tuần 9/Báo cáo thực tập tuần 9.md` | Thu gọn giao diện và thống nhất luồng xử lý |
| `Tuần 10/Báo cáo thực tập tuần 10.md` | Kiểm tra lỗi, xử lý dữ liệu và lưu kết quả |

Các báo cáo trên được viết theo hướng dành cho người đọc không trực tiếp tham
gia lập trình. Nội dung tập trung vào mục tiêu, công việc đã làm, kết quả quan
sát được và phần còn lại; không đưa thông tin cấu hình, thông tin truy cập hoặc
chi tiết triển khai không cần thiết.

## Tài liệu tham khảo nội bộ

Các tệp thiết kế, sơ đồ và ghi chú kỹ thuật trong thư mục này dùng để tra cứu
trong quá trình phát triển. Khi gửi báo cáo cho thầy cô hoặc đơn vị, chỉ nên
gửi các báo cáo thực tập và ảnh minh chứng phù hợp.

## Luồng xử lý khái quát

```text
Chọn tệp Excel
  → Kiểm tra tệp
  → Xác định vùng bảng
  → Đọc nội dung bảng
  → Hiển thị xem trước
  → Kiểm tra kết quả
  → Lưu và chuyển sang bước nghiệp vụ tiếp theo
```

Số liệu hiển thị trong bảng được lấy từ tệp Excel do người dùng cung cấp. Phần
nhận diện chỉ hỗ trợ xác định cấu trúc; hệ thống không tự tạo số liệu thay cho
tệp nguồn.
