using System;
using System.Configuration;
using System.Security.Cryptography;
using System.Text;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace ImportDocument.ImportApi.Security
{
    /// <summary>
    /// Người dùng eForm đã được xác thực qua JWT do eform_nq cấp (POST /webapi/aiimport/token).
    /// </summary>
    public sealed class EformUser
    {
        /// <summary>Mã người dùng eform_nq (claim <c>sub</c>).</summary>
        public string UserId { get; set; }

        /// <summary>Tên đăng nhập eform_nq (claim <c>name</c>).</summary>
        public string UserName { get; set; }

        /// <summary>Thời điểm token hết hạn (UTC).</summary>
        public DateTime ExpiresUtc { get; set; }
    }

    /// <summary>
    /// Kiểm tra JWT HS256 do eform_nq cấp.
    /// </summary>
    public static class EformJwtValidator
    {
        private const int CLOCK_SKEW_SECONDS = 60;

        /// <summary>Bên phát hợp lệ (mặc định <c>eform_nq</c>).</summary>
        public static string Issuer
        {
            get { return Setting("EformJwtIssuer", "eform_nq"); }
        }

        /// <summary>Bên nhận hợp lệ (mặc định <c>eform_import_ai</c>).</summary>
        public static string Audience
        {
            get { return Setting("EformJwtAudience", "eform_import_ai"); }
        }

        /// <summary>
        /// Kiểm token. Trả về người dùng khi hợp lệ, <c>null</c> kèm lý do khi không.
        /// </summary>
        public static EformUser Validate(string token, out string error)
        {
            error = null;
            var secret = ConfigurationManager.AppSettings["EformJwtSecret"];
            if (string.IsNullOrWhiteSpace(secret) || secret.Length < 32)
            {
                error = "Service chưa cấu hình EformJwtSecret (>= 32 ký tự).";
                return null;
            }
            if (string.IsNullOrWhiteSpace(token))
            {
                error = "Thiếu token đăng nhập eForm.";
                return null;
            }

            var parts = token.Split('.');
            if (parts.Length != 3)
            {
                error = "Token không đúng định dạng.";
                return null;
            }

            JObject header, payload;
            byte[] signature;
            try
            {
                header = JObject.Parse(Encoding.UTF8.GetString(FromBase64Url(parts[0])));
                payload = JObject.Parse(Encoding.UTF8.GetString(FromBase64Url(parts[1])));
                signature = FromBase64Url(parts[2]);
            }
            catch (Exception ex) when (ex is FormatException || ex is JsonException || ex is ArgumentException)
            {
                error = "Token không đúng định dạng.";
                return null;
            }

            if (!string.Equals((string)header["alg"], "HS256", StringComparison.Ordinal))
            {
                error = "Thuật toán ký không được chấp nhận.";
                return null;
            }

            byte[] expected;
            using (var hmac = new HMACSHA256(Encoding.UTF8.GetBytes(secret)))
            {
                expected = hmac.ComputeHash(Encoding.ASCII.GetBytes(parts[0] + "." + parts[1]));
            }
            if (!FixedTimeEquals(expected, signature))
            {
                error = "Chữ ký token không hợp lệ.";
                return null;
            }

            if (!string.Equals((string)payload["iss"], Issuer, StringComparison.Ordinal) ||
                !string.Equals((string)payload["aud"], Audience, StringComparison.Ordinal))
            {
                error = "Token không dành cho service này.";
                return null;
            }

            var now = UnixNow();
            long exp, nbf;
            if (!TryReadLong(payload["exp"], out exp) || now > exp + CLOCK_SKEW_SECONDS)
            {
                error = "Token đã hết hạn. Hãy mở lại hộp Nhập Excel AI.";
                return null;
            }
            if (TryReadLong(payload["nbf"], out nbf) && now + CLOCK_SKEW_SECONDS < nbf)
            {
                error = "Token chưa có hiệu lực.";
                return null;
            }

            var userId = (string)payload["sub"];
            if (string.IsNullOrWhiteSpace(userId))
            {
                error = "Token thiếu mã người dùng.";
                return null;
            }

            return new EformUser
            {
                UserId = userId,
                UserName = (string)payload["name"],
                ExpiresUtc = new DateTime(1970, 1, 1, 0, 0, 0, DateTimeKind.Utc).AddSeconds(exp)
            };
        }

        private static string Setting(string key, string fallback)
        {
            var value = ConfigurationManager.AppSettings[key];
            return string.IsNullOrWhiteSpace(value) ? fallback : value.Trim();
        }

        private static long UnixNow()
        {
            return (long)(DateTime.UtcNow - new DateTime(1970, 1, 1, 0, 0, 0, DateTimeKind.Utc)).TotalSeconds;
        }

        private static bool TryReadLong(JToken token, out long value)
        {
            value = 0;
            if (token == null) return false;
            if (token.Type == JTokenType.Integer || token.Type == JTokenType.Float)
            {
                value = token.Value<long>();
                return true;
            }
            return long.TryParse((string)token, out value);
        }

        private static byte[] FromBase64Url(string value)
        {
            var s = value.Replace('-', '+').Replace('_', '/');
            switch (s.Length % 4)
            {
                case 2: s += "=="; break;
                case 3: s += "="; break;
                case 1: throw new FormatException("Base64Url sai độ dài.");
            }
            return Convert.FromBase64String(s);
        }

        private static bool FixedTimeEquals(byte[] a, byte[] b)
        {
            if (a == null || b == null || a.Length != b.Length) return false;
            var diff = 0;
            for (var i = 0; i < a.Length; i++) diff |= a[i] ^ b[i];
            return diff == 0;
        }
    }
}
