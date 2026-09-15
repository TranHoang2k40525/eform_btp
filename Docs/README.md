# Bộ tài liệu kế hoạch AI trích xuất cấu trúc Excel cho eForm

## Phạm vi đã chốt

Dự án xây dựng một mô hình AI local có tên làm việc `EFormExcelStructureExtractor-v1`. Mô hình nhận file Excel, nhận diện vùng bảng, header nhiều tầng và vùng dữ liệu; chương trình sau đó sao chép nguyên giá trị ô để tạo dữ liệu xem trước cho Handsontable.

Mô hình không dùng LLM, không gọi dịch vụ Internet, không ánh xạ DataField, không sinh `FormConfig`, không kiểm tra nghiệp vụ và không ghi vào document. Sau khi người dùng bấm **Nhập dữ liệu**, giao diện eForm tiếp tục dùng logic hiện có để so khớp với biểu, validation và tạo `ValueData`/`SourceData`.

## Danh mục tài liệu

| File | Nội dung |
|---|---|
| `plane.txt` | Kế hoạch thực hiện theo giai đoạn, đầu việc, đầu ra và điều kiện nghiệm thu |
| `01_BAO_CAO_PHAN_TICH_CHI_TIET.md` | Báo cáo tổng thể: bài toán, hệ thống cũ, AI mới, lợi ích, giới hạn, kết quả mong đợi |
| `02_THIET_KE_DATASET_VA_HUAN_LUYEN.md` | Thiết kế dữ liệu, nhãn, mô hình, huấn luyện, đánh giá và chống rò rỉ |
| `03_SO_DO_KIEN_TRUC_VA_DATA_FLOW.md` | Sơ đồ Mermaid cho kiến trúc, dữ liệu huấn luyện và luồng suy luận |
| `Bao_cao_chi_tiet_AI_Trich_xuat_Excel.html` | Báo cáo HTML độc lập để trình bày cho nhóm và người không chuyên |
| `So_do_kien_truc_AI_Trich_xuat_Excel.svg` | Sơ đồ kiến trúc xem trực tiếp |
| `So_do_huan_luyen_va_suy_luan.svg` | Sơ đồ dataset, huấn luyện và suy luận xem trực tiếp |

## Kết luận ngắn

```text
Excel
  → parser đọc ô/merge/style
  → model nhận diện cấu trúc bảng
  → hậu xử lý xác định
  → PreviewData giữ nguyên header và value
  → Handsontable hiển thị
  → người dùng xác nhận
  → giao diện cũ mapping/validation/import
```

Giá trị trong Excel không được mô hình “đoán” hoặc sinh lại. Mô hình chỉ chọn cấu trúc; code sao chép giá trị trực tiếp để yêu cầu bảo toàn dữ liệu đạt 100%.
