# TÍCH HỢP MODULE AI IMPORT EXCEL VÀO HỆ THỐNG eFORM (eform_nq) THEO KIẾN TRÚC MICROSERVICE

## 1. Mục tiêu và kết luận hiện tại

Sau 11 tuần, Module AI Import Excel đã có đủ ba phần: dịch vụ AI (FastAPI), backend .NET (ImportDocumentAPI) và trang xem trước độc lập. Tuy vậy, cán bộ vẫn chưa dùng được module ngay trong màn hình báo cáo của eForm. Giai đoạn tích hợp đặt ra bốn yêu cầu:

1. Trên thanh công cụ báo cáo của eform_nq chỉ có **một nút "Nhập file"**. Bấm vào sẽ mở hộp nhập, trong đó có hai nút: **Nhập file Excel** (cách nhập cũ, giữ nguyên) và **Nhập File Excel AI**. Cán bộ chưa tin kết quả AI vẫn còn cách nhập như trước, ngay trong cùng một hộp.
2. Mọi phần liên quan đến máy chủ nhập Excel bằng AI (gọi AI, kết nối cơ sở dữ liệu, lưu nhật ký) đều thuộc eform_btp. eform_nq chỉ cung cấp đủ thông tin để xác định người dùng. Hai bên là **hai service độc lập** (microservice).
3. Chỉ người dùng đã đăng nhập eForm mới gọi được service nhập AI. Backend eform_nq gần như không bị sửa.
4. Chạy được trên IIS của máy phát triển: eForm tại `http://hoangtv.dev.com/`, service nhập tại `http://import_ai_hoangtv.dev.com/`, cùng mô hình AI thật.

Kết luận sau kiểm thử ngày 18/11/2026:

- Dịch vụ AI **thật** (mô hình `eform_excel_table_extractor_v1`) đã chạy ở `127.0.0.1:8010` và trả trạng thái `ready` qua `http://import_ai_hoangtv.dev.com/api/import/health`.
- Phía service, trên IIS và với AI thật, đạt **15/15 ca kiểm thử** về xác thực, CORS, `parse` và `save`.
- Hộp nhập được mở từ IIS (`hoangtv.dev.com`) và chạy hết luồng với file thật "Sở Tư pháp Thành phố Hà Nội – 04c":
  - Đọc file trong khoảng 1,9 giây.
  - Kết quả: vùng bảng A2:X157, 6 dòng tiêu đề, 150 dòng số liệu, độ tin cậy 100%.
  - Sửa ô, ghép vào biểu, nhập dữ liệu và ghi lịch sử đều thành công.
- API cấp token trên IIS đã được kiểm tra: khi chưa đăng nhập, API trả 401 "Bạn chưa đăng nhập."
- Đã kiểm thử bằng **tài khoản đăng nhập thật cấp Sở Tư pháp tỉnh Bắc Ninh** trên biểu **11b/TP/LSTN** với hai file Excel thật của Sở Tư pháp TP. Hồ Chí Minh (mục 9.3):
  - File đúng thứ tự cột: Nhập File Excel AI cho 2.417 dòng, **0 lỗi**, khớp từng ô với file. Cách nhập cũ nạp cả dòng ghi chú cuối file thành dòng 2.419 và báo 8 lỗi.
  - File bị đảo cột: cách nhập cũ đặt sai cột, sinh 2.434 lỗi, doanh thu tổng chỉ còn khoảng 14,8 tỷ thay vì 1.112,8 tỷ. Nhập File Excel AI phát hiện cột không khớp tiêu đề và **khóa bước Tiếp tục**, không cho nhập số liệu sai.
- Đã thử với **119 file Excel** sinh từ 10 biểu, gồm 12 kiểu biến đổi: bỏ ô gộp, không kẻ khung, đảo cột, nhiều sheet, hai bảng… (mục 9.4). Sau các lần sửa, mô hình đạt **119/119**. Chạy lại 300 file thật: 20 file cho kết quả tốt hơn, không file nào kém đi.

## 2. Kiến trúc hai service

| Service | Công nghệ | Trách nhiệm trong luồng nhập file |
|---|---|---|
| eform_nq (hệ thống có sẵn), `http://hoangtv.dev.com` | ASP.NET MVC 5 / Web API 2, .NET 4.5, IIS, MySQL `eform_nq` | Cấp JWT cho người dùng đang đăng nhập; mở hộp nhập; lưu số liệu vào báo cáo theo luồng sẵn có (validate, khóa kỳ, phân quyền) |
| ImportDocumentAPI (eform_btp), `http://import_ai_hoangtv.dev.com` | ASP.NET Web API 2, .NET 4.8, Ninject, Entity Framework 6, MySQL `datamart_eform_nq` | Kiểm tra JWT và CORS; nhận file; gọi dịch vụ AI; trả kết quả; lưu nhật ký nhập AI vào `import_records` |
| Dịch vụ AI, `http://127.0.0.1:8010` (chỉ nghe nội bộ) | Python 3.10, FastAPI, Uvicorn, PyTorch (CPU) | Nhận workbook, trả vùng bảng, dòng tiêu đề, ô gộp và độ tin cậy theo JSON schema 2.0 |

Nguyên tắc phân vai được giữ từ tài liệu đề xuất tuần 2:

- Dịch vụ AI không truy cập cơ sở dữ liệu và không mở ra ngoài máy.
- ImportDocumentAPI **không ghi vào bảng nghiệp vụ** của eForm. Nó chỉ ghi nhật ký trong bảng riêng.
- Số liệu chỉ vào báo cáo khi cán bộ bấm **Xác nhận & nhập**, và đi qua đúng luồng lưu của eform_nq.

Trình duyệt gọi thẳng ImportDocumentAPI qua CORS, không đi vòng qua eform_nq. Nhờ vậy backend eform_nq không phải chuyển tiếp file Excel và không cần biết địa chỉ dịch vụ AI.

## 3. Xác thực giữa hai service

### 3.1. Cấp token (eform_nq)

API `POST /webapi/aiimport/token` nằm trong `AiImportController`.

- Controller kế thừa `EgovApiBaseController`, nên đi qua bộ lọc xác thực toàn cục `EgovApiAuthorizeAttribute` (cookie phiên).
- Người dùng được lấy từ `UserBll.CurrentUser` phía máy chủ, không nhận từ client.

| Claim | Giá trị |
|---|---|
| `iss` | `eform_nq` |
| `aud` | `eform_import_ai` |
| `sub` | Mã người dùng (`UserId`) |
| `name` | Tên đăng nhập |
| `iat`, `nbf`, `exp` | Thời điểm cấp, hiệu lực, hết hạn (mặc định 15 phút, giới hạn 1–60 phút) |
| `jti` | Mã ngẫu nhiên của token |

- Token được ký bằng **HS256** với khóa `AiImportJwtSecret` (tối thiểu 32 ký tự).
- Phản hồi có dạng `{ success, token, expiresIn, serviceUrl }`, kèm header `Cache-Control: no-store`.
- .NET 4.5 không có `DateTimeOffset.ToUnixTimeSeconds`, nên thời gian Unix được tính thủ công.

### 3.2. Kiểm tra token (ImportDocumentAPI)

`EformGatewayHandler` là một `DelegatingHandler`, được đăng ký trước định tuyến Web API:

- **CORS**:
  - Chỉ origin nằm trong `EformAllowedOrigins` mới gọi được.
  - Preflight `OPTIONS` từ origin hợp lệ trả 204, cho phép header `Authorization, Content-Type`.
  - Preflight từ origin lạ trả 403.
- **Xác thực**: mọi đường dẫn `/api/import/*` (trừ `/api/import/health`) phải có header `Authorization: Bearer <jwt>`. `EformJwtValidator`:
  - chỉ chấp nhận `alg = HS256`;
  - so chữ ký theo thời gian cố định;
  - kiểm tra `iss`, `aud`, `exp`/`nbf` (cho lệch đồng hồ 60 giây);
  - yêu cầu `sub` không rỗng.
  
  Token sai bị từ chối với mã 401 và JSON `{ success: false, message }`.
- Người dùng hợp lệ được đặt vào `request.Properties["EformUser"]`. Controller **luôn lấy `UserId`/`UserName` từ đây** và bỏ mọi giá trị do client tự gửi.
- `ImportAuthRequired = false` chỉ dùng cho trang demo độc lập của module.

## 4. Hợp đồng API

| API | Mục đích | Ghi chú |
|---|---|---|
| `POST /webapi/aiimport/token` (eform_nq) | Cấp JWT | Dùng cookie phiên; trả `serviceUrl` để trình duyệt biết địa chỉ service |
| `GET /api/import/health` | Kiểm tra AI sẵn sàng | Không cần token; trang hiển thị "Sẵn sàng" hoặc "Chưa kết nối được" |
| `POST /api/import/parse` | Gửi file để AI đọc | Multipart gồm `file`, `originalFileName`, `documentId`, `autoSave=false`; trả `aiResult` (schema 2.0) |
| `POST /api/import/save` | Ghi nhật ký nhập AI | JSON `{ documentId, fileName, sheetName, sourceRange, aiModelVersion, source, tableData, corrections }`; bắt buộc có `documentId` và `tableData` |

Khi gọi từ eForm, trang gửi `autoSave=false`, nên `parse` **không tự lưu**. Bản ghi chỉ được tạo sau khi cán bộ xác nhận nhập. Trang demo cũ không gửi trường này nên vẫn giữ hành vi tự lưu như trước.

## 5. Luồng giao diện trên eform_nq

Hộp nhập giữ nguyên bố cục, màu sắc và cách đặt chữ của hộp "Nhập file Excel" sẵn có. Điểm khác duy nhất là có thêm một nút và một nhãn trạng thái nhỏ.

1. Thanh công cụ báo cáo có **một nút "Nhập file"**, nằm đúng vị trí và giữ đúng biểu tượng của nút "Nhập file Excel" cũ. Nút ẩn hoặc hiện theo quyền nhập file của báo cáo, như trước.
2. Bấm **Nhập file** sẽ mở hộp "Import dữ liệu Excel". Thanh thao tác gồm:
   - các nút cũ **Hướng dẫn**, **Tải file mẫu**;
   - hai nút nhập: **Nhập file Excel** (cách cũ, nhận .xlsx/.xls) và **Nhập File Excel AI** (nhận .xlsx/.xlsm);
   - nhãn trạng thái **Sẵn sàng** hoặc **Chưa kết nối được**.
   
   Câu hướng dẫn: "Tải file mẫu, điền số liệu rồi chọn cách nhập để kiểm tra trước khi nhập."
3. **Nhập file Excel** chạy đúng luồng cũ (chọn sheet, ghép dòng, kiểm tra, nhập) và không gọi AI. Nếu trước đó cán bộ đã đọc file bằng AI, phiên AI đó bị hủy, nên lần nhập này không bị ghi nhầm vào lịch sử nhập AI.
4. **Nhập File Excel AI** gửi file cho service. Đọc xong, hộp **Xem trước dữ liệu đọc từ file** hiện từng bảng, kèm vùng bảng, số dòng tiêu đề, số dòng số liệu và độ tin cậy.
   - Bảng giữ nguyên ô gộp.
   - Dòng tiêu đề chỉ xem được; ô số liệu sửa được.
   - Ô nào bị sửa sẽ được tô màu và đếm, ví dụ "Đã sửa 1 ô".
5. Bấm **Tiếp tục** để mở hộp **Chọn sheet để nhập** quen thuộc. Từ đây dữ liệu đi đúng luồng của cách nhập cũ: dò dòng mã cột, cắt dòng số liệu, kiểm tra lỗi và cảnh báo, rồi bấm **Nhập dữ liệu** → **Xác nhận & nhập**.
6. Ngay trước khi gửi số liệu về trang báo cáo, trang gọi `/api/import/save` để ghi lịch sử nhập (bảng đã ghép và các ô đã sửa). Nếu ghi lỗi hoặc quá 10 giây thì **việc nhập vẫn tiếp tục**, và trạng thái chuyển thành "Chưa lưu được lịch sử nhập".
7. Khi có lỗi, hộp **Thông báo** chỉ hiện một câu ngắn, dễ hiểu, ví dụ "Không kết nối được máy chủ. Vui lòng thử lại sau hoặc liên hệ quản trị hệ thống.", kèm nút **Nhập file Excel** để chuyển sang cách nhập cũ.
   - Giao diện **không hiển thị** địa chỉ service, cổng, tên khóa cấu hình hay tên mô hình.
   - Chi tiết kỹ thuật chỉ ghi vào console của trình duyệt, với tiền tố `[NhapExcelAI]`, để quản trị tra cứu.

## 6. Cơ sở dữ liệu

- Bảng `import_records` nằm trong schema `datamart_eform_nq`.
- `ImportDbContext` lấy chuỗi kết nối `ImportDb` rồi đổi tên database theo khóa `EformDataSource`.
- Script tạo bảng: `Module/ImportDoucment/Database/20261118_import_records_eform_service.sql`. Script dùng `CREATE TABLE IF NOT EXISTS` nên chạy lại vẫn an toàn.

| Cột | Ý nghĩa |
|---|---|
| `Id` | Khóa tự tăng |
| `DocumentId` | Báo cáo eForm được nhập |
| `UserId` | Người nhập, lấy từ claim `sub` |
| `FileName` | Tên file Excel |
| `JsonData` | `userName`, `source = EFORM_NQ`, sheet, vùng bảng, mô hình, bảng đã ghép theo từng biểu, danh sách ô đã sửa |
| `CreatedAt` | Thời điểm ghi |

Kết nối luôn ép `CharacterSet = utf8mb4`. Nếu không, MySQL 5.7 dùng mặc định latin1 và chữ tiếng Việt trong `JsonData` bị ghi thành `?`.

## 7. Thay đổi mã nguồn

**eform_nq** (nhánh `hoangtest`, chưa commit):

| Tệp | Thay đổi |
|---|---|
| `Solution/Api/Controller/AiImportController.cs` | Mới: API cấp JWT |
| `Solution/Solution.csproj` | Thêm 1 dòng `Compile` |
| `Solution/web.config` | Thêm `AiImportServiceUrl` (`http://import_ai_hoangtv.dev.com`), `AiImportJwtSecret`, `AiImportTokenMinutes` |
| `templates/document/toolbar.html` | Đổi nhãn nút "Nhập file Excel" thành **Nhập file** (1 dòng) |
| `views/document/toolbar.js` | Nút **Nhập file** mở hộp nhập có cả hai cách (1 dòng). `_getNodeCurrentId` ưu tiên `NodeCurrentId` của báo cáo khi khác 0, để nút không bị ẩn nhầm ở báo cáo mở từ trang tổng hợp |
| `views/document/document.js` | `_importExcelNew(options)` nhận `mode: 'ai'` và thêm `&mode=ai` vào địa chỉ hộp nhập |
| `templates/document/document-import-excel-handsel.html` | Thêm nút **Nhập File Excel AI**, nhãn trạng thái, hộp xem trước và sửa, ghi lịch sử nhập, hộp thông báo lỗi; đổi nhãn nút cũ thành **Nhập file Excel** khi mở từ nút "Nhập file". Bổ sung sau kiểm thử 11b: (1) `_fillColumnFormulas` điền công thức theo dòng của cột (ví dụ cột (3) "Tổng số việc" = (4)+(5)+(6)) vào ô trống, giống khi mở báo cáo; áp dụng cho cả hai cách nhập; (2) bộ tính nhanh công thức SUM cho bảng từ 500 dòng (khoảng 220 giây xuống 0,8 giây với biểu 11b); (3) khi AI báo cột lệch tiêu đề thì khóa nút **Tiếp tục**, ô "Độ tin cậy" hiện "Cột không khớp tiêu đề". Bổ sung sau thử nghiệm mục 9.4: (4) `_aiReorderByCode` xếp lại cột số liệu theo dòng số thứ tự cột (chỉ dùng mã số, bỏ qua cột nhãn A/B/STT) và hiện thông báo các cột đã xếp lại; (5) `_aiDefaultSheets` chọn sẵn bảng chính trong hộp chọn sheet, dựa vào `!aiValueRows`, `!aiConfidence`, `!aiCols` gắn vào từng sheet AI |
| `Scripts/solution.egov/config.js` | Tăng `urlArgs` để trình duyệt tải lại template. **Chỉ để chạy local, không commit.** |

**eform_btp**:

| Tệp | Thay đổi |
|---|---|
| `ImportDocumentAPI/Security/EformJwtValidator.cs`, `EformGatewayHandler.cs` | Mới: kiểm tra JWT, CORS |
| `ImportDocumentAPI/App_Start/WebApiConfig.cs` | Đăng ký `EformGatewayHandler` |
| `ImportDocumentAPI/Controllers/ImportController.cs` | `parse` lấy người dùng từ token, có `autoSave`; thêm `save` |
| `ImportDocumentAPI/Web.config` | `EformAllowedOrigins` thêm `http://hoangtv.dev.com` |
| `ImportDocument.Application` (`SaveReportDto`, `ImportService`) | Thêm `UserName`, `Source` vào nhật ký |
| `ImportDocument.Infrastructure/ImportDbContext.cs` | Ép `utf8mb4` |
| `ImportDocument.Infrastructure.csproj`, `NinjectConfig.cs` | Sửa 2 lỗi build có sẵn: thiếu tham chiếu MySql, thiếu `using Ninject.Web.Common` |
| `Database/20261118_import_records_eform_service.sql` | Script tạo bảng nhật ký |
| `Module/AI Import/API/run_local.ps1` | Tự bỏ qua `.venv` hỏng và chọn bản Python đầu tiên chạy được, có đủ `torch`, `uvicorn`, `fastapi`, `openpyxl` |
| `Module/AI Import/Train/training_core.py` | Chọn cột tên dòng theo nội dung (cột chữ, không phải cột STT/số liệu), trả `labelColumnIndex`. Kiểm tra từng cột số liệu có khớp tiêu đề không (`_column_issues`): cột tên dòng nằm sai chỗ, cột tiêu đề số nhưng chứa chữ… Trên 300 file biểu 10b/11b/15b/21b: sửa đúng 17 trường hợp chọn sai cột tên dòng, không báo nhầm file đúng. Bổ sung sau thử nghiệm mục 9.4: `split_table_at_gaps` chỉ cắt bảng khi phần dưới không còn số liệu cùng cấu trúc; `merge_header_fragments` ghép mảnh tiêu đề vào bảng; `refine_table_bounds` giữ dòng có ô gộp dọc, mở rộng tiêu đề lên tối đa 3 dòng, đếm số dạng chuỗi, bỏ cột trống ở hai rìa; sửa biểu thức nhận diện "kỳ báo cáo", "Ghi chú"; ghi chú khi thứ tự cột khác chuẩn |
| `Module/AI Import/API/main.py` | Trả thêm `labelColumnIndex`, `columnIssues`, `columnNotes` cho từng bảng; bảng có cột lệch được đặt `requiresReview` và thêm cảnh báo dễ hiểu |

## 8. Cấu hình và triển khai trên IIS

### 8.1. Cấu hình

| Nơi | Khóa | Giá trị hiện tại / lưu ý |
|---|---|---|
| eform_nq `web.config` | `AiImportServiceUrl` | `http://import_ai_hoangtv.dev.com`: địa chỉ mà **trình duyệt** gọi được, cùng http/https với eForm |
| | `AiImportJwtSecret` | Trùng `EformJwtSecret`. Đây là khóa mẫu cho môi trường dev, **phải đổi trước khi triển khai thật** |
| | `AiImportTokenMinutes` | 15 (1–60) |
| ImportDocumentAPI `Web.config` | `EformJwtSecret`, `EformJwtIssuer`, `EformJwtAudience` | Khóa chung; `eform_nq`; `eform_import_ai` |
| | `EformAllowedOrigins` | `http://hoangtv.dev.com,http://localhost:64898,https://localhost:44300,http://localhost` |
| | `ImportAuthRequired` | `true`; chỉ đặt `false` cho trang demo độc lập |
| | `ImportDb`, `EformDataSource`, `AiUrl` | MySQL local; `datamart_eform_nq`; `http://127.0.0.1:8010/api/eform/extract` |

Hai tên miền được khai báo trong `C:\Windows\System32\drivers\etc\hosts`, cùng trỏ `127.0.0.1`. Hai site IIS trỏ thẳng vào thư mục mã nguồn:

| Tên miền | Thư mục |
|---|---|
| `hoangtv.dev.com` | `D:\HoangTV\eform_nq\Solution` |
| `import_ai_hoangtv.dev.com` | `ImportDocumentAPI` |

Vì vậy, sửa C# xong cần build lại thì IIS mới nạp DLL mới. Sửa `web.config` thì IIS tự khởi động lại ứng dụng.

### 8.2. Chạy dịch vụ AI

Dịch vụ AI không chạy trong IIS mà là một tiến trình Python riêng. Tệp khởi động là `Module/AI Import/API/main.py` (FastAPI). Mô hình nằm ở `Module/AI Import/Train/Output_Local/eform_excel_table_extractor_v1.eformmodel`.

```powershell
cd "D:\HoangTV\eform_btp1\eform_btp\Module\AI Import\API"
powershell -ExecutionPolicy Bypass -File .\run_local.ps1
```

Cách `run_local.ps1` chọn Python:

1. Thử lần lượt `eform_btp\.venv` rồi `Train\.venv`.
2. Nếu cả hai hỏng thì dùng Python cài trên máy. Hai `.venv` hiện có đều hỏng vì tạo bằng uv trên máy cũ.

Trên máy này, script chọn `C:\Users\HungNTH\AppData\Local\Programs\Python\Python310\python.exe` (torch 2.12 CPU, fastapi 0.115).

Để chạy nền (ẩn cửa sổ, ghi log), dùng lệnh sau:

```powershell
$api = "D:\HoangTV\eform_btp1\eform_btp\Module\AI Import\API"
Start-Process python.exe -ArgumentList "-m","uvicorn","main:app","--app-dir","`"$api`"","--host","127.0.0.1","--port","8010" `
  -WorkingDirectory $api -WindowStyle Hidden -RedirectStandardOutput "$api\ai_service.log" -RedirectStandardError "$api\ai_service.err.log"
```

Kiểm tra dịch vụ đã sẵn sàng:

- `http://127.0.0.1:8010/health`: dịch vụ AI.
- `http://import_ai_hoangtv.dev.com/api/import/health`: kiểm tra qua service nhập.

Cả hai phải trả `"status":"ready"`. Sau khi khởi động lại máy, cần chạy lại lệnh trên. Nếu muốn dịch vụ tự chạy, có thể đăng ký nó trong Task Scheduler với trigger "At startup".

### 8.3. Thứ tự khởi động

1. Chạy script SQL (một lần).
2. Chạy dịch vụ AI như mục 8.2.
3. Kiểm tra hai site IIS đang chạy.
4. Đăng nhập `http://hoangtv.dev.com/`, mở một báo cáo, bấm **Nhập file**. Nếu thanh công cụ vẫn hiện hai nút cũ, trình duyệt đang dùng template trong bộ nhớ đệm: bấm Ctrl+F5.

## 9. Kiểm thử

### 9.1. Kiểm thử service trên IIS với AI thật (15/15 đạt)

| Nhóm | Ca kiểm thử | Kết quả |
|---|---|---|
| Health | Gọi không cần token; trả CORS cho origin `http://hoangtv.dev.com` | Đạt (2 ca) |
| CORS | Preflight origin hợp lệ → 204; origin lạ → 403 | Đạt (2 ca) |
| Xác thực `parse` | Không có token / sai chữ ký / hết hạn / sai `aud` → 401 | Đạt (4 ca) |
| `parse` hợp lệ | File Hà Nội 04c: có `aiResult` schema 2.0; `autoSave=false` không lưu; `userId` lấy từ token; có header CORS | Đạt (4 ca) |
| `save` | Token hợp lệ → có `recordId` và lưu đúng người trong token; không có token → 401; thiếu `documentId` → từ chối | Đạt (3 ca) |

Ngoài 15 ca trên, `POST http://hoangtv.dev.com/webapi/aiimport/token` khi chưa đăng nhập trả 401.

### 9.2. Kiểm thử giao diện trên IIS

Môi trường:

- Trình duyệt Chromium.
- Hộp nhập mở trực tiếp từ `http://hoangtv.dev.com`.
- Dữ liệu báo cáo thật `3dd552eb-…` trong CSDL local.
- File thật `Sở Tư pháp Thành phố Hà Nội_04c_TP_PBGDPL…xlsx`.
- ImportDocumentAPI và dịch vụ AI thật.

| Bước | Kết quả |
|---|---|
| Mở hộp | Tiêu đề "Import dữ liệu Excel"; có các nút Hướng dẫn, Tải file mẫu, Nhập file Excel, Nhập File Excel AI; trạng thái "Sẵn sàng" |
| Nhập File Excel AI | Khoảng 1,9 giây; vùng A2:X157, 6 dòng tiêu đề, 150 dòng số liệu, độ tin cậy 100%; cảnh báo "Có 4 dòng cần kiểm tra lại." |
| Sửa 1 ô | Ô tô màu; "Đã sửa 1 ô" |
| Tiếp tục → Chọn sheet để nhập → ghép | 149 dòng, 0 lỗi, nút "Nhập dữ liệu" bật |
| Nhập dữ liệu → Xác nhận & nhập | Trang báo cáo nhận `IMPORT_EXCEL_DONE`; trạng thái "Đã lưu lịch sử nhập"; `import_records` có bản ghi đúng `DocumentId` |
| Nhập file Excel (cách cũ) | Mở thẳng "Chọn sheet để nhập", không gọi AI |
| Mất kết nối service | Trạng thái "Chưa kết nối được"; hộp Thông báo có câu ngắn, không lộ địa chỉ hay cổng, kèm nút "Nhập file Excel" |

Biểu dùng để thử ("Tổng hợp số liệu thống kê về kết quả thẩm định…") khác mẫu 04c. Vì vậy các ô số liệu ghép vào biểu hiện "-": bước kiểm thử này chỉ xác nhận luồng chạy đúng, chưa kiểm tra độ khớp nghiệp vụ.

Lỗi phát hiện và sửa trong quá trình kiểm thử:

- **Mã báo cáo bị thiếu trong nhật ký.** Hàm lấy mã báo cáo chỉ đọc dữ liệu của chính iframe, trong khi ở eForm dữ liệu nằm ở trang cha (`window.parent.__documentData`). Hậu quả là nhật ký luôn bị từ chối vì thiếu `documentId`. Hàm đã được sửa để đọc theo đúng thứ tự nguồn của trang.
- **Chữ tiếng Việt trong nhật ký bị ghi thành `?`.** Đã sửa bằng cách ép `utf8mb4`.
- **Lưới xem trước chỉ vẽ 8 dòng đầu.** Bảng được dựng khi hộp thoại còn đang hiện dần lên. Đã sửa bằng cách vẽ lại lưới sau khi hộp thoại hiện xong; lần mở đầu tiên đã thấy đủ các dòng trong khung.
- **`run_local.ps1` không khởi động được.** Script chỉ tìm `.venv`, mà cả hai `.venv` đều hỏng (lỗi "uv trampoline failed"). Đã sửa để tự chọn bản Python chạy được.

### 9.3. Thử nghiệm với tài khoản thật: biểu 11b, so sánh hai cách nhập

Môi trường:

- Đăng nhập bằng tài khoản cấp Sở Tư pháp tỉnh Bắc Ninh trên `http://hoangtv.dev.com/`.
- Báo cáo biểu **11b/TP/LSTN** "Số tổ chức và kết quả hoạt động của tổ chức hành nghề luật sư" (2 form: 11b và Ghi chú 11b), mở từ màn hình danh sách báo cáo, bấm **Nhập file**.
- Hai file Excel thật của Sở Tư pháp TP. Hồ Chí Minh:
  - **File A**: đúng thứ tự cột của mẫu. Có 819 văn phòng luật sư, 1.595 công ty luật, 1 dòng tổng và 2 dòng nhóm; cuối file có 5 dòng ghi chú.
  - **File B** (tên có hậu tố "(1)"): cùng số liệu nhưng các cột bị xáo trộn. Cột tên tổ chức nằm ở cột K "Ghi chú" thay vì cột B.
- Không bấm **Xác nhận & nhập** ở bước cuối, để không ghi đè số liệu của báo cáo Bắc Ninh. Sau thử nghiệm, báo cáo không đổi và bảng `import_records` không có bản ghi mới.

| File / cách nhập | Số dòng ghép | Lỗi | Thời gian | Nhận xét |
|---|---|---|---|---|
| A – Nhập file Excel (cũ) | 2.418 | 8 lỗi trên 1 dòng | khoảng 2 giây | Dòng ghi chú cuối file bị nạp thành dòng 2.419; 1.310 cảnh báo nghiệp vụ |
| A – Nhập File Excel AI | 2.417 | 0 | khoảng 7 giây đọc + 2 giây ghép | AI cắt đúng phần ghi chú cuối bảng. Đối chiếu từng ô 2.417 × 11 khớp file, trừ 9 ô tổng do biểu tự tính ("-" thay cho 0). 1.310 cảnh báo nghiệp vụ giống cách cũ |
| B – Nhập file Excel (cũ) | 2.419 | 2.434 lỗi trên 2.416 dòng | — | Ghép theo vị trí cột nên mất tên tổ chức, doanh thu rơi vào cột số việc; tổng doanh thu khoảng 14,8 tỷ thay vì 1.112,8 tỷ |
| B – Nhập File Excel AI | — | — | — | Hộp xem trước cảnh báo "Tên dòng đang nằm ở cột K "Ghi chú" thay vì cột B; số liệu trong file không khớp với tiêu đề cột." và "Có 9 ô bị lỗi công thức"; ô "Độ tin cậy" hiện "Cột không khớp tiêu đề"; nút **Tiếp tục** bị khóa, kèm hướng dẫn "Vui lòng sắp xếp lại các cột của file theo đúng file mẫu rồi chọn lại file." |

Kết luận: cách nhập cũ chỉ đúng khi file giữ nguyên bố cục của file mẫu, vì nó ghép theo vị trí cột và lấy hết các dòng tới cuối sheet. Nhập File Excel AI tự tìm vùng bảng, bỏ phần ghi chú, và chặn file có cột lệch thay vì nhập sai. AI **không tự xếp lại cột**: với file B, cán bộ phải sửa file theo mẫu rồi nhập lại.

Lỗi phát hiện và sửa trong đợt thử nghiệm này:

- **Nút "Nhập file" bị ẩn** khi mở báo cáo từ trang tổng hợp, do lấy sai mã đơn vị hiện tại. Đã sửa trong `toolbar.js`.
- **Cột (3) "Tổng số việc" để trống ở cả hai cách nhập.** Cột này dùng công thức theo dòng khai báo ở cấu hình cột, nhưng hộp nhập không áp dụng. Đã bổ sung bước điền công thức; tổng cột (3) sau khi ghép là 22.024, khớp file.
- **Ghép biểu 11b mất khoảng 220 giây** vì gần 2.400 dòng công thức SUM được tính lại từng ô. Đã thêm bộ tính nhanh, còn khoảng 0,8 giây.
- **AI chọn nhầm cột tên dòng** ở một số file có cột STT hoặc cột ghi chú chứa chữ. Đã chuyển sang chọn theo nội dung cột.
- **File đảo cột vẫn hiện "Độ tin cậy 100%"**: độ tin cậy chỉ phản ánh việc tìm vùng bảng. Nay ô này hiện "Cột không khớp tiêu đề" khi có cột lệch.

### 9.4. Thử nghiệm với nhiều kiểu file Excel trên 10 biểu

Mục tiêu: kiểm tra mô hình với những file khác file mẫu theo các kiểu cán bộ hay gặp, chứ không chỉ với file đúng mẫu.

**Bộ file thử.** Lấy file gốc của 10 biểu có nhập Excel (01b, 02a, 04c, 05c, 08b, 09b, 10b, 11c, 15b, 21b). Từ mỗi file gốc sinh 12 biến thể:

| Biến thể | Cách tạo | Điều cần kiểm tra |
|---|---|---|
| Gốc | Giữ nguyên | Kết quả chuẩn để so sánh |
| Bỏ ô gộp | Tách mọi ô gộp ở tiêu đề | Tiêu đề không bị cắt thành nhiều bảng nhỏ |
| Không kẻ khung | Xóa toàn bộ đường kẻ | Tìm bảng chỉ dựa vào nội dung |
| Không có dòng số thứ tự cột | Xóa dòng (1), (2)… | Vẫn xác định được tiêu đề và số liệu |
| Số dạng chữ | Số liệu lưu dưới dạng chuỗi | Không coi số liệu là tiêu đề |
| Dòng trống xen kẽ | Chèn dòng trống giữa các dòng số liệu | Không cắt bảng tại dòng trống |
| Chân trang dài | Thêm nhiều dòng ghi chú, chữ ký | Cắt đúng cuối bảng |
| Dịch vị trí | Bảng bắt đầu ở cột C, dòng 6 | Không phụ thuộc vị trí A1 |
| Thêm cột ghi chú | Thêm cột "Ghi chú nội bộ" bên phải | Không làm lệch các cột của biểu |
| Hai bảng | Thêm một bảng phụ nhỏ bên dưới | Chọn đúng bảng chính |
| Nhiều sheet | Thêm sheet hướng dẫn, danh mục trước sheet số liệu | Chọn đúng sheet số liệu |
| Đảo cột | Đổi chỗ hai cột số liệu liền nhau (cả tiêu đề, số thứ tự cột và số liệu) | Phát hiện và xếp lại cột |

Tổng cộng 119 file. Biểu 09b không có cặp cột liền nhau nào đổi chỗ được mà không phá ô gộp tiêu đề, nên không có biến thể "Đảo cột". Mỗi file được so với đáp án sinh cùng lúc. Một file chỉ tính là đạt khi đúng cả năm điểm:

1. Số dòng số liệu và nội dung từng dòng.
2. Vùng bảng không thừa cột trống ở hai bên.
3. Số dòng tiêu đề.
4. Bảng được chọn sẵn là bảng chính.
5. Với file đảo cột: có thông báo về thứ tự cột.

**Kết quả ở mức dịch vụ AI.**

| Lần chạy | Số file đạt | Ghi chú |
|---|---|---|
| Trước khi sửa | 50/119 | Lỗi chủ yếu: cắt mất tiêu đề, cắt bảng tại dòng trống, nhận nhầm chân trang, không báo đảo cột |
| Sau đợt sửa thứ nhất | 119/119 | Chỉ chấm số dòng và nội dung |
| Chấm chặt hơn (đủ 5 điểm) | Phát hiện thêm lỗi chọn bảng, tiêu đề vụn, thừa cột trống | Đã sửa, xem bên dưới |
| **Lần cuối** | **119/119** | Thời gian đọc trung bình khoảng 0,57 giây, lâu nhất khoảng 1,8 giây mỗi file |

Số dòng tiêu đề khớp file gốc ở mọi biến thể, trừ 4 file của biểu 11c. Ở biểu này, file gốc tính cả dòng "Đơn vị tính" vào tiêu đề; mô hình không tính dòng đó, và số liệu vẫn đúng.

**Kiểm tra hồi quy trên 300 file thật.** Chạy lại 300 file thật của các đơn vị bằng bản trước và bản sau đợt sửa:

- Số bảng tìm được vẫn là 300.
- 20 file có kết quả khác, và cả 20 đều tốt hơn:
  - 14 file biểu 04a/04b/04d lấy lại được dòng tiêu đề trên cùng trước đây bị cắt mất (vùng bảng A3:S8 thành A2:S8).
  - 6 file biểu 11b bỏ được các cột trống thừa bên phải (ví dụ A3:M29 thành A3:K29).
- Không file nào bị báo nhầm sai thứ tự cột.

**Kết quả trên màn hình báo cáo.** Đăng nhập bằng tài khoản Sở Tư pháp tỉnh Bắc Ninh, dùng các biểu nhập được Excel (02a, 10b, 11c, 15b) và làm tới bước xem kết quả ghép. Không bấm **Xác nhận & nhập**. Sau thử nghiệm, báo cáo không đổi và bảng `import_records` không có bản ghi mới.

| File | Nhập file Excel (cũ) | Nhập File Excel AI |
|---|---|---|
| 10b – Gốc | 125 dòng, 0 lỗi | 125 dòng, 0 lỗi, độ tin cậy 99% |
| 10b – Đảo cột | 125 dòng, **125 dòng lỗi**. Hai cột bị đặt nhầm chỗ mà không có cảnh báo | 125 dòng, 0 lỗi. Số liệu được xếp lại theo số thứ tự cột, kèm thông báo "Các cột trong file không theo thứ tự của biểu mẫu…" |
| 10b – Dịch vị trí | 125 dòng, **125 dòng lỗi** (lấy cả các cột trống ở đầu sheet) | 125 dòng, 0 lỗi, vùng bảng C6:W136 |
| 10b – Dòng trống xen kẽ, Chân trang dài, Thêm cột ghi chú | — | 125 dòng, 0 lỗi |
| 15b – Đảo cột | 21 dòng, 0 lỗi, nhưng số liệu của hai cột **bị đổi chỗ** mà không có báo hiệu | 21 dòng, 0 lỗi. Đã xếp lại cột, có thông báo |
| 15b – Nhiều sheet | Mặc định chọn sheet "Huong dan" nên 12/21 dòng lỗi | Mặc định chọn đúng bảng số liệu, 21 dòng, 0 lỗi |
| 15b – Hai bảng, Không có dòng số thứ tự cột | — | Chọn đúng bảng chính, 21 dòng, 0 lỗi |
| 02a, 11c – Gốc, Không kẻ khung, Số dạng chữ | — | Đúng 1 dòng số liệu, 0 lỗi |

Các biểu 01b, 04c, 05c, 08b, 09b là báo cáo tổng hợp có báo cáo con, nên màn hình không hiện nút nhập file. Đây là quy định có sẵn của eForm. Các biểu này chỉ được thử ở mức dịch vụ AI.

**Lỗi phát hiện và sửa trong đợt thử này.**

| Lỗi | Biến thể bộc lộ | Cách sửa |
|---|---|---|
| Cắt bảng tại dòng trống hoặc dòng ghi chú nằm giữa bảng | Dòng trống xen kẽ, Chân trang dài | Chỉ cắt khi phần dưới không còn dòng số liệu cùng cấu trúc cột; nhận diện chân trang chặt hơn |
| Tiêu đề bị tách thành nhiều bảng nhỏ khi bỏ ô gộp | Bỏ ô gộp | Ghép phần chữ nằm ngay trên bảng (không có số, nằm trong phạm vi cột của bảng) vào tiêu đề của bảng có dòng số thứ tự cột |
| Mất dòng tiêu đề trên cùng | Không kẻ khung, Bỏ ô gộp, file thật 04a/b/d | Không cắt dòng đầu đang có ô gộp dọc trong bảng. Cho phép mở rộng lên tối đa 3 dòng toàn chữ phía trên |
| Cụm "trong kỳ báo cáo" ở tiêu đề cột bị coi là thông tin kỳ báo cáo | Không kẻ khung | Chỉ coi "kỳ báo cáo" là thông tin chung khi không đứng sau "trong" |
| Tiêu đề cột "Ghi chú" bị coi là chân trang | Thêm cột ghi chú | Dòng có từ 3 ô trở lên không bị coi là chân trang chỉ vì chứa "Ghi chú" |
| Số dạng chữ bị tính vào tiêu đề | Số dạng chữ | Đếm cả số lưu dạng chuỗi khi tìm dòng số liệu đầu tiên |
| Vùng bảng thừa cột trống ở hai bên, làm mất tên đơn vị khi ghép | Dịch vị trí, file thật 11b | Bỏ cột rìa không có giá trị, không có đường kẻ, không thuộc ô gộp |
| Hộp chọn sheet mặc định chọn sheet hướng dẫn hoặc bảng phụ | Nhiều sheet, Hai bảng | Chọn sẵn bảng có dòng số thứ tự cột khớp với biểu. Nếu không có, chọn bảng có số cột gần với biểu nhất, rồi bảng nhiều dòng số liệu hơn, rồi bảng có độ tin cậy cao hơn |
| File đảo cột bị ghép sai chỗ mà không có cảnh báo | Đảo cột | Khi dòng số thứ tự cột (1), (2)… của file khớp trọn với biểu, hộp nhập xếp lại số liệu theo đúng thứ tự và hiện thông báo các cột đã xếp lại. Cột nhãn (A, B, STT) không đổi chỗ |

## 10. Hạn chế và hướng tiếp theo

- Hộp nhập chỉ tự xếp lại cột khi file có dòng số thứ tự cột (1), (2)… khớp trọn với biểu (mục 9.4). File đảo cột mà không có dòng này, hoặc có cột tên dòng nằm sai chỗ như file B của biểu 11b, vẫn bị khóa để cán bộ sửa file. Hướng tiếp theo: ánh xạ cột theo nội dung tiêu đề, kèm bước cán bộ xác nhận.
- Bộ 119 file ở mục 9.4 được sinh từ file thật nằm trong dữ liệu huấn luyện, nên kết quả 119/119 cho thấy mô hình chịu được các kiểu biến đổi, chứ chưa phải kết quả trên biểu hoàn toàn mới. Cần thêm file thật của các biểu chưa có trong tập huấn luyện để đánh giá tiếp.
- Báo cáo tổng hợp có báo cáo con không có nút nhập file (quy định có sẵn của eForm), nên 5/10 biểu ở mục 9.4 mới chỉ được thử ở mức dịch vụ AI.
- Chưa bấm **Xác nhận & nhập** trên báo cáo thật của Bắc Ninh để tránh ghi đè số liệu. Bước ghi đã được kiểm thử trên báo cáo thử (mục 9.2).
- Dịch vụ AI đang chạy như một tiến trình thường, nên sẽ dừng khi khởi động lại máy. Khi triển khai thật, nên chạy nó dưới dạng Windows Service hoặc tác vụ khởi động.
- Khóa JWT dùng chung là khóa đối xứng. Nếu sau này có nhiều service cùng tin token của eForm, nên chuyển sang khóa bất đối xứng (RS256), để mỗi service chỉ giữ khóa công khai.
- Nhật ký nhập AI (bảng gốc và các ô cán bộ đã sửa) là nguồn dữ liệu tốt để bổ sung tập huấn luyện. Cần quy trình xác minh trước khi dùng làm nhãn (`verified = true`), đúng như yêu cầu dữ liệu trong tài liệu đề xuất.
