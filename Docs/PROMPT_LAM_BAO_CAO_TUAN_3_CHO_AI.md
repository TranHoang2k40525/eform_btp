# PROMPT GIAO VIỆC CHO AI – HOÀN THIỆN BÁO CÁO THỰC TẬP TUẦN 3

## Vai trò

Bạn là người phụ trách viết báo cáo thực tập kỹ thuật. Hãy viết một báo cáo tuần 3 hoàn chỉnh, có tính kiểm chứng, trình bày chuyên nghiệp bằng tiếng Việt. Không viết chung chung, không tự bịa chức năng chưa có trong mã nguồn hoặc ảnh minh chứng.

## Mục tiêu báo cáo

Báo cáo phải chứng minh hai nội dung chính:

1. **Lập trình Backend (.NET MVC):** Xây dựng API đọc/tiếp nhận file Excel thô, xử lý bóc tách dữ liệu bảng biểu và trả về cấu trúc JSON phẳng.
2. **Quản lý mã nguồn bằng Git:** Thực hiện commit, push và Pull Request/Merge Request có tổ chức.

Kết luận bắt buộc phải đánh giá được mục tiêu: **“Bóc tách thành công dữ liệu bảng biểu phức tạp thành JSON.”**

## Nguồn thông tin phải sử dụng

Đọc và đối chiếu các nguồn sau trước khi viết:

- Mã nguồn backend hiện tại: `C:\Users\hoang\Downloads\eform_btp\Module\ImportDoucment`.
- Tiến độ dự án: `C:\Users\hoang\Downloads\eform_btp\Docs\Bao_cao_tien_do_AI_Import_Excel.md`.
- Báo cáo tuần 2 dùng làm mẫu bố cục: `C:\Users\hoang\Downloads\BÁO CÁO THỰC TẬP TUẦN 2.docx`.
- Ảnh Swagger request/response: `C:\Users\hoang\Downloads\swagger.png`.
- Ảnh GitLab hệ thống eForm gốc: `C:\Users\hoang\Downloads\gitlab_duan_chinh.png` và `C:\Users\hoang\Downloads\gitlab_duan_eform_chính.png`.
- Ảnh GitHub dự án AI đang làm: `C:\Users\hoang\Downloads\Github_ai.png`.

Nếu không đọc được một nguồn, phải ghi rõ “chưa xác minh được”, không được suy đoán.

## Các nội dung kỹ thuật phải mô tả

### 1. Kiến trúc dự án

Mô tả đúng các project hiện có:

- `ImportDocument.Domain`: entity và interface repository.
- `ImportDocument.Application`: DTO, interface service và service nghiệp vụ.
- `ImportDocument.Infrastructure`: Entity Framework `DbContext`, cấu hình entity, repository, MySQL.
- `ImportDocumentAPI`: ASP.NET MVC/Web API 2, controller, Ninject DI, Swagger, Web.config và giao diện kiểm thử.

Phải giải thích quan hệ phụ thuộc theo Clear Architecture:

```text
API → Application → Infrastructure
             ↓
          Domain
```

### 2. API import

Nêu chính xác endpoint:

```http
POST /api/import/parse
Content-Type: multipart/form-data
```

Tham số:

| Tên | Kiểu | Bắt buộc | Ý nghĩa |
|---|---|---|---|
| file | File | Có | File Excel `.xlsx` hoặc `.xls` |
| userId | String | Có | Mã người dùng truyền từ FE |
| documentId | String | Có | Mã document truyền từ FE |

Mô tả tuần tự: Controller nhận request → kiểm tra file và tham số → Service gọi AI/mock AI → chuẩn hóa dữ liệu → Repository lưu MySQL → trả DTO về FE.

### 3. Kết quả API

Phải đưa ví dụ JSON thực tế tương tự ảnh Swagger:

```json
{
  "Success": true,
  "Message": "Bóc tách và lưu dữ liệu thành công.",
  "FileName": "...xlsx",
  "Sheets": ["MockAI"],
  "Data": [{"stt_a":"","chitiet_b":"Tổng số trên địa bàn tỉnh/thành phố","ketquahoatdong":682}],
  "RowCount": 107,
  "ErrorCount": 0,
  "UserId": "121",
  "DocumentId": "121212"
}
```

Giải thích rõ rằng `Data` là mảng object JSON phẳng: mỗi object đại diện một dòng, key đại diện mã cột/field, không còn cấu trúc cell lồng khó xử lý ở FE.

### 4. Validate và lỗi

Nêu các trường hợp đã kiểm thử:

- Không gửi file → HTTP 400, thông báo “Vui lòng chọn file Excel.”
- Thiếu `userId` hoặc `documentId` → HTTP 400.
- Thành công → HTTP 200, `Success = true`.
- Lỗi AI hoặc lỗi lưu DB → trả thông báo lỗi và không coi là import thành công.

Phân biệt rõ phần xác thực người dùng thật đang tạm ẩn/comment do chưa kết nối database eForm gốc; không viết rằng đã hoàn thiện xác thực nếu chưa có bằng chứng.

### 5. MySQL và Entity Framework

Mô tả entity `ImportRecord` gồm:

```text
Id, DocumentId, UserId, FileName, JsonData, CreatedAt
```

Nêu bảng `import_records`, database `importai`, việc dùng `SaveChangesAsync`, và vai trò của repository. Không đưa mật khẩu database vào báo cáo công khai.

### 6. Swagger

Mô tả Swagger chuẩn Swashbuckle, URL `/swagger`, giao diện có Choose File, userId, documentId, content type multipart/form-data. Ảnh Swagger phải được chú thích là minh chứng request thực tế và response HTTP 200.

### 7. Git/GitLab/GitHub

Phân biệt:

- GitLab là repository hệ thống eForm gốc, dùng để tham khảo mã nguồn và quy trình hiện hữu.
- GitHub là repository dự án `eform_btp` đang phát triển module AI.

Giải thích quy trình chuẩn:

```text
Tạo branch → sửa code → build/kiểm tra → commit có thông điệp rõ → push → Pull Request/Merge Request → review → merge
```

Đối chiếu nội dung nhìn thấy trong ảnh commit/merge, không khẳng định có review nếu ảnh không chứng minh điều đó.

## Cấu trúc báo cáo bắt buộc

1. Tiêu đề và thông tin tuần thực tập.
2. Mục tiêu tuần.
3. Công việc đã thực hiện.
4. Kiến trúc và luồng xử lý backend.
5. Thiết kế API và request/response.
6. Cách bóc tách JSON phẳng.
7. MySQL, Entity Framework và lưu dữ liệu.
8. Swagger và kết quả kiểm thử.
9. Git/GitHub/GitLab và quy trình commit/PR.
10. Đối chiếu với hệ thống eForm gốc.
11. Kết quả đạt được, hạn chế, kế hoạch tuần sau.
12. Bảng minh chứng ảnh, ghi rõ ảnh chứng minh nội dung nào.
13. Đánh giá mức độ hoàn thành hai mục tiêu tuần.

## Yêu cầu trình bày

- Viết tiếng Việt có dấu, không lỗi mã hóa UTF-8.
- Văn phong báo cáo thực tập kỹ thuật, rõ ràng, có dẫn chứng.
- Dùng bảng cho API, entity, kết quả kiểm thử và đối chiếu.
- Dùng sơ đồ chữ cho luồng xử lý.
- Không phóng đại: phân biệt rõ phần đã chạy thật, phần mock AI và phần chưa triển khai.
- Tạo file Word `.docx`, không chỉ tạo Markdown hoặc đổi đuôi HTML thành `.doc`.
- Giữ bố cục gần với báo cáo tuần 2 nhưng nội dung phải đầy đủ hơn.
- Chèn bốn ảnh minh chứng đúng vị trí, có chú thích dưới mỗi ảnh.
- Tên file đầu ra: `Bao_cao_thuc_tap_tuan_3_Backend_Git.docx`.

## Tiêu chí nghiệm thu

Báo cáo chỉ đạt khi người đọc có thể trả lời “có” cho tất cả câu hỏi:

- API nhận được file Excel qua multipart/form-data chưa?
- API trả dữ liệu JSON phẳng có ví dụ thực tế chưa?
- Có chứng minh HTTP 200 và HTTP 400 chưa?
- Có mô tả lưu MySQL và entity chưa?
- Có Swagger chuẩn và ảnh minh chứng chưa?
- Có phân biệt GitLab hệ thống gốc với GitHub dự án mới chưa?
- Có mô tả commit/PR nhưng không bịa bằng chứng chưa?
- Có đánh giá rõ đã đạt hay chưa đạt mục tiêu tuần 3 chưa?
