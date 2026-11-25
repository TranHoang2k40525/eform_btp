# BÁO CÁO KIỂM THỬ TẦNG TÍCH HỢP BACKEND C#

**Giai đoạn:** Tuần 6 
**Phạm vi:** Kiểm tra luồng kết nối giữa cổng dịch vụ trung gian (.NET trên IIS) với dịch vụ suy luận AI (FastAPI) và cơ chế kiểm soát đầu vào/lưu vết.

---

## 1. Môi trường kiểm thử

- **Cổng dịch vụ trung gian:** Triển khai trên máy chủ IIS cục bộ kết nối với cổng eForm BTP.
- **Dịch vụ suy luận AI:** Dịch vụ FastAPI nạp trực tiếp mô hình học sâu (~3,48 MB).
- **Cơ chế xác thực:** Sử dụng mã phiên ký số thật cấp từ phiên đăng nhập hợp lệ trên hệ thống eForm.

---

## 2. Kết quả thực thi các nhóm kịch bản kiểm thử

| Mã kịch bản | Nội dung kiểm thử | Kết quả mong đợi | Kết quả thực tế | Đánh giá |
|:---:|---|---|---|:---:|
| **BE-01** | Kiểm tra trạng thái sẵn sàng của cổng dịch vụ và mô hình AI | Phản hồi mã 200, xác nhận dịch vụ AI đang sẵn sàng | Phản hồi tức thời trong < 20 ms, trạng thái sẵn sàng | **ĐẠT** |
| **BE-02** | Gửi yêu cầu không kèm mã phiên xác thực hoặc mã phiên hết hạn | Từ chối truy cập, không chuyển tệp sang dịch vụ AI | Từ chối an toàn với mã lỗi xác thực chuẩn | **ĐẠT** |
| **BE-03** | Gửi tệp Excel chuẩn (1 trang tính, nhiều tầng tiêu đề) | Trả về JSON 2.0 đúng tọa độ bảng, tiêu đề phân cấp và đủ dòng số liệu | Bóc tách chính xác 100%, giữ đủ ô gộp tiêu đề | **ĐẠT** |
| **BE-04** | Gửi tệp rỗng 0 byte hoặc tệp văn bản đổi đuôi thành Excel | Chặn ngay tại tầng thẩm định đầu vào, trả thông báo tiếng Việt | Phát hiện ngay sai chữ ký tệp, từ chối an toàn | **ĐẠT** |
| **BE-05** | Gửi hàng loạt 109 tệp thuộc 5 biểu tổng hợp khó (22 biến thể) qua cổng IIS | Toàn bộ 109 tệp trả về mã 200, bóc tách đúng bảng chính | **109/109 ĐẠT (100%)**, thời gian trung bình 342,5 ms/tệp | **ĐẠT** |
| **BE-06** | Mô phỏng ngắt dịch vụ AI khi cổng trung gian nhận yêu cầu | Không treo hệ thống, trả thông báo gián đoạn máy chủ thân thiện | Thông báo lỗi rõ ràng, không làm ảnh hưởng trang eForm | **ĐẠT** |

---

## 3. Kết luận

Tầng tích hợp Backend C# vận hành ổn định, bảo mật theo đúng chuẩn mã phiên của eForm, kiểm soát chặt chẽ dữ liệu đầu vào và duy trì thời gian phản hồi nhanh ngay cả khi xử lý liên tiếp hơn 100 biểu mẫu phức tạp.
