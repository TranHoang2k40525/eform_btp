# Kết quả chuẩn bị dữ liệu và thử nghiệm mô hình

## 1. Mục đích đánh giá

Phần đánh giá trả lời ba câu hỏi:

1. Bộ dữ liệu có thể được sử dụng để huấn luyện hay chưa?
2. Mô hình đã học được việc phân biệt tiêu đề, giá trị và vùng ngoài bảng ở mức nào?
3. Những trường hợp nào cần tiếp tục bổ sung dữ liệu hoặc kiểm duyệt?

## 2. Quy mô dữ liệu

| Chỉ số | Kết quả |
|---|---:|
| Số tệp Excel thu thập | 1.232 |
| Số tệp duy nhất sau khi loại bản sao | 929 |
| Số bản sao được loại | 303 |
| Số tệp lỗi không đọc được | 0 |
| Số trang tính dùng làm mẫu | 929 |
| Tổng số vùng bảng được gán nhãn | 956 |
| Số trang tính có nhiều bảng | 27 |
| Số trang tính không có bảng | 0 |
| Số nhóm bố cục | 201 |
| Số nhóm bố cục chỉ có một mẫu | 142 |
| Số nhãn đã đối chiếu thủ công | 1 |
| Số biến thể tăng cường | 976 |
| Số mẫu huấn luyện tính cả tăng cường | 1.670 |
| Số mẫu có cảnh báo chỉ chứa tiêu đề | 13 |

## 3. Phân chia dữ liệu

| Tập dữ liệu | Số trang tính | Tỷ lệ xấp xỉ | Mục đích |
|---|---:|---:|---|
| Huấn luyện | 694 | 74,7% | Học tham số mô hình |
| Xác thực | 71 | 7,6% | Chọn mô hình và dừng huấn luyện |
| Kiểm tra cùng miền | 130 | 14,0% | Kiểm tra bố cục quen thuộc |
| Kiểm tra khác miền | 34 | 3,7% | Kiểm tra bố cục chưa gặp khi học |

## 4. Nguồn nhãn

| Cách xác định nhãn | Số mẫu |
|---|---:|
| Nhận diện hàng mã cột chuẩn | 914 |
| Nhận diện chuỗi mã số âm | 10 |
| Nhận diện chuỗi mã số dương | 4 |
| Đối chiếu thủ công với kết quả mong đợi | 1 |

Phần lớn nhãn hiện được tạo tự động từ cấu trúc Excel. Điều này giúp tạo dữ liệu nhanh nhưng cũng làm tăng yêu cầu kiểm duyệt độc lập trước khi dùng kết quả để kết luận chất lượng sản xuất.

## 5. Kiểm tra kỹ thuật đã đạt

- Không có mã mẫu bị trùng.
- Mỗi tệp chỉ thuộc một tập dữ liệu.
- Nhóm bố cục dùng để kiểm tra khác miền không xuất hiện trong tập huấn luyện.
- Mọi vùng bảng nằm trong kích thước trang tính.
- Các vùng bảng trên cùng một trang không chồng lấn.
- Phép tăng cường chỉ được sử dụng trong tập huấn luyện.
- Tham số tăng cường nằm trong phạm vi cho phép.
- Dữ liệu mô tả không sao chép toàn bộ giá trị ô.

Kết quả kiểm tra cho thấy bộ dữ liệu có thể được nạp vào quy trình huấn luyện. Đây là kết luận về tính hợp lệ kỹ thuật, không đồng nghĩa với việc toàn bộ nhãn đã chính xác tuyệt đối.

## 6. Trường hợp mẫu đã đối chiếu

Một biểu báo cáo hỗ trợ pháp lý cho doanh nghiệp được chọn làm trường hợp kiểm chứng. Trang tính có 10 hàng và 13 cột. Kết quả đối chiếu xác nhận:

| Nội dung | Phạm vi |
|---|---|
| Toàn bộ bảng cần hiển thị | A2:M8 |
| Phần tiêu đề | A2:M7 |
| Phần giá trị | A8:M8 |

Trường hợp này được dùng để kiểm tra đồng thời tọa độ vùng bảng, ranh giới tiêu đề, ô gộp và dữ liệu xem trước.

## 7. Cấu hình thử nghiệm

| Thành phần | Giá trị |
|---|---:|
| Loại mô hình | Mạng phân đoạn lưới ô, ba lớp |
| Số tham số học | 379.107 |
| Số vòng huấn luyện dự kiến | 20 |
| Số vòng đã chạy | 14 |
| Vòng có kết quả xác thực tốt nhất | 9 |
| Số mẫu xử lý trong một lượt | 8 |
| Số mẫu huấn luyện tính cả tăng cường | 1.670 |

Quá trình huấn luyện dừng sớm khi kết quả xác thực không tiếp tục cải thiện. Mô hình tốt nhất được lưu lại và nạp lại thành công để chạy thử.

## 8. Giải thích các chỉ số

| Chỉ số | Ý nghĩa |
|---|---|
| F1 tiêu đề | Mức cân bằng giữa nhận diện đúng và bỏ sót các ô tiêu đề |
| F1 giá trị | Mức cân bằng giữa nhận diện đúng và bỏ sót các ô dữ liệu |
| Mức giao nhau của vùng | Tỷ lệ chồng khớp giữa vùng dự đoán và vùng mong đợi |
| Vùng chính xác tuyệt đối | Tỷ lệ mẫu có đủ năm ranh giới hoàn toàn trùng khớp |

Chỉ số theo ô cao không bảo đảm ranh giới bảng hoàn toàn đúng. Chỉ cần lấy thừa một dòng ghi chú thì hàng trăm ô bên trong vẫn có thể đúng nhưng kết quả vùng chính xác tuyệt đối vẫn bị tính sai.

## 9. Kết quả thử nghiệm

| Tập đánh giá | Vùng chính xác tuyệt đối | Mức giao nhau của vùng | F1 tiêu đề | F1 giá trị |
|---|---:|---:|---:|---:|
| Xác thực | 69,01% | 94,33% | 99,92% | 99,68% |
| Kiểm tra cùng miền | 55,38% | 85,62% | 98,71% | 98,79% |
| Kiểm tra khác miền | 97,06% | 99,96% | 100,00% | 99,98% |

## 10. Phân tích kết quả

Mô hình phân biệt ô tiêu đề và ô giá trị khá tốt trên các tập hiện có. Tuy nhiên, độ chính xác tuyệt đối của ranh giới trên tập kiểm tra cùng miền còn thấp hơn nhiều so với chỉ số theo ô. Điều này cho thấy sai số chủ yếu tập trung ở mép bảng, đặc biệt là hàng cuối.

Kết quả của tập kiểm tra khác miền cao hơn tập cùng miền nhưng chưa đủ để kết luận khả năng tổng quát đã tốt. Tập này mới có 34 trang tính và phần lớn nhãn được tạo tự động, do đó cần mở rộng và kiểm duyệt thủ công trước khi công bố.

## 11. Ví dụ lỗi được phát hiện

Trong một tệp báo cáo chứng thực cấp xã, phạm vi mong đợi là `A3:I7` nhưng mô hình dự đoán `A3:I10`. Kết quả đã lấy thêm:

- một dòng trống;
- dòng ghi chú;
- khu vực chữ ký xác nhận.

Ví dụ này cho thấy việc chỉ nhìn vào tỷ lệ nhận diện ô là chưa đủ. Bộ dữ liệu cần thêm các mẫu có ghi chú và chữ ký nằm gần bảng để mô hình học rõ hơn ranh giới kết thúc.

## 12. Đánh giá mức độ sẵn sàng

| Tiêu chí | Trạng thái |
|---|---|
| Có đủ tập huấn luyện, xác thực và hai tập kiểm tra | Đạt |
| Có tăng cường dữ liệu không làm thay đổi số liệu | Đạt |
| Có kiểm tra trùng lặp và rò rỉ dữ liệu | Đạt |
| Có thể huấn luyện và chạy thử mô hình | Đạt |
| Có tập nhãn chuẩn được kiểm duyệt đủ lớn | Chưa đạt |
| Có mẫu trang tính không chứa bảng | Chưa đạt |
| Đã chứng minh chính xác trên mọi loại biểu | Chưa đạt |
| Đủ căn cứ triển khai không cần người kiểm tra | Chưa đạt |

Kết luận hiện tại: bộ dữ liệu đủ để chứng minh tính khả thi và tiếp tục huấn luyện, nhưng cần hoàn thiện nhãn chuẩn trước khi cam kết chất lượng trên dữ liệu thực tế diện rộng.

## 13. Kế hoạch hoàn thiện

1. Tạo tập nhãn chuẩn được kiểm duyệt thủ công, bao phủ các nhóm bố cục quan trọng.
2. Bổ sung trang tính không có bảng để đo khả năng nhận diện nhầm.
3. Rà soát 13 mẫu chỉ có tiêu đề và 27 mẫu chứa nhiều bảng.
4. Bổ sung dữ liệu thật cho các nhóm bố cục chỉ có một mẫu.
5. Ưu tiên trường hợp có ghi chú, dòng trống và chữ ký sát bảng.
6. Đánh giá lỗi riêng theo từng ranh giới: trên, dưới, trái, phải và hàng cuối tiêu đề.
7. Huấn luyện lại và chỉ công bố kết quả dựa trên tập kiểm tra có nhãn do con người xác nhận.

## 14. Kết luận

Thử nghiệm xác nhận phương pháp có khả năng nhận diện cấu trúc bảng và bảo toàn tiêu đề phân cấp. Kết quả đồng thời chỉ ra ranh giới cuối bảng là vấn đề cần ưu tiên. Hướng hoàn thiện phù hợp là tăng chất lượng và độ đại diện của nhãn, đặc biệt với bảng có ghi chú, chữ ký, nhiều vùng và bố cục hiếm.

