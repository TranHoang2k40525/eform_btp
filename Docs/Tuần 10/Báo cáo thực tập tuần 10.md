# BÁO CÁO THỰC TẬP TUẦN 10

## 1. Nội dung thực hiện

Trong tuần 10, em tập trung kiểm tra các trường hợp tệp không hợp lệ, hoàn
thiện việc lưu kết quả và xử lý trường hợp hệ thống gặp lỗi. Mục tiêu là bảo
đảm người dùng nhận được thông báo rõ ràng và không ghi dữ liệu chưa được kiểm
tra vào hệ thống.

## 2. Các công việc đã thực hiện

### 2.1. Kiểm tra tệp đầu vào

Em đã bổ sung và kiểm tra các điều kiện:

- tệp phải thuộc định dạng được hỗ trợ;
- tệp không được rỗng;
- tệp phải có cấu trúc Excel hợp lệ;
- tệp có kích thước vượt giới hạn phải được thông báo trước khi xử lý.

Khi phát hiện lỗi, hệ thống dừng xử lý và hiển thị hướng dẫn để người dùng
chọn lại tệp. Tệp lỗi không được chuyển sang bước lưu dữ liệu.

### 2.2. Hoàn thiện lưu kết quả

Sau khi bảng được đọc thành công và kết quả đáp ứng các điều kiện cần thiết,
hệ thống thực hiện lưu kết quả. Thông báo thành công chỉ được hiển thị sau khi
việc lưu hoàn tất. Nếu xảy ra lỗi trong quá trình lưu, hệ thống trả về thông
báo lỗi thay vì thông báo thành công không đúng thực tế.

### 2.3. Xử lý trường hợp tiêu đề phức tạp

Một số tệp có phần thông tin mô tả ở đầu trang, tiêu đề nhiều tầng và các ô
gộp kéo dài qua nhiều hàng. Em đã bổ sung bước rà soát ranh giới bảng để phân
biệt phần mô tả với phần tiêu đề và dữ liệu thực tế. Cách xử lý dựa trên nhiều
dấu hiệu của bảng như ô gộp, đường viền, mật độ dữ liệu và sự chuyển tiếp giữa
tiêu đề với hàng giá trị, không phụ thuộc vào một vị trí cố định.

## 3. Kết quả đạt được

Luồng nhập dữ liệu đã có kiểm tra đầu vào, xử lý lỗi, dựng bảng xem trước và
lưu kết quả theo đúng thứ tự. Các trường hợp thường gặp như tệp rỗng, tệp hỏng
hoặc kết quả không đúng cấu trúc đều được chặn và thông báo rõ ràng.

## 4. Kiểm tra và minh chứng

Em đã kiểm tra các nhóm trường hợp sau:

| Nhóm kiểm tra | Kết quả |
|---|---|
| Tệp hợp lệ | Hiển thị được bảng xem trước |
| Tệp rỗng | Hiển thị cảnh báo và dừng xử lý |
| Tệp sai cấu trúc | Hiển thị cảnh báo và không lưu |
| Kết quả có tiêu đề nhiều tầng | Giữ được cấu trúc bảng |
| Lưu kết quả hợp lệ | Chỉ thông báo thành công sau khi lưu hoàn tất |
| Lỗi trong quá trình lưu | Hiển thị thông báo lỗi phù hợp |

Ảnh minh chứng và các tệp kiểm tra được lưu trong thư mục `evidence` của tuần
10. Các minh chứng chỉ thể hiện kết quả quan sát được trong ứng dụng.

## 5. Khó khăn và hướng xử lý

Khó khăn lớn nhất là phải xử lý đồng thời nhiều kiểu bố cục Excel nhưng vẫn
giữ nguyên số liệu nguồn. Em đã tách việc xác định vùng bảng khỏi việc đọc nội
dung ô. Nhờ đó, phần xác định có thể được cải thiện theo bố cục, còn giá trị
được lấy trực tiếp từ tệp gốc.

## 6. Công việc còn lại

- Tiếp tục kiểm tra với nhiều biểu mẫu thực tế hơn.
- Đối chiếu kết quả với quy tắc nghiệp vụ của hệ thống chính.
- Kiểm tra đầy đủ trong môi trường triển khai chính thức trước khi nghiệm thu.

## 7. Tự đánh giá

Trong tuần 10, em đã hoàn thiện phần kiểm tra lỗi và luồng lưu kết quả của
module. Sản phẩm đã đáp ứng được quy trình nhập tệp cơ bản và có thông báo phù
hợp cho các trường hợp thành công hoặc thất bại. Các bước tiếp theo chủ yếu là
mở rộng kiểm thử và đối chiếu với dữ liệu thực tế của đơn vị.
