# Cấu trúc dữ liệu huấn luyện và bộ câu lệnh mẫu

## 1. Mục đích

Tài liệu quy định cách mô tả một mẫu huấn luyện, nguyên tắc gán nhãn vùng bảng, cách biểu diễn tiêu đề phân cấp và bộ câu lệnh dùng để hướng dẫn gán nhãn hoặc kiểm định kết quả. Các quy ước thống nhất giúp dữ liệu được tạo bởi nhiều người hoặc nhiều công cụ vẫn có cùng ý nghĩa.

## 2. Đơn vị của bộ dữ liệu

Một mẫu tương ứng với một trang tính Excel. Mẫu lưu thông tin tham chiếu đến tệp gốc, kích thước trang tính, danh sách vùng bảng, nhóm bố cục, nguồn nhãn và tập dữ liệu được phân bổ.

Một trang tính có thể chứa một hoặc nhiều bảng. Các tọa độ sử dụng cách đánh số hàng và cột bắt đầu từ 1, giống cách người dùng nhìn thấy trong Excel.

## 3. Cấu trúc một mẫu huấn luyện

| Nhóm thông tin | Thành phần | Ý nghĩa |
|---|---|---|
| Nhận dạng | Mã mẫu | Phân biệt duy nhất từng trang tính |
| Nhận dạng | Mã tệp | Gom các trang tính thuộc cùng một tệp |
| Truy vết | Vị trí tệp nguồn | Cho phép mở lại đúng tệp Excel khi cần |
| Truy vết | Dấu vân tay số | Phát hiện tệp trùng và kiểm tra tính toàn vẹn |
| Trang tính | Tên, thứ tự, số hàng và số cột | Mô tả phạm vi dữ liệu có thể sử dụng |
| Bố cục | Nhóm bố cục | Gom các mẫu có cấu trúc tương tự |
| Nhãn | Danh sách vùng bảng | Xác định bảng, tiêu đề và vùng giá trị |
| Chất lượng | Phương pháp gán nhãn, độ tin cậy, cảnh báo | Hỗ trợ kiểm duyệt và truy vết |
| Phân chia | Tập huấn luyện, xác thực hoặc kiểm tra | Xác định mục đích sử dụng mẫu |
| Tăng cường | Danh sách phép biến đổi | Tạo biến thể cấu trúc cho tập huấn luyện |

Thông tin mô tả không cần lưu lại toàn bộ ma trận giá trị của tệp Excel. Khi huấn luyện hoặc kiểm tra trực quan, nội dung cần thiết được đọc từ tệp nguồn.

## 4. Quy tắc gán nhãn vùng bảng

Mỗi bảng có năm ranh giới:

| Ranh giới | Quy tắc |
|---|---|
| Hàng bắt đầu | Hàng đầu tiên thực sự thuộc bảng, không lấy tiêu đề chung của báo cáo |
| Cột bắt đầu | Cột trái nhất của bảng |
| Hàng kết thúc | Hàng dữ liệu cuối cùng, không lấy ghi chú hoặc chữ ký |
| Cột kết thúc | Cột phải nhất của bảng |
| Hàng cuối tiêu đề | Hàng cuối của tiêu đề nhiều tầng hoặc hàng mã cột |

Các điều kiện bắt buộc:

- hàng bắt đầu không được nằm sau hàng cuối tiêu đề;
- hàng cuối tiêu đề không được nằm sau hàng kết thúc;
- cột bắt đầu không được nằm sau cột kết thúc;
- mọi tọa độ phải nằm trong kích thước trang tính;
- hai bảng độc lập không được gán thành một vùng chung;
- ghi chú và vùng ký xác nhận phải nằm ngoài bảng.

## 5. Chuyển nhãn vùng thành ba lớp ô

| Vị trí ô | Lớp gán cho mô hình |
|---|---|
| Nằm ngoài tất cả các vùng bảng | Ngoài bảng |
| Từ hàng bắt đầu đến hàng cuối tiêu đề, trong chiều rộng bảng | Tiêu đề |
| Sau hàng cuối tiêu đề đến hàng kết thúc, trong chiều rộng bảng | Giá trị |

Nhờ cách biểu diễn này, mô hình vừa học được ranh giới bảng vừa học được điểm chuyển tiếp giữa tiêu đề và số liệu.

## 6. Nguồn nhãn và mức độ tin cậy

Nhãn có thể được tạo từ các dấu hiệu cấu trúc và sau đó được con người kiểm duyệt.

| Nguồn nhãn | Diễn giải |
|---|---|
| Hàng mã cột chuẩn | Bảng có hàng mã dạng `(1)`, `(2)`, ký tự hoặc mẫu tương tự |
| Chuỗi mã số | Bảng có hàng mã số tăng/giảm đều theo cột |
| Chuyển tiếp chữ – số | Suy luận vị trí khi hàng tiêu đề chủ yếu là chữ và hàng tiếp theo chủ yếu là số |
| Đối chiếu thủ công | Người kiểm duyệt xác nhận trực tiếp ranh giới với tệp Excel và kết quả mong đợi |

Độ tin cậy của nhãn chỉ phản ánh mức chắc chắn của quá trình gán nhãn. Nó không thay thế bước kiểm tra thủ công đối với tập đánh giá chính thức.

## 7. Tăng cường dữ liệu

### 7.1. Mục tiêu

Tăng cường dữ liệu tạo các biến thể hợp lý của bố cục để mô hình không ghi nhớ vị trí hoặc định dạng của một vài biểu mẫu.

### 7.2. Các phép biến đổi

| Phép biến đổi | Tác dụng |
|---|---|
| Dịch hàng | Mô phỏng bảng bắt đầu thấp hơn trong trang tính |
| Dịch cột | Mô phỏng bảng bắt đầu lệch sang phải |
| Giảm tín hiệu định dạng | Giúp mô hình không phụ thuộc hoàn toàn vào chữ đậm, căn giữa hoặc đường viền |
| Che một phần chữ tiêu đề | Khuyến khích mô hình dùng đồng thời bố cục, kiểu dữ liệu và ô gộp |

Mọi phép dịch chuyển phải áp dụng đồng thời cho dữ liệu biểu diễn, vùng ô gộp và nhãn. Tăng cường không được tạo số liệu nghiệp vụ giả.

## 8. Chia tập và ngăn rò rỉ dữ liệu

Việc chia tập phải thực hiện theo tệp, không chia ngẫu nhiên từng hàng hoặc từng ô. Nếu cùng một tệp xuất hiện ở cả tập huấn luyện và tập kiểm tra, kết quả đánh giá sẽ cao hơn thực tế.

Tập kiểm tra khác miền phải gồm những nhóm bố cục không xuất hiện trong quá trình huấn luyện. Điều này cho biết mô hình có thể xử lý cấu trúc mới đến mức nào.

## 9. Biểu diễn đầu ra cho từng cột

Sau khi vùng bảng được xác định, mỗi cột được mô tả bằng:

| Thành phần | Ví dụ | Ý nghĩa |
|---|---|---|
| Vị trí cột | Cột C | Vị trí vật lý trong Excel |
| Đường dẫn tiêu đề | Kết quả thực hiện → Kinh phí | Quan hệ từ tiêu đề cha đến tiêu đề con |
| Nhãn hiển thị | Kinh phí | Nhãn chi tiết nhất của cột |
| Mã cột | `(3)` | Mã thứ tự nếu bảng có hàng mã |

Đây là ánh xạ cấu trúc cơ bản giúp giao diện biết mỗi giá trị thuộc nhánh tiêu đề nào. Việc ghép với chỉ tiêu nghiệp vụ của biểu đích được thực hiện ở giai đoạn sau.

## 10. Vai trò của bộ câu lệnh

Mô hình huấn luyện chính sử dụng lưới đặc trưng và nhãn ô, không phụ thuộc vào một dịch vụ mô hình ngôn ngữ khi vận hành. Bộ câu lệnh trong tài liệu có ba vai trò:

1. Thống nhất hướng dẫn cho người gán nhãn.
2. Hỗ trợ một công cụ AI kiểm tra nhãn nếu được sử dụng trong tương lai.
3. Làm hợp đồng mô tả đầu vào, quy tắc và đầu ra mong đợi.

## 11. Câu lệnh mẫu 1 — xác định vùng bảng

```text
VAI TRÒ
Bạn là chuyên viên kiểm định cấu trúc bảng thống kê trong Excel.

NHIỆM VỤ
Xác định tất cả các bảng cần hiển thị trên trang tính. Với mỗi bảng,
hãy chỉ ra hàng bắt đầu, cột bắt đầu, hàng kết thúc, cột kết thúc
và hàng cuối cùng thuộc phần tiêu đề.

QUY TẮC
1. Phần tiêu đề gồm toàn bộ các tầng tiêu đề và hàng mã cột nếu có.
2. Phần giá trị chỉ gồm các hàng dữ liệu thực tế.
3. Không đưa tiêu đề chung của báo cáo, ghi chú hoặc chữ ký vào bảng.
4. Nếu có nhiều bảng độc lập, phải trả từng bảng riêng.
5. Không suy diễn hoặc sửa nội dung ô.
6. Nếu không có bảng, trả danh sách rỗng và nêu lý do.

KẾT QUẢ
Trả danh sách vùng bảng và các cảnh báo cần người kiểm duyệt xem lại.
```

## 12. Câu lệnh mẫu 2 — kiểm tra tiêu đề phân cấp

```text
VAI TRÒ
Bạn là chuyên viên kiểm tra tiêu đề nhiều tầng của bảng thống kê.

ĐẦU VÀO
Phạm vi bảng, hàng cuối tiêu đề, nội dung các ô tiêu đề
và danh sách các ô gộp.

NHIỆM VỤ
1. Kiểm tra các hàng được gán là tiêu đề có đầy đủ hay không.
2. Xác định tiêu đề cha bao phủ những cột con nào dựa trên ô gộp.
3. Tạo đường dẫn tiêu đề từ trên xuống cho từng cột.
4. Tách mã cột nếu có một hàng mã thống nhất.
5. Không ánh xạ sang biểu đích và không thay đổi số liệu.

KẾT QUẢ
Trả trạng thái hợp lệ, danh sách cột, đường dẫn tiêu đề
và các vấn đề cần sửa.
```

## 13. Câu lệnh mẫu 3 — kiểm định nhãn

```text
So sánh nhãn vùng bảng với trang tính gốc.

Kiểm tra lần lượt:
- hàng hoặc cột bắt đầu có bị thiếu hay thừa;
- hàng hoặc cột kết thúc có bị thiếu hay thừa;
- ranh giới tiêu đề có chính xác;
- có bỏ sót bảng hoặc tạo thừa bảng;
- có lấy nhầm ghi chú, dòng trống hoặc chữ ký;
- trang tính có thực sự không chứa bảng hay không.

Trả kết luận chấp nhận hoặc không chấp nhận, vùng đã hiệu chỉnh
và danh sách lỗi cụ thể. Không tự chấp nhận nếu chưa quan sát đủ trang tính.
```

## 14. Tiêu chí chấp nhận bộ dữ liệu

- Các mẫu đọc được và có mã định danh duy nhất.
- Mọi tệp nguồn có thể truy vết và kiểm tra tính toàn vẹn.
- Tọa độ bảng hợp lệ, không vượt trang tính và không chồng lấn.
- Không có tệp nào xuất hiện ở nhiều tập đánh giá khác nhau.
- Tập kiểm tra khác miền không chia sẻ nhóm bố cục với tập huấn luyện.
- Tăng cường chỉ áp dụng cho tập huấn luyện.
- Có mẫu trang tính không chứa bảng để đo trường hợp nhận diện nhầm.
- Tập đánh giá có nhãn được con người xác nhận và đủ đại diện.
- Có mẫu chứa nhiều bảng, tiêu đề sâu, ghi chú sát bảng và bố cục hiếm.

## 15. Kết luận

Cấu trúc dữ liệu được thiết kế gọn nhưng đủ để huấn luyện bài toán nhận diện vùng bảng. Bộ câu lệnh giúp thống nhất cách hiểu giữa người làm dữ liệu, công cụ hỗ trợ và người kiểm định. Quan hệ tiêu đề cha – con được bảo toàn dưới dạng đường dẫn cột, tạo đầu ra rõ ràng cho bước xem trước và xử lý nghiệp vụ tiếp theo.

