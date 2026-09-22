# BÁO CÁO KIỂM THỬ GIAO DIỆN UPLOAD EXCEL

## 1. Kết luận

Thử nghiệm ngày **16/09/2026** có **15 PASS, 1 FAIL** trên màn hình thực tế của dự án. Frontend gửi được file Excel Raw tới ứng dụng C# chạy qua IIS Express, nhận kết quả của FastAPI thật và không tải lại trang. Các cơ chế kiểm tra file, khoá thao tác, báo lỗi và thử lại hoạt động trong các ca đã thử.

Ca không đạt là **UI15 – yêu cầu Bootstrap trên màn hình import**. Dự án có Bootstrap nhưng màn hình import không nạp thư viện này, nên không được kết luận đáp ứng đầy đủ yêu cầu HTML/CSS, Bootstrap và AJAX.

Đây là báo cáo về upload và trạng thái trao đổi dữ liệu, không phải báo cáo độ chính xác AI, lưới Handsontable, ánh xạ nghiệp vụ hoặc lưu cơ sở dữ liệu.

## 2. Môi trường và dữ liệu

| Thành phần | Điều kiện thực tế |
|---|---|
| Web frontend/C# | Ứng dụng ASP.NET MVC/Web API hiện có, chạy bằng IIS Express |
| Địa chỉ thử | `http://localhost:5077/` |
| Tuyến AJAX | `GET /api/import/health`, `POST /api/import/parse` |
| Dịch vụ AI thật | `http://127.0.0.1:8010/api/eform/extract` |
| Mô hình | `eform_excel_table_extractor_v1`, định dạng `eformmodel-1.0`, CPU |
| Trình duyệt | Microsoft Edge Chromium, chạy tự động ở chế độ headless |
| Công cụ thao tác/chụp ảnh | Playwright cài trong thư mục tạm, không thêm vào dự án |
| Kích thước hiển thị | Desktop 1.440 × 960; bố cục upload hẹp 390 × 844 |
| File Raw hợp lệ | Mẫu Sở Giáo dục và đào tạo, biểu 21a, `.xlsx`, 60.161 byte |
| Dữ liệu kiểm tra lỗi | `.txt`; file giả có phần mở rộng `.xlsx` nhưng không phải Excel; file giả 52.428.801 byte để kiểm tra chặn dung lượng |

Tên đầy đủ file Raw: `Sở Giáo dục và đào tạo_21a_TP_HTPLDN_Kết quả triển khai công tác hỗ trợ phá(...).xlsx`.

SHA-256 file Raw: `0A87CC43B43834EDA6B469609747D4A1186781DB2BFBC2419819B68A7B4CF9C7`.

Giá trị người dùng/biểu đích không được thêm trong phiên thử; mục tiêu là luồng upload/trích xuất, không phải nhập số liệu vào biểu. Không nhấn nút “Nhập dữ liệu”.

## 3. Danh sách ca kiểm thử

| Mã | Thao tác/điều kiện | Kết quả mong đợi | Kết quả thực tế | Trạng thái |
|---|---|---|---|---|
| UI01 | Mở trang qua IIS Express | HTML tải thành công; input đúng định dạng; xác nhận bị khoá | HTTP 200; nhận `.xlsx,.xlsm`; không có iframe; xác nhận bị khoá | PASS |
| UI02 | Kiểm tra trạng thái dịch vụ qua C# | Frontend nhận trạng thái ready từ AI thật | HTTP 200; `ready`; đúng tên và định dạng mô hình, CPU | PASS |
| UI03 | Nhấn hai nút chọn file | Mở trình chọn file của trình duyệt, một file mỗi lần | Cả hai nút mở file chooser, `multiple=false` | PASS |
| UI04 | Chọn file `.txt` | Báo lỗi trước khi gửi mạng | Hiện “Chỉ chấp nhận file .xlsx hoặc .xlsm.”; không thêm POST | PASS |
| UI05 | Chọn file giả lớn hơn 50 MiB | Từ chối ở frontend | 52.428.801 byte bị chặn; không thêm POST | PASS |
| UI06 | Chọn file Raw 21a | Multipart POST tới C#; nhận JSON thật | HTTP 200; Success=true; JSON 2.0; đúng tên, 60.161 byte; SHA-256 của file trong FormData trùng nguồn | PASS |
| UI07 | Giữ lượt upload đang chờ và thả file thứ hai | Khoá chọn/xác nhận; không gửi trùng | Vùng chờ hiện; ba nút bị khoá; chỉ một yêu cầu upload | PASS |
| UI08 | Theo dõi document trước và sau upload | Không tải lại hoặc điều hướng trang | Chỉ một document request; dấu nhận diện document giữ nguyên; URL không đổi | PASS |
| UI09 | Chọn lại cùng file Raw | Input được đặt rỗng sau lượt đầu, có thể gửi lại | Giá trị input rỗng; chọn lại tạo đúng một POST và nhận thành công | PASS |
| UI10 | Chọn file `.xlsx` cố ý không hợp lệ | Backend/AI từ chối; UI báo lỗi và mở lại chọn file | C# trả Success=false; lỗi Open XML thật; chọn khả dụng, xác nhận bị khoá | PASS |
| UI11 | Giả lập phản hồi HTTP 503 có JSON | UI hiển thị lỗi HTTP và giải phóng thao tác | Hiện `TEST_ONLY_HTTP_503`; chọn file được mở lại | PASS |
| UI12 | Giả lập HTTP 200 nhưng nội dung không phải JSON | UI bắt lỗi phân tích JSON, không tải lại | Hiện “Backend trả dữ liệu không đúng định dạng JSON.”; document giữ nguyên | PASS |
| UI13 | Thu viewport upload về 390 px | Nút chọn còn truy cập được, không tràn ngang | Nút nằm trong viewport; chiều rộng cuộn/viewport cùng 390 px | PASS |
| UI14 | Upload Raw thật sau các lỗi | Thử lại thành công; không phát sinh ngoại lệ JavaScript | HTTP 200; Success=true; không có `pageerror`; document giữ nguyên | PASS |
| UI15 | Kiểm tra Bootstrap được nạp ở trang import | Có Bootstrap tại chính màn hình upload | Trang chỉ nạp CSS/script Handsontable và CSS/script import riêng; không có Bootstrap | FAIL |
| UI16 | Thả workbook Raw thật vào trang | Chặn hành vi mở file; gửi đúng một POST AJAX | Sự kiện mặc định bị chặn; thêm một POST, HTTP 200; SHA-256 trùng Raw; không tải lại trang | PASS |

15/16 là tỷ lệ ca đạt trong **bộ kiểm thử này**, không phải “độ chính xác 93,75% của AI” hoặc tỷ lệ ổn định của hệ thống trên mọi môi trường.

## 4. Kiểm chứng gửi/nhận và không tải lại trang

### Gửi file gốc

Một bộ quan sát chỉ dùng trong trình duyệt kiểm thử tính SHA-256 của đối tượng `File` trong `FormData`, rồi chuyển **nguyên FormData** vào `fetch` gốc. Không đổi URL, không thay nội dung workbook và không sửa mã ứng dụng. Mã băm trùng file Raw và phản hồi AI cho biết `uploadBytes=60161`.

Thông tin text `postData` do Chromium/Playwright cung cấp không chứa đầy đủ phần byte file trong multipart của phiên này, nên không dùng kích thước text đó để suy luận file đã mất dữ liệu. Báo cáo lưu riêng thông tin header mạng, file được quan sát và kích thước file từ phản hồi thật.

### Nhận kết quả thật

| Trường phản hồi | Giá trị quan sát |
|---|---|
| HTTP | 200 |
| Success | true |
| Schema | 2.0 |
| File nguồn | Đúng tên Raw biểu 21a |
| Bộ đếm | 1 sheet; 1 bảng; 7 hàng ma trận, trong đó 1 hàng dữ liệu; 91 ô trong ma trận trả về |
| Vùng nguồn | Sheet 21a, `A2:M8` |
| Yêu cầu kiểm tra | `requiresReview=true` |

Các bộ đếm/vùng nguồn chỉ được ghi lại để nhận diện phản hồi của lần upload. **Không đánh giá** vùng nguồn có đầy đủ bảng cần nhập, 91 ô có đúng nghiệp vụ hay quan hệ phân cấp có chính xác. Mã băm `responseBodySha256` trong JSON là mã băm toàn thân phản hồi HTTP, khác với SHA-256 của file Raw/FormData. Phần vẽ/kiểm chứng lưới chưa thuộc tuần 7.

### Bằng chứng AJAX

Theo dõi request loại `document` và dấu nhận diện riêng trong `window` xác nhận document ban đầu được giữ sau các lượt upload. Chỉ có một document request trong toàn phiên; các lượt gửi file dùng POST bất đồng bộ. Bằng chứng không chỉ dựa vào cảm giác nhìn màn hình hoặc việc URL có vẻ không đổi.

## 5. Ảnh UI và nguồn gốc minh chứng

| Ảnh | Nội dung | Điều kiện chụp |
|---|---|---|
| [01_UI_CHON_FILE.png](evidence/01_UI_CHON_FILE.png) | Giao diện chưa chọn file | Trang thật qua IIS Express; không vẽ lưới |
| [02_UI_DANG_GUI_FILE.png](evidence/02_UI_DANG_GUI_FILE.png) | Tên Raw, vùng chờ, nút bị khoá | Yêu cầu thật tạm giữ trước khi truyền, sau đó gửi tới backend thật |
| [03_UI_NHAN_KET_QUA.png](evidence/03_UI_NHAN_KET_QUA.png) | Thông báo thành công có cảnh báo, tên file và bộ đếm | Chụp trực tiếp phần đầu trang, không chụp lưới bên dưới |
| [04_UI_BAO_LOI_FILE.png](evidence/04_UI_BAO_LOI_FILE.png) | Thông báo workbook không hợp lệ | Phản hồi từ C#–FastAPI thật với file lỗi có chủ đích, không giả lập response |

Ảnh là screenshot nội dung web của Microsoft Edge, không bao gồm thanh địa chỉ trình duyệt. Không chỉnh chữ, số liệu hoặc màu của ảnh. Thời gian hiển thị sau thành công do API báo ở lần chạy đó; không bao gồm lượt giữ yêu cầu và không phải phép đo hiệu năng end-to-end.

UI11/UI12 dùng phản hồi giả lập có dấu `TEST_ONLY` để thử nhánh lỗi; không dùng ảnh của chúng làm minh chứng AI thật bị lỗi. UI07 dùng giữ request có kiểm soát, không thay JSON. Mỗi trường hợp được đánh dấu trong [JSON kiểm thử nguyên bản](evidence/ui_checks_actual.json), kèm thời điểm chụp và mã băm nguồn.

## 6. Lỗi chưa đạt và giới hạn

**UI15:** Bootstrap đã có ở dự án nhưng trang import không dùng layout chung và không nạp thư viện. Muốn nghiệm thu đầy đủ tiêu chí Bootstrap phải có thay đổi frontend riêng và kiểm thử lại, không chỉ thêm câu “đã dùng Bootstrap” vào báo cáo.

Các phần chưa kiểm chứng: tương thích mọi trình duyệt, trình đọc màn hình, tải đồng thời, mạng chậm kéo dài, timeout/hủy ở client, upload thành công tại biên dung lượng tối đa, workbook `.xlsm` thật và chuẩn thiết kế của toàn hệ thống. Không kiểm chứng ánh xạ/lưu nghiệp vụ đang thiếu ở tuần 6.

Phiên thử có thể làm lưới hiện có được gọi sau khi nhận JSON vì upload và Preview đang dùng chung script. Không tạo hay sửa lưới, không chụp lưới có số liệu, không đo phân cấp/ô gộp và không tính lưới là kết quả tuần 7.

## 7. Kết luận nghiệm thu tài liệu

Bộ minh chứng xác nhận được luồng tải file bất đồng bộ và trải nghiệm trạng thái cơ bản trên ứng dụng thật, đồng thời chỉ rõ yêu cầu Bootstrap chưa đạt. Không phát sinh thay đổi nguồn sản xuất hoặc ghi vào cơ sở dữ liệu. Công cụ và file thử dung lượng chỉ nằm trong thư mục tạm và phải được dọn khi xuất bản xong tài liệu.
