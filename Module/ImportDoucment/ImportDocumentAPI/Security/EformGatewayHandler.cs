using System;
using System.Configuration;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace ImportDocument.ImportApi.Security
{
    /// <summary>
    /// Kiểm tra CORS và JWT cho các API /api/import.
    /// </summary>
    public class EformGatewayHandler : DelegatingHandler
    {
        /// <summary>Khoá của <see cref="EformUser"/> trong <c>HttpRequestMessage.Properties</c>.</summary>
        public const string USER_KEY = "EformUser";

        protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            var origin = request.Headers.Contains("Origin") ? request.Headers.GetValues("Origin").FirstOrDefault() : null;
            var allowedOrigin = IsAllowedOrigin(origin) ? origin : null;

            if (request.Method == HttpMethod.Options && origin != null)
            {
                var preflight = new HttpResponseMessage(allowedOrigin != null ? HttpStatusCode.NoContent : HttpStatusCode.Forbidden);
                AddCors(preflight, allowedOrigin);
                if (allowedOrigin != null)
                {
                    preflight.Headers.Add("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
                    preflight.Headers.Add("Access-Control-Allow-Headers", "Authorization, Content-Type");
                    preflight.Headers.Add("Access-Control-Max-Age", "600");
                }
                return preflight;
            }

            if (RequiresAuth(request))
            {
                string error;
                var user = EformJwtValidator.Validate(ReadBearer(request), out error);
                if (user == null)
                {
                    var denied = JsonError(HttpStatusCode.Unauthorized, error);
                    AddCors(denied, allowedOrigin);
                    return denied;
                }
                request.Properties[USER_KEY] = user;
            }

            var response = await base.SendAsync(request, cancellationToken);
            AddCors(response, allowedOrigin);
            return response;
        }

        /// <summary>Người dùng eForm của request (null khi tắt xác thực / không có token).</summary>
        public static EformUser GetUser(HttpRequestMessage request)
        {
            object value;
            return request != null && request.Properties.TryGetValue(USER_KEY, out value) ? value as EformUser : null;
        }

        /// <summary>Có bắt buộc token eForm không (appSettings <c>ImportAuthRequired</c>, mặc định true).</summary>
        public static bool AuthRequired
        {
            get
            {
                bool required;
                return !bool.TryParse(ConfigurationManager.AppSettings["ImportAuthRequired"], out required) || required;
            }
        }

        private static bool RequiresAuth(HttpRequestMessage request)
        {
            var path = (request.RequestUri.AbsolutePath ?? string.Empty).TrimEnd('/').ToLowerInvariant();
            if (path.IndexOf("/api/import/", StringComparison.Ordinal) < 0) return false;
            if (path.EndsWith("/api/import/health", StringComparison.Ordinal)) return false;
            if (AuthRequired) return true;
            // Tắt bắt buộc nhưng client vẫn gửi token: vẫn kiểm để lấy đúng người dùng.
            return request.Headers.Authorization != null;
        }

        private static string ReadBearer(HttpRequestMessage request)
        {
            var auth = request.Headers.Authorization;
            if (auth == null || !string.Equals(auth.Scheme, "Bearer", StringComparison.OrdinalIgnoreCase))
                return null;
            return auth.Parameter;
        }

        private static bool IsAllowedOrigin(string origin)
        {
            if (string.IsNullOrWhiteSpace(origin)) return false;
            var configured = ConfigurationManager.AppSettings["EformAllowedOrigins"] ?? string.Empty;
            var normalized = origin.Trim().TrimEnd('/');
            return configured
                .Split(new[] { ',', ';' }, StringSplitOptions.RemoveEmptyEntries)
                .Select(o => o.Trim().TrimEnd('/'))
                .Any(o => string.Equals(o, normalized, StringComparison.OrdinalIgnoreCase));
        }

        private static void AddCors(HttpResponseMessage response, string allowedOrigin)
        {
            if (response == null) return;
            response.Headers.Vary.Add("Origin");
            if (allowedOrigin == null) return;
            response.Headers.Remove("Access-Control-Allow-Origin");
            response.Headers.Add("Access-Control-Allow-Origin", allowedOrigin);
        }

        private static HttpResponseMessage JsonError(HttpStatusCode status, string message)
        {
            var body = new JObject { ["success"] = false, ["message"] = message };
            return new HttpResponseMessage(status)
            {
                Content = new StringContent(body.ToString(Formatting.None), Encoding.UTF8, "application/json")
            };
        }
    }
}
