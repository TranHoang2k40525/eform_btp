using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Security.Claims;
using System.Threading;
using System.Threading.Tasks;
using System.Web.Http;
using EForm.ImportDocument.Application;
using EForm.ImportDocument.Domain;

namespace EForm.ImportDocument.ImportApi.Controllers
{
    [RoutePrefix("api/import")]
    public sealed class ImportController : ApiController
    {
        private readonly ImportPipelineService _service;
        public ImportController(ImportPipelineService service) { _service = service ?? throw new ArgumentNullException("service"); }
        [HttpPost, Route("parse")]
        public async Task<HttpResponseMessage> Parse(CancellationToken cancellationToken)
        {
            if (!Request.Content.IsMimeMultipartContent()) return Request.CreateErrorResponse(HttpStatusCode.UnsupportedMediaType, "Content-Type phải là multipart/form-data.");
            long documentId;
            if (!long.TryParse(GetQuery("documentId"), out documentId) || documentId <= 0) return Request.CreateErrorResponse(HttpStatusCode.BadRequest, "Thiếu documentId.");
            var userId = CurrentUserId();
            if (userId <= 0) return Request.CreateErrorResponse(HttpStatusCode.Unauthorized, "Không xác định được người dùng.");
            var provider = new MultipartMemoryStreamProvider();
            await Request.Content.ReadAsMultipartAsync(provider, cancellationToken).ConfigureAwait(false);
            var file = provider.Contents.FirstOrDefault(item => string.Equals(item.Headers.ContentDisposition?.Name?.Trim('\\', '"'), "file", StringComparison.OrdinalIgnoreCase));
            if (file == null) return Request.CreateErrorResponse(HttpStatusCode.BadRequest, "Thiếu multipart field 'file'.");
            var schema = provider.Contents.FirstOrDefault(item => string.Equals(item.Headers.ContentDisposition?.Name?.Trim('\\', '"'), "targetSchemaJson", StringComparison.OrdinalIgnoreCase));
            var schemaJson = schema == null ? null : await schema.ReadAsStringAsync().ConfigureAwait(false);
            try
            {
                using (var stream = await file.ReadAsStreamAsync().ConfigureAwait(false))
                {
                    var result = await _service.ParseAsync(new ImportRequestContext { DocumentId = documentId, UserId = userId, TargetSchemaJson = schemaJson }, stream, file.Headers.ContentDisposition?.FileName?.Trim('\\', '"') ?? "upload.xlsx", cancellationToken).ConfigureAwait(false);
                    return new HttpResponseMessage(HttpStatusCode.OK) { Content = new StringContent(result.Json ?? "{}", System.Text.Encoding.UTF8, "application/json") };
                }
            }
            catch (ImportPermissionException ex) { return Request.CreateErrorResponse(HttpStatusCode.Forbidden, ex.Message); }
            catch (ImportRequestException ex) { return Request.CreateErrorResponse(HttpStatusCode.BadRequest, ex.Message); }
            catch (HttpRequestException ex) { return Request.CreateErrorResponse(HttpStatusCode.BadGateway, ex.Message); }
        }
        private string GetQuery(string key) { var p = Request.GetQueryNameValuePairs().FirstOrDefault(x => string.Equals(x.Key, key, StringComparison.OrdinalIgnoreCase)); return p.Equals(default(KeyValuePair<string, string>)) ? null : p.Value; }
        private long CurrentUserId() { var p = User as ClaimsPrincipal; var c = p?.FindFirst(ClaimTypes.NameIdentifier) ?? p?.FindFirst("sub"); long v; return c != null && long.TryParse(c.Value, out v) ? v : 0; }
    }
}
