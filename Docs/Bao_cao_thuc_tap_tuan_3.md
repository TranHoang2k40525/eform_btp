# BÁO CÁO THỰC TẬP TUẦN 3

## 1. Thông tin chung

**Dự án:** eForm BTP – AI-assisted Excel Import  
**Nội dung tuần:** Xây dựng Backend .NET MVC/Web API, bóc tách Excel thành JSON phẳng và quản lý mã nguồn bằng Git.  
**Thời gian:** Tuần 3

## 2. Mục tiêu tuần

- Xây dựng API backend tiếp nhận file Excel thô từ giao diện.
- Kiểm tra dữ liệu đầu vào và thông tin định danh biểu mẫu.
- Gọi module xử lý AI/mô phỏng AI và nhận dữ liệu JSON.
- Bóc tách bảng biểu phức tạp thành cấu trúc JSON phẳng.
- Lưu kết quả import vào MySQL thông qua Entity Framework.
- Cấu hình Swagger để kiểm thử API.
- Quản lý mã nguồn bằng Git, commit theo chức năng và tạo Pull/Merge Request.

## 3. Công việc đã thực hiện

### 3.1. Kiến trúc backend

Backend được tổ chức theo các lớp:

```text
ImportDocument.Domain
ImportDocument.Application
ImportDocument.Infrastructure
ImportDocumentAPI
```

- **Domain:** chứa entity `ImportRecord` và các interface repository.
- **Application:** chứa DTO, `IImportService` và nghiệp vụ import.
- **Infrastructure:** chứa `ImportDbContext`, cấu hình Entity Framework, repository và kết nối MySQL.
- **ImportDocumentAPI:** ASP.NET MVC/Web API 2, controller, DI bằng Ninject, Swagger và giao diện kiểm thử.

### 3.2. API import Excel

API chính:

```http
POST /api/import/parse
Content-Type: multipart/form-data
```

Các tham số:

| Tên | Kiểu | Bắt buộc | Mô tả |
|---|---|---:|---|
| file | File | Có | File Excel `.xlsx` hoặc `.xls` |
| userId | String | Có | Mã người dùng giả lập/hiện tại |
| documentId | String | Có | Mã document cần import |

Quy trình xử lý:

```text
FE gửi file Excel
        ↓
ImportController kiểm tra multipart/form-data
        ↓
ImportService đọc thông tin file và gọi module AI
        ↓
AI trả dữ liệu bảng dạng JSON
        ↓
Chuẩn hóa dữ liệu thành JSON phẳng
        ↓
ImportRepository lưu ImportRecord vào MySQL
        ↓
Controller trả kết quả JSON cho FE
```

### 3.3. Kiểm tra và validate

Backend đã kiểm tra:

- Không có file: trả HTTP 400 và thông báo `Vui lòng chọn file Excel.`
- Thiếu `userId`: trả HTTP 400.
- Thiếu `documentId`: trả HTTP 400.
- File không đọc được hoặc AI không trả kết quả: trả thông báo lỗi rõ ràng.
- Kết quả thành công gồm tên file, danh sách sheet, dữ liệu phẳng, số dòng và số lỗi.

Phần xác thực quyền người dùng/document được để sẵn trong nghiệp vụ nhưng tạm thời chưa bật vì chưa kết nối hệ thống eForm gốc.

### 3.4. Kết quả JSON

Khi import thành công, API trả về dạng:

```json
{
  "Success": true,
  "Message": "Bóc tách và lưu dữ liệu thành công.",
  "FileName": "Template_10_TH_CC_Tổng hợp số tổ chức và kết quả hoạt động công chứng trên toàn quốc.xlsx",
  "Sheets": ["MockAI"],
  "Data": [
    {
      "stt_a": "",
      "chitiet_b": "Tổng số trên địa bàn tỉnh/thành phố",
      "ketquahoatdong": 682
    }
  ],
  "RowCount": 107,
  "ErrorCount": 0,
  "UserId": "121",
  "DocumentId": "121212"
}
```

Dữ liệu bảng nhiều tầng được chuyển thành mảng các object JSON, mỗi object là một dòng và mỗi thuộc tính là một mã cột/field tương ứng. Cách này giúp FE dễ hiển thị, kiểm tra và gửi tiếp sang hệ thống eForm.

### 3.5. Lưu dữ liệu MySQL

Entity lưu trữ:

```text
ImportRecord
 ├── Id
 ├── DocumentId
 ├── UserId
 ├── FileName
 ├── JsonData
 └── CreatedAt
```

Bảng tương ứng là `import_records` trong database `importai`. Repository sử dụng `SaveChangesAsync` để lưu bất đồng bộ.

### 3.6. Swagger

Swagger chuẩn được cấu hình bằng Swashbuckle tại:

```text
http://hoang.dev.com/swagger
```

Swagger hiển thị endpoint `POST /api/import/parse` với các trường:

- Choose File: chọn file Excel.
- userId.
- documentId.

Ảnh kiểm thử cho thấy request multipart được gửi thành công và API trả HTTP 200 cùng dữ liệu JSON đã bóc tách.

## 4. Kiểm thử thực tế

### 4.1. Trường hợp thành công

- Chọn file Excel mẫu.
- Nhập `userId = 121`.
- Nhập `documentId = 121212`.
- API trả mã 200.
- `Success = true`.
- Dữ liệu bảng được trả về dạng JSON phẳng.
- `ErrorCount = 0`.

Kết quả này được thể hiện trong ảnh Swagger kết quả API: `swagger.png`.

### 4.2. Trường hợp thiếu file

Khi gọi API không có file, backend trả:

```json
{
  "Message": "Vui lòng chọn file Excel."
}
```

Mã HTTP: `400 Bad Request`.

## 5. Quản lý mã nguồn bằng Git

Mã nguồn được quản lý trên GitHub/GitLab.

- Repository GitHub dự án AI: `eform_btp`.
- Repository GitLab hệ thống eForm gốc: `Eform Solution 2.0`.
- Mã nguồn backend AI được đặt trong thư mục `Module/ImportDoucment`.
- Tài liệu và tiến độ được đặt trong thư mục `Docs`.

Quy trình commit đã thực hiện:

```text
Chỉnh sửa chức năng
        ↓
Build và kiểm tra lỗi
        ↓
git add
        ↓
git commit -m "mô tả ngắn gọn theo chức năng"
        ↓
git push
        ↓
Tạo Pull Request/Merge Request
```

Các nhóm commit thể hiện trong ảnh Git gồm cập nhật tài liệu, merge nhánh, sửa lỗi hiển thị, cập nhật chức năng và đồng bộ mã nguồn. Việc tách repository AI với repository eForm gốc giúp giảm ảnh hưởng đến hệ thống hiện hữu.

## 6. Đối chiếu với hệ thống eForm gốc

Hệ thống eForm gốc trên GitLab đã có luồng nhập/xuất Excel và các module nghiệp vụ. Module mới kế thừa mục tiêu đầu ra JSON nhưng bổ sung bước AI:

| Hệ thống cũ | Module AI mới |
|---|---|
| FE tự xử lý nhiều quy tắc Excel | Backend tiếp nhận file và điều phối xử lý |
| Phụ thuộc cấu hình cột thủ công | AI nhận diện/mapping field |
| Dữ liệu xử lý phân tán ở FE | Kết quả chuẩn hóa tại service |
| Khó kiểm thử độc lập | Có API và Swagger riêng |
| Chưa có bản ghi import tập trung | Lưu `ImportRecord` vào MySQL |

Module mới vẫn giữ cấu trúc JSON phẳng để tương thích với cách FE eForm hiển thị bảng và các field dữ liệu.

## 7. Kết quả đạt được

- Hoàn thành API backend nhận file Excel.
- Hoàn thành nghiệp vụ bóc tách bảng biểu phức tạp thành JSON phẳng.
- Kết nối và lưu kết quả vào MySQL.
- Có Swagger chuẩn để chọn file và kiểm thử trực tiếp.
- Có validate đầu vào và thông báo lỗi tiếng Việt rõ ràng.
- Build solution thành công và chạy được trên IIS.
- Quản lý mã nguồn trên GitHub/GitLab theo commit và merge request.

## 8. Tồn tại và kế hoạch tiếp theo

- AI hiện đang dùng dữ liệu mô phỏng để kiểm thử toàn bộ luồng backend.
- Cần thay URL mock bằng cổng AI thật trong `Web.config`.
- Cần bổ sung đọc trực tiếp cấu trúc sheet Excel thay vì chỉ dùng response mô phỏng.
- Cần bật xác thực `userId/documentId` khi kết nối được database eForm gốc.
- Cần bổ sung test tự động cho nhiều loại biểu mẫu và nhiều sheet.

## 9. Minh chứng

- Ảnh Swagger request/response: `C:\Users\hoang\Downloads\swagger.png`.
- Ảnh repository GitLab hệ thống gốc: `gitlab_duan_chinh.png`, `gitlab_duan_eform_chính.png`.
- Ảnh repository GitHub module đang phát triển: `Github_ai.png`.

**Đánh giá tuần 3:** Hoàn thành các mục tiêu backend, API bóc tách JSON và quản lý mã nguồn theo kế hoạch.
