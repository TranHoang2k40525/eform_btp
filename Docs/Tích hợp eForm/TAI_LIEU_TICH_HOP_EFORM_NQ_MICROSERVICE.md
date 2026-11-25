# TÀI LIỆU KIẾN TRÚC VÀ TÍCH HỢP DỊCH VỤ NHẬP EXCEL AI VÀO HỆ THỐNG eFORM BTP

**Hệ thống đích:** Hệ thống Báo cáo điện tử ngành Tư pháp (eForm BTP) 
**Phân hệ tích hợp:** Dịch vụ bóc tách cấu trúc bảng biểu Excel bằng Trí tuệ nhân tạo 
**Tài liệu:** Kiến trúc microservice và kết quả kiểm thử toàn trình 219 tình huống

---

## 1. Tổng quan mục tiêu và nguyên tắc tích hợp

Tính năng **Nhập File Excel AI** được bổ sung song song bên cạnh tính năng **Nhập file Excel** truyền thống trên hộp thoại nhập dữ liệu của eForm BTP. Mục tiêu của phân hệ là tiếp nhận các tệp bảng tính Excel có bố cục đa dạng do các đơn vị địa phương gửi lên (bị dịch vị trí, bỏ ô gộp, xóa kẻ khung, thêm cột ghi chú, chứa nhiều bảng ngang hoặc dọc, lặp tiêu đề giữa trang, lẫn trang hướng dẫn trống hoặc đảo vị trí hai cột số liệu), tự động định vị vùng bảng chính và chuẩn hóa thành cấu trúc dữ liệu đồng nhất để ghép vào biểu mẫu eForm.

Bốn nguyên tắc thiết kế bắt buộc được giữ vững xuyên suốt quá trình tích hợp:

1. **Không làm gián đoạn hệ thống hiện hữu:** Mọi chức năng nhập mẫu truyền thống, quy tắc kiểm tra công thức, quy trình phê duyệt và cơ sở dữ liệu lõi của eForm đều giữ nguyên. Dịch vụ AI vận hành như một dịch vụ vệ tinh độc lập.
2. **AI chỉ bóc tách, con người và eForm quyết định:** Mô hình AI chỉ nhận diện cấu trúc bảng và đề xuất dữ liệu thô từ tệp Excel. Toàn bộ quyền xem trước, chỉnh sửa số liệu trực tiếp, đối soát công thức nghiệp vụ, kiểm tra quyền khóa kỳ báo cáo và ghi vào cơ sở dữ liệu vẫn thuộc về hệ thống eForm và cán bộ thao tác.
3. **Tách rời hoàn toàn tầng huấn luyện và tầng vận hành:** Dịch vụ suy luận chỉ nạp duy nhất gói mô hình học sâu đã biên dịch sẵn (~3,48 MB), không phụ thuộc vào sổ tay huấn luyện hay tập dữ liệu gốc, rút ngắn thời gian khởi động và thuận tiện bảo trì.
4. **An toàn xác thực nhiều lớp:** Mọi yêu cầu gửi tệp từ trình duyệt lên cổng tích hợp đều bắt buộc đi qua cơ chế cấp mã phiên ký số ngắn hạn từ máy chủ eForm, kết hợp kiểm soát nguồn truy cập hợp lệ và lưu vết lịch sử nhập liệu độc lập.

---

## 2. Kiến trúc tổng thể ba tầng

Luồng xử lý của tính năng Nhập File Excel AI đi qua ba thành phần chính, tách bạch rõ vai trò:

| Thành phần | Môi trường triển khai | Vai trò nghiệp vụ chính |
|---|---|---|
| **Hệ thống lõi eForm BTP** | Cổng web nghiệp vụ ngành Tư pháp | Xác thực người dùng, cấp mã phiên ngắn hạn, hiển thị hộp thoại nhập Excel có hai chế độ (nhập thường và nhập AI), cung cấp lưới xem trước đa cấp cho phép sửa trực tiếp, ghép số liệu vào biểu mẫu, chạy kiểm tra ràng buộc công thức và lưu báo cáo chính thức. |
| **Cổng dịch vụ tích hợp (.NET trên IIS)** | Dịch vụ web trung gian độc lập | Kiểm tra tính hợp lệ của mã phiên ký số, thẩm định chữ ký tệp Excel và dung lượng đầu vào, chuyển tiếp tệp sang dịch vụ AI, ghi nhận nhật ký và lịch sử các lần nhập tệp vào cơ sở dữ liệu lưu vết riêng biệt. |
| **Dịch vụ suy luận AI (FastAPI + PyTorch)** | Dịch vụ nội bộ chuyên trách | Nạp trực tiếp gói mô hình học sâu vào bộ nhớ ngay khi khởi động, đọc cấu trúc bảng tính, trích xuất 60 kênh đặc trưng bất biến theo vị trí, suy luận đa tác vụ và trả về kết quả bóc tách chuẩn hóa kèm cảnh báo cấu trúc (nếu có). |

---

## 3. Luồng nghiệp vụ đầu cuối từ khi chọn tệp đến khi lưu báo cáo

Quy trình tác nghiệp của cán bộ trên giao diện eForm được thiết kế khép kín qua 7 bước rõ ràng:

1. **Kiểm tra trạng thái sẵn sàng:** Khi cán bộ mở hộp thoại nhập Excel, giao diện tự động kiểm tra sức khỏe của dịch vụ tích hợp và dịch vụ AI. Nếu dịch vụ sẵn sàng, chỉ báo trạng thái hiển thị màu xanh lục; nếu máy chủ tạm gián đoạn, nút nhập AI tự động chuyển sang trạng thái chờ và hướng dẫn cán bộ sử dụng phương thức nhập mẫu truyền thống.
2. **Xin mã phiên và gửi tệp:** Khi cán bộ chọn tệp Excel qua nút **Nhập File Excel AI**, trình duyệt kiểm tra nhanh dung lượng và phần mở rộng, sau đó yêu cầu máy chủ eForm cấp mã phiên ngắn hạn gắn với tài khoản và tài liệu đang mở rồi gửi tệp tới cổng dịch vụ tích hợp.
3. **Thẩm định đầu vào và suy luận mô hình:** Cổng dịch vụ xác thực mã phiên, kiểm tra định dạng nén hợp lệ của tệp bảng tính và chuyển sang dịch vụ suy luận AI. Mô hình học sâu đa tác vụ (839.420 tham số) tự động bỏ qua các trang hướng dẫn không có bảng, định vị vùng bảng chính, tách độc lập các bảng phụ nằm ngang hoặc bên dưới, loại bỏ khối tiêu đề lặp ở giữa bảng và đánh dấu các cột bị đảo thứ tự.
4. **Xem trước và tinh chỉnh trực tiếp:** Kết quả bóc tách được hiển thị trên cửa sổ xem trước bảng tính đa cấp giữ nguyên cấu trúc ô gộp, kèm các thông số tóm tắt (tên trang tính, tọa độ vùng bảng, số dòng tiêu đề, số dòng số liệu, độ tin cậy và cảnh báo cấu trúc nếu có). Nếu tệp có nhiều bảng, cán bộ có thể chuyển đổi thẻ bảng hoặc nhấp đúp sửa trực tiếp từng ô ngay trên lưới xem trước.
5. **Chọn trang/bảng ghép vào biểu mẫu:** Sau khi cán bộ xác nhận bảng cần lấy, hệ thống ánh xạ dữ liệu sang biểu mẫu đích, tự động sắp xếp lại thứ tự cột khi phát hiện file bị đảo cột (kèm thông báo nhắc soát lại) và mở giao diện đối soát.
6. **Kiểm tra ràng buộc nghiệp vụ:** Động cơ kiểm tra sẵn có của eForm rà soát toàn bộ các ô bắt buộc, kiểu dữ liệu số, công thức cộng tổng ngang dọc và hiển thị bảng thống kê tổng số dòng, số dòng hợp lệ, số lỗi và cảnh báo.
7. **Xác nhận ghi dữ liệu và lưu lịch sử:** Chỉ sau khi cán bộ bấm xác nhận lần cuối, số liệu mới được ghi vào biểu mẫu eForm và đồng bộ nhật ký giao dịch nhập liệu sang cổng dịch vụ tích hợp.

---

## 4. Các năng lực xử lý cấu trúc khó của mô hình AI

Mô hình học sâu đa tác vụ kết hợp hậu xử lý thuần cấu trúc giải quyết trọn vẹn các tình huống biến thể bố cục phổ biến trong thực tế:

- **Bất biến theo vị trí (dịch bảng xa góc):** Loại bỏ các đặc trưng phụ thuộc tọa độ tuyệt đối, giúp mô hình tìm chính xác một vùng bảng duy nhất ngay cả khi bảng bị đẩy lùi 25 dòng và dịch phải 6 cột.
- **Tách nhiều bảng nằm ngang và loại bỏ ghi chú bên phải:** Phân cụm thành phần liên thông theo chiều ngang và kiểm soát vùng lề, tách sạch bảng phụ đặt song song hoặc khối chữ ghi chú bên phải khỏi bảng số liệu chính.
- **Gộp bảng có tiêu đề lặp lại giữa trang:** Tự động nhận diện khối tiêu đề lặp lại ở các trang in tiếp theo, loại bỏ dòng tiêu đề thừa và giữ nguyên vẹn số liệu của cả hai nửa bảng.
- **Nhận diện trang không có bảng:** Được huấn luyện với 106 trang tính chỉ chứa hướng dẫn hoặc danh mục, giúp chọn đúng trang chứa bảng số liệu ngay cả khi tệp có nhiều trang trống hoặc trang hướng dẫn đứng đầu.
- **Phát hiện và tự động sắp xếp lại cột bị đảo thứ tự:** Nhánh dự đoán lệch cột kết hợp đối chiếu mã cột chuẩn cho phép cảnh báo sớm và tự động hoán đổi dữ liệu về đúng cột đích của biểu mẫu.

---

## 5. Tóm tắt kết quả kiểm định chất lượng tích hợp

Dịch vụ tích hợp đã được kiểm thử toàn trình trên môi trường eForm thật (`Sở Tư pháp Thành phố Bắc Ninh`) bằng bộ kiểm chuẩn gồm **219 tệp Excel thuộc 22 nhóm biến thể cấu trúc khó trên 10 biểu mẫu ngành Tư pháp**:

| Hạng mục kiểm định | Kết quả đo thực tế | Đánh giá |
|---|---:|---|
| Khớp chính xác vùng bảng trên tập Xác thực (152 trang) | **100,00%** (152/152) | Tuyệt đối |
| Khớp chính xác vùng bảng trên tập Kiểm tra cùng miền (250 trang) | **100,00%** (250/250) | Tuyệt đối |
| Khớp chính xác vùng bảng trên tập Kiểm tra khác miền (133 trang) | **98,50%** (131/133) | Tổng quát hóa cao |
| Tỷ lệ vượt qua bộ 219 tình huống khó trên hệ thống thật | **100,0%** (219/219) | Đạt toàn bộ 22 nhóm |
| Thời gian xử lý trung bình toàn trình qua IIS + AI | **322,5 ms/tệp** | Đáp ứng thời gian thực |
| Đối chứng nhập thường trên 4 biểu mẫu giao diện trực tiếp | **Nhập thường lỗi 42/53 ca khó (79,2%)** | AI vượt trội hoàn toàn |
