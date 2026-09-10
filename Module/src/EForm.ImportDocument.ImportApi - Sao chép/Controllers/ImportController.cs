using System.Threading;
using System.Threading.Tasks;
using System.Web;
using System.Web.Http;
using EForm.ImportDocument.Application.Services;
namespace EForm.ImportDocument.ImportApi.Controllers
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
            if (string.IsNullOrWhiteSpace(userId) || string.IsNullOrWhiteSpace(documentId)) return BadRequest("Thiếu userId hoặc documentId.");
            var result = await service.ImportAsync(file.InputStream, file.FileName, userId, documentId, cancellationToken);
            return Ok(result);
        }
    }
}
