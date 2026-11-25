# KẾT QUẢ KIỂM ĐỊNH BỘ DỮ LIỆU VÀ THỬ NGHIỆM MÔ HÌNH

**Đề tài:** Module AI Import file Excel thông minh cho Hệ thống Báo cáo thống kê eForm BTP 
**Giai đoạn:** Tuần 4

---

## 1. Kết quả kiểm định 11 tiêu chí toàn vẹn dữ liệu

Trước khi đưa vào huấn luyện, toàn bộ bộ dữ liệu gồm **2.429 trang tính sạch** được kiểm tra tự động qua 11 tiêu chí nghiêm ngặt. Toàn bộ 11/11 tiêu chí đều đạt trạng thái **HỢP LỆ**:

| STT | Tiêu chí kiểm định chất lượng | Kết quả đo thực tế | Trạng thái |
|:---:|---|---|---:|
| 1 | Không có lỗi đọc tệp Excel đầu vào | 0 lỗi trên 929 tệp gốc và 1.394 tệp biến thể | **ĐẠT** |
| 2 | Không trùng dấu vân tay tệp giữa các phân tập | 0 tệp giao nhau giữa Huấn luyện, Xác thực và Kiểm tra | **ĐẠT** |
| 3 | Không rò rỉ họ bố cục sang tập Kiểm tra khác miền | 0 họ bố cục trùng lặp với tập Huấn luyện | **ĐẠT** |
| 4 | Khớp nhất quán giữa vùng bảng và lưới nhãn ô | 100% trên toàn bộ 2.456 vùng bảng | **ĐẠT** |
| 5 | Không còn nhãn chân trang/tiêu đề bẩn trên tập gốc | Đã làm sạch 12/12 trường hợp, còn lại 0 | **ĐẠT** |
| 6 | Bao phủ đầy đủ nhóm trang không có bảng | 106 trang hướng dẫn/trống được gán nhãn chuẩn | **ĐẠT** |
| 7 | Bao phủ nhóm đa bảng (dọc và ngang) | 133 trang đa bảng có phân tách ranh giới rõ | **ĐẠT** |
| 8 | Bao phủ nhóm đảo thứ tự cột số liệu | 60 trang được đánh dấu tín hiệu lệch cột | **ĐẠT** |
| 9 | Bao phủ nhóm biểu trống chỉ có tiêu đề | 20 bảng tiêu đề không phát sinh dòng số liệu giả | **ĐẠT** |
| 10 | Bảo đảm cân bằng phân phối 15 biến thể cấu trúc | 1.500 trang biến thể phân bổ đều qua các nhóm khó | **ĐẠT** |
| 11 | Tính tái lập quy trình sinh và chia tập dữ liệu | Cố định hạt giống ngẫu nhiên cho kết quả nhất quán 100% | **ĐẠT** |

---

## 2. Tóm tắt kết quả thử nghiệm mô hình trên 3 tập đánh giá

Sau khi huấn luyện mô hình học sâu đa tác vụ trên bộ dữ liệu đã chuẩn hóa (16 chu kỳ huấn luyện trên CPU, chọn mô hình tốt nhất tại chu kỳ 14 với hàm mất mát xác thực `0,0022`), kết quả đánh giá thô từ mạng nơ-ron trên ba tập độc lập đạt mức vượt trội:

| Chỉ số đánh giá | Tập Xác thực (152 trang) | Tập Kiểm tra cùng miền (250 trang) | Tập Kiểm tra khác miền (133 trang) |
|---|---:|---:|---:|
| Độ chính xác phân loại từng ô | **100,00%** | **100,00%** | **99,78%** |
| F1 tiêu đề chữ | 100,00% | 100,00% | 100,00% |
| F1 hàng mã cột | 100,00% | 100,00% | 100,00% |
| F1 vùng số liệu | 100,00% | 100,00% | 99,87% |
| Macro F1 tổng hợp | **100,00%** | **100,00%** | **99,71%** |
| Độ chính xác vai trò cột | 100,00% | 100,00% | 99,82% |
| Độ chính xác cấp độ hàng | 99,93% | 99,94% | 99,85% |
| Độ trùng khớp vùng bảng (Box IoU) | 100,00% | 100,00% | 99,10% |
| **Khớp chính xác tuyệt đối vùng bảng** | **100,00% (152/152)** | **100,00% (250/250)** | **98,50% (131/133)** |
| Khớp chính xác vùng tiêu đề | 100,00% | 100,00% | 99,25% |

Kết quả này khẳng định chiến lược sinh tệp Excel biến thể thật kết hợp 60 kênh đặc trưng bất biến theo vị trí đã giúp mô hình đạt độ chính xác tuyệt đối trên các biểu mẫu trong hệ thống và duy trì năng lực tổng quát hóa rất cao (98,50% khớp vùng bảng tuyệt đối) ngay cả với những bố cục bảng biểu chưa từng gặp.
