# LẬP TRÌNH FRONTEND: DỰNG LƯỚI PREVIEW ĐA CẤP BẰNG HANDSONTABLE

## 1. Mục tiêu và kết quả thực hiện

Tiếp nối kết quả xây dựng giao diện tải file bất đồng bộ tại Tuần 7, nội dung trọng tâm của **Tuần 8** là:
- **Lập trình Frontend**: Ứng dụng thư viện Handsontable để vẽ lưới Preview đa cấp, trực quan hóa toàn bộ cấu trúc bảng tính và số liệu đã được mô hình AI trích xuất và ánh xạ lên giao diện web.
- **Đầu ra**: Lưới hiển thị chuẩn xác cấu trúc Excel gốc kèm số liệu (tái tạo hoàn hảo các ô gộp đa tầng ngang/dọc, cố định tiêu đề, giữ đúng định dạng số, phân cấp dòng tổng số và chi tiết).
- **Khắc phục tồn tại tuần trước**: Nạp đầy đủ thư viện **Bootstrap 3.4.1** trên chính màn hình import (giải quyết triệt để lỗi kiểm thử UI15 ghi nhận tại Tuần 7).
- **Minh chứng**: Ảnh chụp giao diện UI thật qua trình duyệt Microsoft Edge; Mã nguồn Frontend hoàn thiện trên kho lưu trữ Git; Báo cáo kiểm thử tự động với Playwright.

Kết quả kiểm thử tự động Tuần 8: **5/5 PASS (100%)**.

---

## 2. Danh mục công việc hoàn thành trong Tuần 8

| STT | Nội dung kỹ thuật | Chi tiết hiện thực | Trạng thái |
|:---:|---|---|:---:|
| 1 | **Nạp Bootstrap 3.4.1** | Tích hợp Bootstrap CSS vào [Index.cshtml](file:///c:/Users/hoang/Downloads/eform_btp/Module/ImportDoucment/ImportDocumentAPI/Views/Home/Index.cshtml), khắc phục lỗi UI15 của Tuần 7 | **Đạt** |
| 2 | **Tái tạo cấu trúc Header đa tầng** | Phân tách chính xác 6 dòng tiêu đề (`headerRows = 6`) và 78 ô gộp phức tạp của Mẫu 21a từ payload AI | **Đạt** |
| 3 | **Cấu hình Handsontable Grid** | Thiết lập `mergeCells`, `customBorders`, `renderers`, vô hiệu hóa chỉnh sửa trên hàng tiêu đề (`readOnly: true`) | **Đạt** |
| 4 | **Sticky Headers & Scrolling** | Cố định 6 hàng tiêu đề trên cùng khi cuộn dọc và cố định cột mã chỉ tiêu khi cuộn ngang | **Đạt** |
| 5 | **Định dạng số liệu & Phân cấp** | Căn lề số sang phải, chữ sang trái; gắn nhãn phân cấp hàng (`.row-grand-total`, `.row-section`) | **Đạt** |
| 6 | **Breadcrumb & Thanh công cụ** | Hiển thị Breadcrumb phân cấp cột, nhãn độ tin cậy AI (84,2%), vùng dữ liệu A2:M8 | **Đạt** |

---

## 3. Kiến trúc và Quy trình xử lý dữ liệu Frontend

![Quy trình dựng lưới Handsontable đa cấp](diagrams/01_LUONG_RENDER_HANDSONTABLE_DA_CAP.png)

*Sơ đồ quy trình tiếp nhận payload AI và tái cấu trúc lưới đa cấp bằng thư viện Handsontable.*

### Chi tiết các bước xử lý:

1. **Tiếp nhận kết quả JSON từ AI Service**:
   Phản hồi từ API chứa ma trận tọa độ `matrix` (7 hàng x 13 cột), danh sách ô gộp `merged_cells`, siêu dữ liệu phân cấp `hierarchy` và độ tin cậy `confidence = 0.842`.
2. **Phân tách tầng Header và Data**:
   Frontend tự động nhận diện ranh giới giữa phần tiêu đề biểu (dòng 0 đến dòng 5) và phần dữ liệu nghiệp vụ (dòng 6).
3. **Tính toán hình học ô gộp (Merged Cells Geometry)**:
   Chuyển đổi danh sách tọa độ gộp từ định dạng Excel (`from_row`, `to_row`, `from_col`, `to_col`) sang cấu hình của Handsontable:
   $$\text{rowspan} = \text{to\_row} - \text{from\_row} + 1, \quad \text{colspan} = \text{to\_col} - \text{from\_col} + 1$$
4. **Khởi tạo đối tượng Handsontable**:
   Áp dụng custom renderer `.eform-header-cell` cho toàn bộ các ô tiêu đề, thiết lập font chữ chuẩn `Arial / Segoe UI`, đường kẻ viền tinh tế `#cbd5e1` tương thích hoàn toàn phong cách eForm.
5. **Gắn Metadata AI Mapping**:
   Hiển thị huy hiệu độ tin cậy 84,2%, tên sheet `21a (1)`, phạm vi ô nguồn `A2:M8`, và phân loại dòng tổng số để hỗ trợ thẩm định.

---

## 4. Giao diện thực tế và Minh chứng trực quan

### 4.1. Lưới xem trước đa cấp chuẩn xác cấu trúc Excel gốc

![Giao diện Preview Handsontable](evidence/01_UI_PREVIEW_HANDSONTABLE_DA_CAP.png)

*Hình 1: Toàn cảnh giao diện Preview sau khi tải tệp Raw biểu 21a. 6 tầng header được hiển thị trung thực với 78 ô gộp.*

**Đặc điểm kỹ thuật ghi nhận trên giao diện:**
- Cấu trúc biểu 21a gồm 13 cột (A đến M) với 6 tầng tiêu đề cha–con phức tạp (bao gồm các nhóm chỉ tiêu: *Văn bản QPPL, Kế hoạch/chương trình, Tài liệu giới thiệu, Tập huấn bồi dưỡng, Đối thoại pháp luật, v.v.*) được dựng chính xác 100%.
- Các ô tiêu đề gộp không bị vỡ bố cục hay xô lệch cột.
- Cột tiêu đề cố định giúp người dùng cuộn xem dữ liệu mà không mất ngữ cảnh biểu mẫu.

### 4.2. Hiển thị số liệu đã được AI ánh xạ lên lưới

![Chi tiết số liệu AI mapping](evidence/02_UI_SO_LIEU_AI_MAP.png)

*Hình 2: Chi tiết khu vực số liệu nghiệp vụ và các thông số AI mapping.*

**Chi tiết hiển thị:**
- Số liệu tại hàng dữ liệu được căn lề phải, định dạng số nguyên phân tách rõ ràng.
- Thanh trạng thái hiển thị rõ: *“Vùng A2:M8 | 6 dòng tiêu đề | Cấu trúc đa cấp | Độ tin cậy AI: 84,2%”*.
- Thẻ tab sheet hỗ trợ chuyển đổi linh hoạt khi workbook có nhiều sheet báo cáo.

---

## 5. Mã nguồn Frontend hoàn thiện trên Git

Các thay đổi mã nguồn đã được thực hiện trực tiếp trong cấu trúc dự án eForm:

1. **[Index.cshtml](file:///c:/Users/hoang/Downloads/eform_btp/Module/ImportDoucment/ImportDocumentAPI/Views/Home/Index.cshtml)**:
   - Nạp Bootstrap CSS 3.4.1 tại thẻ `<head>`:
     ```html
     <link rel="stylesheet" href="~/Content/bootstrap.min.css" />
     ```
   - Định nghĩa vùng chứa container chuẩn Bootstrap: `<div class="container-fluid eform-shell">`.
   - Bố cục khu vực điều khiển, thanh tab sheet và thẻ chứa Handsontable `#hotGrid`.

2. **[import-preview.js](file:///c:/Users/hoang/Downloads/eform_btp/Module/ImportDoucment/ImportDocumentAPI/Scripts/import-preview.js)**:
   - Hàm `renderHandsontable(sheetData)`:
     ```javascript
     var hot = new Handsontable(container, {
         data: tableMatrix,
         colHeaders: false,
         rowHeaders: true,
         mergeCells: calculatedMergeCells,
         fixedRowsTop: headerRowsCount,
         cells: function(row, col) {
             var cellProperties = {};
             if (row < headerRowsCount) {
                 cellProperties.readOnly = true;
                 cellProperties.renderer = headerRenderer;
             } else {
                 cellProperties.renderer = dataCellRenderer;
             }
             return cellProperties;
         }
     });
     ```
   - Xây dựng cơ chế trích xuất breadcrumb khi người dùng click vào bất kỳ ô số liệu nào trên bảng.

3. **[import.css](file:///c:/Users/hoang/Downloads/eform_btp/Module/ImportDoucment/ImportDocumentAPI/Content/import.css)**:
   - Thiết lập phong cách ô tiêu đề `.eform-header-cell`:
     ```css
     .handsontable td.eform-header-cell {
         background-color: #f1f5f9 !important;
         font-weight: 600;
         color: #1e293b;
         text-align: center;
         vertical-align: middle;
         border: 1px solid #cbd5e1 !important;
     }
     ```
   - Thiết lập đường viền và hiệu ứng hover tăng trải nghiệm người dùng.

---

## 6. Đánh giá và Giới hạn nghiệm thu Tuần 8

- **Kết quả đạt được**:
  - Lưới xem trước hiển thị trung thực 100% cấu trúc workbook Excel gốc.
  - Khắc phục triệt để tồn tại UI15 từ Tuần 7 bằng việc nhúng Bootstrap 3.4.1.
  - Toàn bộ 5 ca kiểm thử T8.01–T8.05 đạt trạng thái PASS tuyệt đối.
- **Giới hạn chuyển giao**:
  - Tại Tuần 8, người dùng mới chỉ xem trước cấu trúc và số liệu; việc cho phép chỉnh sửa trực tiếp các ô dữ liệu trên lưới và lưu cache tự học được triển khai tại **Tuần 9**.
  - Việc xử lý tệp tin rác và lưu báo cáo vào cơ sở dữ liệu được hoàn thiện tại **Tuần 10**.
