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
            if (HttpContext.Current.Request.Files.Count == 0) return BadRequest("Vui lÃ²ng chá»n file Excel.");
            var file = HttpContext.Current.Request.Files[0];
            var userId = HttpContext.Current.Request.Form["userId"];
            var documentId = HttpContext.Current.Request.Form["documentId"];
            if (string.IsNullOrWhiteSpace(userId) || string.IsNullOrWhiteSpace(documentId)) return BadRequest("Thiáº¿u userId hoáº·c documentId.");
            var result = await service.ImportAsync(file.InputStream, file.FileName, userId, documentId, cancellationToken);
            return Ok(result);
        }
    }
}

