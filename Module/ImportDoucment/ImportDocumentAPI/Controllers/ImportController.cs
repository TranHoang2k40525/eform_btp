using System;
using System.Threading.Tasks;
using System.Web;
using System.Web.Http;
using ImportDocument.Application.Dto;
using ImportDocument.Application.Services;
using ImportDocument.ImportApi.Security;

namespace ImportDocument.ImportApi.Controllers
{
    /// <summary>
    /// API nhập Excel AI: health, parse, save.
    /// </summary>
    [RoutePrefix("api/import")]
    public class ImportController : ApiController
    {
        private readonly IImportService service;
        public ImportController(IImportService service) { this.service = service; }

        [HttpGet, Route("health")]
        public async Task<IHttpActionResult> Health()
        {
            var result = await service.GetHealthAsync();
            return Ok(result);
        }

        [HttpPost, Route("parse")]
        public async Task<IHttpActionResult> Parse()
        {
            if (HttpContext.Current.Request.Files.Count == 0) return BadRequest("Vui lòng chọn file Excel.");
            var file = HttpContext.Current.Request.Files[0];
            var form = HttpContext.Current.Request.Form;
            var originalFileName = form["originalFileName"];
            if (string.IsNullOrWhiteSpace(originalFileName)) originalFileName = file.FileName;

            var eformUser = EformGatewayHandler.GetUser(Request);
            // Có token eForm thì danh tính lấy từ token; chỉ khi tắt xác thực (demo) mới đọc form.
            var userId = eformUser != null ? eformUser.UserId : form["userId"];
            var documentId = form["documentId"];
            var autoSave = !string.Equals(form["autoSave"], "false", StringComparison.OrdinalIgnoreCase);

            var result = await service.ImportAsync(
                file.InputStream, originalFileName, userId, documentId);

            if (result.Success && autoSave)
            {
                var saved = await service.SaveReportAsync(new SaveReportRequestDto
                {
                    DocumentId = documentId,
                    UserId = userId,
                    UserName = eformUser == null ? null : eformUser.UserName,
                    FileName = result.FileName,
                    SheetName = result.Sheets == null || result.Sheets.Count == 0 ? null : result.Sheets[0],
                    TableData = result.Data,
                    AiModelVersion = result.ModelVersion,
                    RawJson = result.AiResult == null ? null : result.AiResult.ToString()
                });
                result.Saved = saved.Success;
                result.SavedRecordId = saved.RecordId;
                result.SaveMessage = saved.Message;
                if (!saved.Success)
                {
                    result.Success = false;
                    result.Message = "AI đã bóc tách nhưng chưa lưu được kết quả: " + saved.Message;
                }
            }

            return Ok(result);
        }

        /// <summary>
        /// Lưu bản dữ liệu người dùng ĐÃ xem trước và xác nhận nhập vào báo cáo eForm.
        /// Body: <c>{ documentId, fileName, sheetName, sourceRange, aiModelVersion, tableData, corrections, source }</c>.
        /// </summary>
        [HttpPost, Route("save")]
        public async Task<IHttpActionResult> Save([FromBody] SaveReportRequestDto request)
        {
            if (request == null)
                return Ok(new SaveReportResponseDto { Success = false, Message = "Dữ liệu yêu cầu rỗng." });
            if (string.IsNullOrWhiteSpace(request.DocumentId) || request.TableData == null)
                return Ok(new SaveReportResponseDto { Success = false, Message = "Thiếu mã báo cáo hoặc dữ liệu nhập." });

            var eformUser = EformGatewayHandler.GetUser(Request);
            if (eformUser == null && EformGatewayHandler.AuthRequired)
                return Unauthorized();

            // Danh tính luôn theo token, bỏ mọi giá trị client tự gửi.
            request.UserId = eformUser != null ? eformUser.UserId : request.UserId;
            request.UserName = eformUser != null ? eformUser.UserName : request.UserName;
            request.RawJson = null;

            var saved = await service.SaveReportAsync(request);
            return Ok(saved);
        }
    }
}
