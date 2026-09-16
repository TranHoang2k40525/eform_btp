# BÁO CÁO KIỂM THỬ TÍCH HỢP AI – BACKEND C#

## 1. Kết luận kiểm thử

Lần kiểm thử ghi nhận ngày 16/09/2026 xác nhận lớp nghiệp vụ C# gọi được FastAPI đang nạp mô hình, tiếp nhận hai workbook Raw và giữ đúng giá trị ô trong vùng kết quả. Lớp lưu trữ ghi/đọc lại JSON thành công trong một cơ sở dữ liệu LocalDB tạm.

Kết quả tổng hợp: **14 PASS, 1 FAIL, 0 BLOCKED**; ngoài ra có **3 khoảng thiếu (GAP)** được xác định bằng kiểm tra mã nguồn. Không dùng tỷ lệ PASS để suy ra độ chính xác AI hoặc độ chính xác ánh xạ nghiệp vụ.

Mục tiêu tự động lưu số liệu vào biểu **chưa đủ điều kiện nghiệm thu**. Lỗi lược đồ phía C# và việc chưa nối luồng ánh xạ/lưu được giữ nguyên trong báo cáo.

## 2. Môi trường và mức kiểm thử

| Thành phần | Môi trường thực tế |
|---|---|
| Backend | Mã C# của dự án, đích .NET Framework 4.8 |
| Runtime lần chạy | CLR `4.0.30319.42000` |
| Bộ biên dịch | Roslyn có sẵn trong gói phụ thuộc của dự án, cấu hình C# 7.3 |
| Đọc JSON | Newtonsoft.Json 12.0.2 |
| Lưu trữ | Entity Framework 6.4.4, SQL Server LocalDB kiểm thử |
| FastAPI thật | `127.0.0.1:8016`, mô hình `eform_excel_table_extractor_v1`, CPU |
| Giả lập lỗi | HTTP server cục bộ `127.0.0.1:8017`, chỉ dùng để bơm lỗi |
| Nguồn dữ liệu | Hai tệp `.xlsx` thật trong Raw |
| Giao diện / CSDL dự án | Không khởi chạy giao diện; không ghi vào CSDL dự án |

Đã biên dịch trực tiếp các lớp nghiệp vụ, DTO, domain, context, cấu hình thực thể và repository từ chính mã nguồn đang có để chạy trong chương trình kiểm thử tạm. Không sửa các lớp này. Đây không phải kết quả build toàn bộ solution hay kiểm thử tuyến controller qua IIS.

Các trường hợp lỗi JSON/HTTP/timeout/mất kết nối là **fault injection (giả lập lỗi có kiểm soát)**, không phải phản hồi sai do mô hình thật tạo ra. Phép thử LocalDB là phép thử riêng của repository (lớp lưu trữ), với bản ghi do chương trình kiểm thử dựng từ JSON thật; luồng nhận JSON của ứng dụng hiện chưa tự tạo/gọi lưu bản ghi này.

## 3. Dữ liệu đầu vào và kết quả qua C#

| Thuộc tính | Mẫu 1: Giáo dục, biểu 21a | Mẫu 2: Thanh Hóa, biểu 04c |
|---|---:|---:|
| Sheet | `21a` | `04c` |
| Vùng được trả về | `A2:M8` | `A2:X195` |
| Hàng × cột | 7 × 13 | 194 × 24 |
| Header / value rows | 6 / 1 | 6 / 188 |
| Số vùng ô gộp | 17 | 27 |
| Số mô tả hàng phân cấp | 1 | 188 |
| Số đường dẫn cột | 13 | 24 |
| `requiresReview` | true | true |
| Số cảnh báo | 1 | 1 |
| `RowMappings` nghiệp vụ | 0 | 0 |
| Ô đối chiếu với Excel | 91 | 4.656 |
| Ô sai khác trong vùng trả về | 0 | 0 |

Tên tệp thật:

- `Sở Giáo dục và đào tạo_21a_TP_HTPLDN_Kết quả triển khai công tác hỗ trợ phá(...).xlsx`
- `Sở Tư pháp Tỉnh Thanh Hóa_04c_TP_PBGDPL_Kết quả công tác phổ biến giáo dục(...).xlsx`

Vùng/số hàng là đầu ra thực tế của lần chạy, không được sửa cho giống một hình mong đợi. Phép đối chiếu 4.747 ô chỉ kiểm tra giá trị **bên trong vùng mô hình đã trả**; chưa có nhãn chuẩn để kết luận biên bảng hay phân loại header/value của hai mẫu này đều đúng tuyệt đối.

SHA-256 nguồn và phản hồi được lưu trong JSON kiểm thử. Đối chiếu ô được thực hiện độc lập bằng openpyxl: mở workbook nguồn, xử lý giá trị ô gộp và công thức/cache theo hợp đồng, rồi so sánh với ma trận trong phản hồi C#.

## 4. Các ca đã chạy

| Mã | Kiểm tra | Kết quả | Ghi nhận thực tế |
|---|---|---|---|
| TC01 | C# đọc health từ FastAPI thật | PASS | `status=ready`, đúng tên mô hình |
| TC02 | Stream rỗng | PASS | `Success=false`, thông báo file rỗng |
| TC03 | Tệp `.txt` | PASS | Bị từ chối trước khi gửi tới AI |
| TC04 | Workbook 21a qua lớp nghiệp vụ C# | PASS | `Success=true`, schema 2.0, 1 bảng |
| TC05 | Workbook 04c qua lớp nghiệp vụ C# | PASS | `Success=true`, schema 2.0, 1 bảng |
| TC06 | Giữ cờ và cảnh báo của AI | PASS | `requiresReview=true`, giữ 1 cảnh báo |
| TC07 | HTTP 200 nhưng JSON lỗi cú pháp | PASS | C# trả trạng thái thất bại và lỗi JSON |
| TC08 | AI trả HTTP 415 | PASS | C# trả thất bại, giữ nội dung `detail` |
| TC09 | JSON phiên bản 999, `data` là chuỗi | **FAIL** | C# vẫn trả `Success=true`, `Data` là `JValue` |
| TC10 | AI trả quá timeout 5 giây | PASS | C# trả thất bại và thông báo quá thời gian |
| TC11 | AI không kết nối được | PASS | C# trả thất bại và lỗi kết nối |
| TC12 | Repository ghi/đọc lại JSON ở LocalDB | PASS | 1 bản ghi, chuỗi JSON đọc lại trùng nguyên bản |
| TC13 | Repository nhận bản ghi thiếu DocumentId | PASS | Entity Framework từ chối bằng lỗi validation |
| VC01 | Đối chiếu ô của mẫu 21a | PASS | 91 ô, 0 sai khác |
| VC02 | Đối chiếu ô của mẫu 04c | PASS | 4.656 ô, 0 sai khác |

TC07–TC11 dùng HTTP server/cổng lỗi được kiểm soát. TC12–TC13 không chứng minh ứng dụng đã có luồng lưu tự động vào biểu đích; chúng kiểm tra riêng repository hiện có.

## 5. Lỗi TC09: JSON đọc được nhưng chưa đúng hợp đồng

Đầu vào giả lập để kiểm thử cơ chế phòng lỗi phía nhận:

```json
{
  "schemaVersion": "999",
  "sheets": [
    {
      "sheetName": "FaultSheet",
      "tables": [{ "data": "wrong-type" }]
    }
  ]
}
```

Kỳ vọng: backend từ chối phản hồi vì phiên bản không hỗ trợ, thiếu trường và `data` không phải ma trận.

Kết quả chạy thật: `success=True; schema=999; Data type=JValue`.

Nguyên nhân trong mã nguồn: `JObject.Parse` chỉ kiểm tra cú pháp; luồng xây dựng kết quả chỉ xét có đối tượng bảng. Backend chưa xác thực đầy đủ phiên bản, trường bắt buộc và kiểu dữ liệu trước khi đặt `Success`/`Valid`.

Khuyến nghị: bổ sung hợp đồng nhận kiểu rõ ràng/validator ở C#, chỉ đánh dấu hợp lệ sau khi qua kiểm tra cấu trúc và nghiệp vụ. Sau sửa phải chạy lại TC09 cùng các ca JSON thiếu trường, ma trận lệch kích thước và chỉ số cha–con không hợp lệ. Báo cáo này không tuyên bố lỗi đã được sửa.

## 6. Phép thử lưu và đọc lại

Repository thật nhận một `ImportRecord` do chương trình kiểm thử tạo từ JSON thật của mẫu 04c. Trong cơ sở dữ liệu tạm, EF tạo bảng theo cấu hình hiện có, lưu một bản ghi, rồi một context mới đọc lại bản ghi đó.

| Thuộc tính | Ghi nhận |
|---|---|
| Bảng thực thể | `import_records` |
| Nội dung lưu | JSON nguồn và thông tin bản nhập |
| Số bản ghi đọc lại | 1 |
| JSON đọc lại bằng nguyên bản | true |
| SHA-256 JSON trước/sau | `295E90DB92C769CE7C43093733D26E41D2EB2ABC6399A722841D1099F47846DC` |
| Thiếu DocumentId | Bị EF validation từ chối |
| Dọn cơ sở dữ liệu tạm | `testDatabaseRemoved=true` |

Cơ sở dữ liệu có tên riêng bắt đầu bằng `eform_week6_evidence_`, được tạo trong khu vực kiểm thử và xoá sau chạy. Không đọc/sửa dữ liệu nghiệp vụ, không dùng kết nối MySQL của dự án.

Lưu JSON vào một bản ghi không tương đương đổ số liệu vào từng chỉ tiêu. Chưa đo được số giá trị nghiệp vụ đã lưu, vì chưa có luồng ánh xạ/lưu nối liền trong ứng dụng.

## 7. Khoảng thiếu qua kiểm tra mã nguồn

| Mã | Khoảng thiếu | Bằng chứng | Điều kiện hoàn thiện |
|---|---|---|---|
| AC01 | Chưa ánh xạ vào chỉ tiêu/cột đích | `RowMappings` được tạo là mảng rỗng | Có định danh đích và kiểm tra cha–con |
| AC02 | Chưa nối luồng nhận JSON với lớp lưu | Lớp nghiệp vụ không có dependency repository/call `SaveAsync` | Có luồng lưu số liệu được chạy và đọc lại |
| AC03 | Chưa đủ kiểm soát nghiệp vụ cho commit | Chưa thấy xử lý nhập lặp, quyền với biểu và giao dịch toàn bản nhập | Có test quyền, nhập lặp, rollback và đọc lại |

AC01–AC03 là các phát hiện khảo sát, **không phải ca đã chạy rồi PASS/FAIL**. Việc EF có giao dịch cho một lần `SaveChangesAsync` không đủ để suy ra đã có toàn bộ kiểm soát nhập số liệu nghiệp vụ.

## 8. Các kiểm thử còn phải bổ sung để nghiệm thu

Nhóm dưới đây là **ca đề xuất, chưa chạy**:

- Controller C# qua IIS nhận multipart và gọi FastAPI thành công.
- Lưu trên MySQL thử nghiệm đúng cấu trúc cơ sở dữ liệu nghiệp vụ.
- Đối chiếu mã “1” lặp dưới I/II và header nhiều cấp, không làm mất ngữ cảnh cha–con.
- Sai biểu/kỳ/đơn vị hoặc sai quyền: không tạo giá trị nghiệp vụ.
- `requiresReview=true`/ánh xạ thiếu: không commit tự động phần chưa xác nhận.
- Ô trống, 0, `-`, chuỗi và công thức/cache được xử lý theo quy tắc đã xác nhận.
- Nhiều sheet/bảng đều được xử lý, không chỉ bảng đầu tiên.
- Lỗi giữa chừng: rollback toàn bản nhập; nhập lại không nhân đôi số liệu.
- Đọc lại từng giá trị đã lưu và so sánh định danh hàng/cột đích cùng giá trị nguồn.

## 9. Cách đối chiếu minh chứng

1. Mở [JSON kiểm thử](evidence/backend_checks_actual.json), xem `cases`, `summary`, `sourceFiles` và `testDatabaseRemoved`.
2. Mở [phản hồi C# thật](evidence/backend_response_actual.json). Mỗi phần tử `captures` chứa tên nguồn và `response`; dữ liệu AI đầy đủ nằm trong `response.AiResult`.
3. Đọc [nhật ký C# gốc](evidence/backend_checks_actual.txt). Nhật ký ghi 12 PASS/1 FAIL của chương trình C#; hai ca VC01/VC02 được bổ sung bởi phép đối chiếu độc lập và nằm trong JSON, nên tổng cuối cùng là 14 PASS/1 FAIL.
4. Đối chiếu mã băm tệp Raw và từng ô `data` với `sourceRange` tương ứng. Không đối chiếu thời gian xử lý như một hằng số.
5. So sánh ảnh mã nguồn với các lớp hiện có; `sourceFiles` ghi SHA-256 tại thời điểm chụp để nhận ra nếu mã đã thay đổi sau đó.

Khi tái lập kiểm thử cần dùng môi trường .NET Framework 4.8, phụ thuộc đúng phiên bản, FastAPI/mô hình hiện có và một cơ sở dữ liệu thử nghiệm riêng. Chương trình chạy kiểm thử là công cụ tạm, không được thêm vào backend. Không gửi các yêu cầu kiểm thử lưu tới cơ sở dữ liệu thật.

## 10. Kết luận nghiệm thu

Đạt ở mức kiểm thử thành phần: kết nối C#–FastAPI, xử lý nhóm lỗi vận chuyển/cú pháp, bảo toàn giá trị trong vùng trả về và repository lưu/đọc JSON. Chưa đạt mục tiêu toàn tuyến: xác thực JSON đầy đủ, ánh xạ nghiệp vụ và tự động lưu đúng số liệu vào biểu đích trên MySQL. Phạm vi không mở rộng sang giao diện.
