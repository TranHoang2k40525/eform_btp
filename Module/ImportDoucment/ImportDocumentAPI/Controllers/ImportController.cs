using System.Threading.Tasks;
using System.Web;
using System.Web.Http;
using ImportDocument.Application.Dto;
using ImportDocument.Application.Services;

namespace ImportDocument.ImportApi.Controllers
{
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
            var originalFileName = HttpContext.Current.Request.Form["originalFileName"];
            if (string.IsNullOrWhiteSpace(originalFileName)) originalFileName = file.FileName;
            var userId = HttpContext.Current.Request.Form["userId"];
            var documentId = HttpContext.Current.Request.Form["documentId"];
            var result = await service.ImportAsync(
                file.InputStream, originalFileName, userId, documentId);

            if (result.Success)
            {
                var saved = await service.SaveReportAsync(new SaveReportRequestDto
                {
                    DocumentId = documentId,
                    UserId = userId,
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
    }
}
