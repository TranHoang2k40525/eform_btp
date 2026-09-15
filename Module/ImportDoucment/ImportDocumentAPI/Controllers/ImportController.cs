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

        [HttpGet, Route("health")]
        public async Task<IHttpActionResult> Health(CancellationToken cancellationToken)
        {
            return Ok(await service.GetHealthAsync(cancellationToken));
        }

        [HttpPost, Route("parse")]
        public async Task<IHttpActionResult> Parse(CancellationToken cancellationToken)
        {
            if (HttpContext.Current.Request.Files.Count == 0) return BadRequest("Vui lòng chọn file Excel.");
            var file = HttpContext.Current.Request.Files[0];
            var originalFileName = HttpContext.Current.Request.Form["originalFileName"];
            if (string.IsNullOrWhiteSpace(originalFileName)) originalFileName = file.FileName;
            var userId = HttpContext.Current.Request.Form["userId"];
            var documentId = HttpContext.Current.Request.Form["documentId"];
            var result = await service.ImportAsync(
                file.InputStream, originalFileName, userId, documentId, cancellationToken);
            return Ok(result);
        }
    }
}

