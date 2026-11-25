# TÀI LIỆU NGHIÊN CỨU TUẦN 4 – XÂY DỰNG VÀ CHUẨN HÓA BỘ DỮ LIỆU HUẤN LUYỆN AI

Thư mục này tổng hợp kết quả chuẩn bị, làm sạch, gán nhãn và làm giàu bộ dữ liệu phục vụ bài toán nhận diện cấu trúc bảng biểu Excel bằng học sâu cho Hệ thống Báo cáo điện tử eForm BTP.

## Danh mục tài liệu trong thư mục

1. **[01_BAO_CAO_XAY_DUNG_BO_DU_LIEU.md](01_BAO_CAO_XAY_DUNG_BO_DU_LIEU.md):** Báo cáo quy trình thu thập 1.232 tệp Excel thật, lọc trùng lặp, sinh 1.394 tệp biến thể cấu trúc thực tế, gán nhãn đa tác vụ và phân chia 4 tập dữ liệu chống rò rỉ (tổng cộng 2.429 trang tính sạch).
2. **[02_CAU_TRUC_DU_LIEU_VA_BO_PROMPT_MAU.md](02_CAU_TRUC_DU_LIEU_VA_BO_PROMPT_MAU.md):** Đặc tả kiến trúc biểu diễn bảng tính theo lưới đặc trưng 60 kênh, cấu trúc nhãn đa tác vụ (4 lớp ô, 5 vai trò cột, 9 cấp độ hàng) và chuẩn đầu ra JSON phân cấp.
3. **[03_KET_QUA_CHUAN_BI_DU_LIEU_VA_THU_NGHIEM.md](03_KET_QUA_CHUAN_BI_DU_LIEU_VA_THU_NGHIEM.md):** Bảng tổng hợp 11 tiêu chí kiểm định chất lượng dữ liệu, thống kê phân bố 4 phân tập và kết quả kiểm chứng mô hình trên các tập dữ liệu độc lập.

## Sơ đồ trực quan

- `diagrams/01_QUY_TRINH_NHAN_DIEN_VA_TRICH_XUAT.png` – Quy trình nhận diện cấu trúc và trích xuất bảng biểu từ tệp Excel.
- `diagrams/02_QUY_TRINH_XAY_DUNG_BO_DU_LIEU.png` – Quy trình xây dựng, làm giàu bằng tệp biến thể và kiểm định 11 tiêu chí chất lượng dữ liệu.
- `diagrams/03_BIEU_DIEN_TIEU_DE_PHAN_CAP.png` – Cấu trúc biểu diễn tiêu đề nhiều tầng và ánh xạ chỉ tiêu cha–con.
