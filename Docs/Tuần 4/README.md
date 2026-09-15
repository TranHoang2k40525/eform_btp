# Danh mục tài liệu Tuần 4

## Chủ đề

**Chuẩn bị dữ liệu mẫu và thiết kế bộ câu lệnh để mô hình nhận diện cấu trúc phân cấp của bảng thống kê trong Excel.**

Bộ tài liệu trình bày một giải pháp hỗ trợ đọc các tệp Excel báo cáo có bố cục khác nhau. Hệ thống xác định bảng cần lấy, phân biệt vùng tiêu đề và vùng số liệu, bảo toàn quan hệ tiêu đề cha – con, sau đó trả dữ liệu xem trước để người dùng kiểm tra trước khi nhập.

## Đối tượng sử dụng

- Người quản lý và cán bộ nghiệp vụ cần hiểu mục tiêu, lợi ích và kết quả của giải pháp.
- Thành viên dự án cần thống nhất cách chuẩn bị, gán nhãn và kiểm tra bộ dữ liệu.
- Người đánh giá cần có số liệu, sơ đồ và kết quả thử nghiệm làm minh chứng.

## Thành phần tài liệu

| Tài liệu | Nội dung |
|---|---|
| `01_BAO_CAO_XAY_DUNG_BO_DU_LIEU.md` | Bài toán, phạm vi, phương pháp chuẩn bị dữ liệu và kết quả mong đợi |
| `02_CAU_TRUC_DU_LIEU_VA_BO_PROMPT_MAU.md` | Cấu trúc mẫu huấn luyện, quy tắc gán nhãn và bộ câu lệnh mẫu |
| `03_KET_QUA_CHUAN_BI_DU_LIEU_VA_THU_NGHIEM.md` | Thống kê bộ dữ liệu, kết quả thử nghiệm, hạn chế và kế hoạch hoàn thiện |
| `BAO_CAO_TUAN_4_CHUAN_BI_BO_DU_LIEU_AI.docx` | Báo cáo Word tổng hợp để trình bày và lưu minh chứng |
| `diagrams/` | Ba sơ đồ draw.io có thể chỉnh sửa và ảnh PNG để xem nhanh |

## Ba nội dung cốt lõi

1. Mô hình học cách xác định vị trí bảng và phân loại ô thành ba nhóm: ngoài bảng, tiêu đề và giá trị.
2. Nội dung trong Excel được đọc trực tiếp sau khi đã xác định vùng; mô hình không tự tạo lại số liệu.
3. Quan hệ tiêu đề phân cấp được biểu diễn thành đường dẫn từ tiêu đề cha đến tiêu đề con cho từng cột, tạo cơ sở cho việc hiển thị và ánh xạ nghiệp vụ ở bước tiếp theo.

## Phạm vi

Bộ tài liệu tập trung vào dữ liệu huấn luyện, quy tắc gán nhãn, bộ câu lệnh mẫu và kết quả thử nghiệm. Việc đối chiếu với biểu đích, kiểm tra nghiệp vụ và ghi dữ liệu chính thức được thực hiện sau bước xem trước nên không thuộc phạm vi báo cáo này.

