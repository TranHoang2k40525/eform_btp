# BÁO CÁO KIỂM THỬ GIAO DIỆN TẢI TỆP BẤT ĐỒNG BỘ

**Giai đoạn:** Tuần 7 
**Công cụ kiểm thử:** Kiểm thử trực tiếp trên trình duyệt Chrome với giao diện web tích hợp

---

## 1. Bảng kết quả kiểm thử các kịch bản giao diện tải tệp

| Mã ca kiểm thử | Kịch bản kiểm thử | Kết quả ghi nhận | Đánh giá |
|:---:|---|---|:---:|
| **UI-01** | Hiển thị hộp thoại và kiểm tra trạng thái sẵn sàng của dịch vụ AI | Huy hiệu trạng thái hiển thị màu xanh lục khi dịch vụ sẵn sàng | **ĐẠT** |
| **UI-02** | Chọn tệp Excel hợp lệ và gửi bất đồng bộ không tải lại trang | Trình duyệt gửi tệp mượt mà, giữ nguyên trạng thái trang báo cáo nền | **ĐẠT** |
| **UI-03** | Khóa nút thao tác trong lúc chờ mô hình phân tích | Ngăn chặn thành công tình trạng nhấn gửi nhiều lần liên tiếp | **ĐẠT** |
| **UI-04** | Chọn tệp rỗng (0 byte) hoặc tệp không đúng định dạng Excel | Báo lỗi đỏ trực quan ngay trên trình duyệt, không phát sinh yêu cầu thừa | **ĐẠT** |
| **UI-05** | Hiển thị thông tin tóm tắt sau khi dịch vụ AI trả kết quả | Hiển thị đầy đủ tên tệp, trang tính, vùng bảng, số dòng và độ tin cậy | **ĐẠT** |
| **UI-06** | Chọn lại tệp khác sau khi hủy hoặc gặp lỗi | Trạng thái hộp thoại được làm mới sạch sẽ, sẵn sàng cho lượt nhập kế tiếp | **ĐẠT** |

---

## 2. Nhận xét

Luồng tải tệp bất đồng bộ vận hành mượt mà, phản hồi rõ ràng ở mọi trạng thái và đặt nền tảng ổn định cho giai đoạn phát triển lưới xem trước bảng tính đa cấp ở Tuần 8.
