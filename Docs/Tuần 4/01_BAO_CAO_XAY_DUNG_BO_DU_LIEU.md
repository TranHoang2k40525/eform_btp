# Báo cáo xây dựng bộ dữ liệu nhận diện cấu trúc bảng thống kê

## 1. Tóm tắt

Các báo cáo thống kê thường được cung cấp dưới dạng Excel với nhiều kiểu bố cục: phần tiêu đề có thể gồm nhiều hàng, một tiêu đề cha có thể bao phủ nhiều cột con, số liệu có thể bắt đầu ở các vị trí khác nhau và phía dưới bảng thường có ghi chú hoặc khu vực ký xác nhận. Nếu chỉ dựa vào vị trí cố định, hệ thống dễ lấy thiếu dữ liệu hoặc lấy nhầm phần không thuộc bảng.

Giải pháp được xây dựng nhằm tự động xác định vùng bảng cần sử dụng, nhận biết phần tiêu đề và phần số liệu, sau đó trả lại nội dung theo đúng cấu trúc của bảng gốc để người dùng xem trước. Bộ dữ liệu huấn luyện là nền tảng giúp mô hình học được những đặc điểm bố cục chung thay vì phụ thuộc vào một biểu mẫu duy nhất.

## 2. Bài toán nghiệp vụ

### 2.1. Đầu vào

Đầu vào là các tệp Excel báo cáo có thể khác nhau về:

- số lượng hàng và cột;
- vị trí bắt đầu của bảng;
- số tầng tiêu đề;
- cách gộp ô để biểu diễn tiêu đề cha – con;
- định dạng chữ, căn lề, đường viền và độ rộng cột;
- số lượng bảng trên cùng một trang tính;
- vị trí ghi chú, chữ ký và thông tin mô tả ngoài bảng.

### 2.2. Kết quả cần đạt

Đối với mỗi bảng được phát hiện, hệ thống cần trả được:

- phạm vi của bảng trong trang tính;
- số hàng thuộc phần tiêu đề;
- toàn bộ nội dung ô trong vùng bảng;
- thông tin ô gộp;
- độ rộng cột, chiều cao hàng và định dạng cần thiết để hiển thị;
- đường dẫn tiêu đề phân cấp của từng cột;
- độ tin cậy của kết quả nhận diện.

Kết quả này được dùng để dựng màn hình xem trước. Người dùng có thể kiểm tra cấu trúc và số liệu trước khi chuyển sang bước nhập dữ liệu chính thức.

## 3. Phạm vi xử lý

Quy trình được chia thành hai phần có trách nhiệm khác nhau.

| Phần xử lý | Trách nhiệm |
|---|---|
| Nhận diện bằng mô hình học máy | Xác định ô nào nằm ngoài bảng, ô nào thuộc tiêu đề và ô nào thuộc vùng giá trị |
| Trích xuất theo quy tắc xác định | Đọc nguyên nội dung, ô gộp, công thức và định dạng từ tệp Excel trong vùng đã nhận diện |

Cách tổ chức này bảo đảm mô hình chỉ giải quyết phần khó thay đổi theo bố cục, còn việc đọc dữ liệu sử dụng phương pháp xác định. Vì vậy, số liệu đầu ra luôn bắt nguồn từ tệp Excel đã tải lên, không phải nội dung do mô hình tự tạo.

Việc ghép các cột đã nhận diện với chỉ tiêu của một biểu đích cụ thể được thực hiện ở bước nghiệp vụ sau khi xem trước. Bộ dữ liệu trong báo cáo này không phụ thuộc vào loại biểu hoặc mã biểu đích.

## 4. Cách mô hình biểu diễn một bảng

Mỗi ô trong trang tính được gán vào một trong ba nhóm:

| Nhóm | Ý nghĩa |
|---|---|
| Ngoài bảng | Tiêu đề báo cáo, thông tin đơn vị, khoảng trống, ghi chú, chữ ký hoặc nội dung khác không thuộc bảng cần lấy |
| Tiêu đề | Các hàng mô tả cột, bao gồm tiêu đề nhiều tầng và hàng mã cột nếu có |
| Giá trị | Các hàng chứa dữ liệu cần hiển thị và nhập |

Từ kết quả phân loại ô, phạm vi một bảng được mô tả bằng năm thông tin:

| Thông tin | Diễn giải |
|---|---|
| Hàng bắt đầu | Hàng đầu tiên thuộc bảng |
| Cột bắt đầu | Cột đầu tiên thuộc bảng |
| Hàng kết thúc | Hàng cuối cùng thuộc bảng |
| Cột kết thúc | Cột cuối cùng thuộc bảng |
| Hàng cuối tiêu đề | Ranh giới giữa phần tiêu đề và phần giá trị |

Ví dụ, phạm vi `A2:M8` với hàng cuối tiêu đề là hàng 7 có nghĩa: bảng bắt đầu tại ô A2, kết thúc tại ô M8, phần tiêu đề kéo dài từ hàng 2 đến hàng 7 và phần giá trị bắt đầu từ hàng 8.

## 5. Hiểu cấu trúc tiêu đề phân cấp

Tiêu đề phân cấp là trường hợp một nhóm cột có chung tiêu đề cha và mỗi cột có một tiêu đề con riêng. Trong Excel, quan hệ này thường được thể hiện bằng ô gộp.

Hệ thống xử lý theo trình tự:

1. Xác định toàn bộ các hàng thuộc vùng tiêu đề.
2. Đọc thông tin ô gộp trong vùng này.
3. Gán nội dung của ô gốc cho các cột mà ô gộp bao phủ.
4. Duyệt từng cột từ hàng tiêu đề trên xuống dưới.
5. Ghép các nhãn thành một đường dẫn từ tiêu đề cha đến tiêu đề con.
6. Tách mã cột như `(1)`, `(2)` hoặc `-1`, `-2` nếu có.

Ví dụ:

| Cột | Tiêu đề cha | Tiêu đề con | Đường dẫn phân cấp |
|---|---|---|---|
| B | Kết quả thực hiện | Số lượng | Kết quả thực hiện → Số lượng |
| C | Kết quả thực hiện | Kinh phí | Kết quả thực hiện → Kinh phí |

Đường dẫn này là kết quả ánh xạ cơ bản của giai đoạn nhận diện cấu trúc: mỗi cột vật lý trong Excel được gắn với đầy đủ chuỗi tiêu đề của nó.

## 6. Quy trình xây dựng bộ dữ liệu

### 6.1. Thu thập dữ liệu mẫu

Nguồn dữ liệu gồm các tệp Excel báo cáo thực tế. Dữ liệu được giữ nguyên để bảo toàn cấu trúc hàng, cột, ô gộp, kiểu dữ liệu và định dạng trình bày.

### 6.2. Loại bỏ bản sao

Các tệp có nội dung hoàn toàn giống nhau được nhận diện bằng dấu vân tay số. Mỗi nhóm trùng lặp chỉ giữ một bản đại diện. Việc này hạn chế tình trạng cùng một mẫu xuất hiện ở cả tập huấn luyện và tập kiểm tra.

### 6.3. Xác định vùng bảng ban đầu

Vùng bảng được nhận diện dựa trên nhiều dấu hiệu thường gặp trong biểu thống kê:

- hàng mã cột;
- tỷ lệ ô chữ và ô số;
- chữ đậm và căn giữa;
- mật độ đường viền;
- vùng ô gộp;
- sự chuyển tiếp từ tiêu đề sang số liệu;
- dòng trống, ghi chú và khu vực chữ ký.

### 6.4. Gán nhãn và kiểm duyệt

Mỗi vùng bảng được gán năm ranh giới đã mô tả ở phần 4. Một số trường hợp đại diện được đối chiếu thủ công với kết quả mong đợi để làm nhãn chuẩn. Các mẫu có cảnh báo, nhiều bảng hoặc bố cục hiếm được ưu tiên kiểm duyệt.

### 6.5. Nhóm theo bố cục

Các trang tính có cấu trúc tương tự được gom thành cùng một nhóm dựa trên kích thước, ô gộp, hình dạng bảng và mẫu tiêu đề. Nhóm bố cục giúp đánh giá hai khả năng khác nhau:

- nhận diện tệp mới có bố cục quen thuộc;
- nhận diện tệp có bố cục chưa xuất hiện trong quá trình huấn luyện.

### 6.6. Chia tập dữ liệu

| Tập dữ liệu | Mục đích |
|---|---|
| Huấn luyện | Giúp mô hình học các đặc điểm nhận diện bảng |
| Xác thực | Chọn mô hình tốt và xác định thời điểm dừng huấn luyện |
| Kiểm tra cùng miền | Đo khả năng xử lý tệp mới có kiểu bố cục quen thuộc |
| Kiểm tra khác miền | Đo khả năng xử lý nhóm bố cục chưa xuất hiện khi huấn luyện |

Tất cả trang tính thuộc cùng một tệp được giữ trong cùng một tập. Nhóm bố cục dùng cho kiểm tra khác miền được tách khỏi các tập còn lại.

### 6.7. Tăng cường dữ liệu

Để giảm phụ thuộc vào vị trí và cách định dạng cụ thể, các mẫu huấn luyện có thể được biến đổi bằng cách:

- dịch bảng xuống một số hàng;
- dịch bảng sang phải một số cột;
- loại bỏ ngẫu nhiên một phần tín hiệu định dạng;
- che ngẫu nhiên một phần chữ trong vùng tiêu đề.

Các phép biến đổi chỉ tác động đến cấu trúc dùng để học. Chúng không tạo, thay đổi hoặc thay thế số liệu nghiệp vụ.

### 6.8. Kiểm tra chất lượng

Trước khi huấn luyện, bộ dữ liệu được kiểm tra các điều kiện:

- mỗi mẫu có mã định danh duy nhất;
- phạm vi bảng nằm trong trang tính và có thứ tự hợp lệ;
- các vùng bảng trên cùng một trang không chồng lấn;
- một tệp không xuất hiện ở nhiều tập dữ liệu;
- nhóm kiểm tra khác miền không bị trộn với tập huấn luyện;
- phép tăng cường chỉ áp dụng cho tập huấn luyện;
- dữ liệu mô tả không sao chép toàn bộ giá trị ô ra một kho riêng.

## 7. Thông tin mô hình sử dụng để học

Mỗi trang tính được biểu diễn như một lưới. Với từng ô, mô hình nhận các tín hiệu sau:

- ô có nội dung hay để trống;
- loại nội dung: chữ, số, công thức, ngày giờ hoặc giá trị đúng/sai;
- chữ đậm, căn giữa và đường viền;
- ô có thuộc vùng gộp hay không;
- vị trí tương đối của hàng và cột;
- độ dài văn bản và mẫu chữ đã chuẩn hóa;
- dấu hiệu của hàng mã cột.

Các giá trị số, ngày và công thức chỉ được biểu diễn theo loại dữ liệu trong bước học. Mô hình không học cách ghi nhớ hoặc tái tạo số liệu của từng đơn vị báo cáo.

## 8. Dữ liệu đầu ra phục vụ xem trước

Sau khi vùng bảng được xác định, hệ thống tạo một gói dữ liệu gồm:

- ma trận nội dung của bảng;
- số hàng tiêu đề và số hàng giá trị;
- danh sách ô gộp;
- danh sách cột cùng đường dẫn tiêu đề phân cấp;
- kích thước hàng, cột;
- định dạng cần thiết cho hiển thị;
- thông tin công thức và giá trị đã tính nếu có;
- độ tin cậy và cảnh báo cần kiểm tra.

Gói dữ liệu này đủ để giao diện tái hiện cấu trúc bảng gần với tệp Excel ban đầu, kể cả trường hợp có nhiều cột và nhiều tầng tiêu đề.

## 9. Lợi ích so với xử lý hoàn toàn bằng quy tắc cố định

| Tiêu chí | Xử lý bằng quy tắc cố định | Kết hợp mô hình và bộ đọc xác định |
|---|---|---|
| Vị trí bảng | Phụ thuộc mạnh vào hàng, cột đã biết | Có thể nhận diện bảng ở vị trí khác |
| Tiêu đề nhiều tầng | Cần nhiều trường hợp xử lý riêng | Nhận diện vùng tiêu đề và khai thác ô gộp |
| Bố cục mới | Dễ phải bổ sung mã xử lý | Có thể tổng quát từ các mẫu đã học |
| Độ an toàn số liệu | Đọc trực tiếp từ Excel | Vẫn đọc trực tiếp từ Excel |
| Đánh giá chất lượng | Khó có thước đo thống nhất | Có tập kiểm tra và các chỉ số định lượng |
| Khả năng mở rộng | Số quy tắc tăng theo số biểu | Mở rộng chủ yếu bằng dữ liệu mẫu đại diện |

## 10. Phạm vi áp dụng và giới hạn

Giải pháp phù hợp với các báo cáo dạng bảng có vùng tiêu đề và vùng số liệu tương đối liên tục. Khả năng nhận diện có thể giảm với trang tính dạng bảng điều khiển, biểu đồ, ảnh nhúng, bảng xoay phức tạp, nhiều vùng rời rạc hoặc ghi chú nằm sát dữ liệu.

Không thể kết luận mô hình áp dụng chính xác cho mọi loại biểu chỉ từ số lượng tệp hiện có. Mỗi nhóm bố cục mới vẫn cần ví dụ thực tế và nhãn kiểm duyệt để đánh giá khách quan.

## 11. Kết quả mong đợi

Khi hoàn thiện, hệ thống cần đạt các yêu cầu:

1. Xác định đúng bảng cần hiển thị trong phần lớn tệp Excel báo cáo thuộc phạm vi nghiệp vụ.
2. Phân biệt chính xác tiêu đề, giá trị, ghi chú và chữ ký.
3. Bảo toàn tiêu đề cha – con và ô gộp.
4. Trả nguyên số liệu có trong tệp, không phát sinh dữ liệu mới.
5. Đưa ra cảnh báo khi kết quả có độ tin cậy thấp.
6. Cho phép người dùng kiểm tra trước khi nhập dữ liệu chính thức.

## 12. Kết luận

Bộ dữ liệu được thiết kế cho bài toán nhận diện cấu trúc bảng Excel, trong đó mô hình học vị trí và vai trò của ô, còn nội dung được trích xuất trực tiếp từ tệp gốc. Cách tiếp cận này cân bằng giữa khả năng thích nghi của học máy và độ chính xác của xử lý xác định, đồng thời tạo nền tảng để xử lý nhiều biểu thống kê có header phân cấp.

