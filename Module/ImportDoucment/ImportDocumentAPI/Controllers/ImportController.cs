using System.Threading;
using System.Threading.Tasks;
using System.Web;
using System.Web.Http;
using ImportDocument.Application.Services;
namespace ImportDocument.ImportApi.Controllers
{
    [RoutePrefix("api/import")]
    public class ImportController : ApiController
    {
        private readonly IImportService service;
        public ImportController(IImportService service) { this.service = service; }
        [HttpPost, Route("parse")]
        public async Task<IHttpActionResult> Parse(CancellationToken cancellationToken)
        {
            if (HttpContext.Current.Request.Files.Count == 0) return BadRequest("Vui lòng chọn file Excel.");
            var file = HttpContext.Current.Request.Files[0];
            var userId = HttpContext.Current.Request.Form["userId"];
            var documentId = HttpContext.Current.Request.Form["documentId"];
            var targetSchemaJson = HttpContext.Current.Request.Form["targetSchemaJson"];
            var docTypeCode = HttpContext.Current.Request.Form["docTypeCode"];
            int formIndex;
            if (!int.TryParse(HttpContext.Current.Request.Form["formIndex"], out formIndex) || formIndex < 0) formIndex = 0;
            if (string.IsNullOrWhiteSpace(userId) || string.IsNullOrWhiteSpace(documentId)) return BadRequest("Thiếu userId hoặc documentId.");
            var result = await service.ImportAsync(
                file.InputStream, file.FileName, userId, documentId,
                targetSchemaJson, docTypeCode, formIndex, cancellationToken);
            return Ok(result);
        }
    }
}

