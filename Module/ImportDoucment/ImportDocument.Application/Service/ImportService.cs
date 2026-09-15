using System;
using System.Collections.Generic;
using System.Configuration;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using ImportDocument.Application.Dto;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace ImportDocument.Application.Services
{
    public class ImportService : IImportService
    {
        private static readonly HttpClient Http = CreateHttpClient();

        public async Task<object> GetHealthAsync(CancellationToken cancellationToken)
        {
            var extractUrl = ConfigurationManager.AppSettings["AiUrl"]
                ?? "http://127.0.0.1:8010/api/eform/extract";
            var healthUri = new UriBuilder(extractUrl) { Path = "/health", Query = string.Empty }.Uri;
            using (var linked = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken))
            {
                linked.CancelAfter(TimeSpan.FromSeconds(5));
                try
                {
                    using (var response = await Http.GetAsync(healthUri, linked.Token))
                    {
                        var content = await response.Content.ReadAsStringAsync();
                        if (!response.IsSuccessStatusCode)
                            return new JObject { ["status"] = "unavailable" };
                        return JObject.Parse(content);
                    }
                }
                catch (Exception ex) when (
                    ex is HttpRequestException || ex is TaskCanceledException || ex is JsonException)
                {
                    return new JObject { ["status"] = "unavailable" };
                }
            }
        }

        public async Task<ImportResponseDto> ImportAsync(
            Stream file,
            string fileName,
            string userId,
            string documentId,
            CancellationToken cancellationToken)
        {
            cancellationToken.ThrowIfCancellationRequested();
            if (file == null || (file.CanSeek && file.Length == 0))
                return Failed("File Excel rỗng.", fileName, userId, documentId);

            var safeFileName = Path.GetFileName(fileName ?? string.Empty);
            var extension = Path.GetExtension(safeFileName).ToLowerInvariant();
            if (extension != ".xlsx" && extension != ".xlsm")
                return Failed("Chỉ chấp nhận file .xlsx hoặc .xlsm.", safeFileName, userId, documentId);

            var aiUrl = ConfigurationManager.AppSettings["AiUrl"]
                ?? "http://127.0.0.1:8010/api/eform/extract";
            var timeoutSeconds = ReadPositiveSetting("AiTimeoutSeconds", 180, 5, 600);

            if (file.CanSeek)
                file.Position = 0;

            string responseJson;
            using (var linked = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken))
            using (var multipart = new MultipartFormDataContent())
            using (var fileContent = new StreamContent(file))
            {
                linked.CancelAfter(TimeSpan.FromSeconds(timeoutSeconds));
                fileContent.Headers.ContentType = new MediaTypeHeaderValue(
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet");
                multipart.Add(fileContent, "file", safeFileName);
                multipart.Add(new StringContent(safeFileName, Encoding.UTF8), "originalFileName");

                try
                {
                    using (var response = await Http.PostAsync(aiUrl, multipart, linked.Token))
                    {
                        responseJson = await response.Content.ReadAsStringAsync();
                        if (!response.IsSuccessStatusCode)
                        {
                            return Failed(
                                "AI service từ chối workbook: " + ReadAiError(responseJson),
                                safeFileName,
                                userId,
                                documentId);
                        }
                    }
                }
                catch (TaskCanceledException ex)
                {
                    var message = cancellationToken.IsCancellationRequested
                        ? "Yêu cầu đọc Excel đã bị hủy."
                        : "AI service xử lý quá thời gian cho phép.";
                    return Failed(message + " " + ex.Message, safeFileName, userId, documentId);
                }
                catch (HttpRequestException ex)
                {
                    return Failed(
                        "Không kết nối được AI service: " + ex.Message,
                        safeFileName,
                        userId,
                        documentId);
                }
            }

            JObject aiResult;
            try
            {
                aiResult = JObject.Parse(responseJson);
            }
            catch (JsonException ex)
            {
                return Failed(
                    "AI service trả JSON không hợp lệ: " + ex.Message,
                    safeFileName,
                    userId,
                    documentId);
            }

            return BuildPreviewResponse(aiResult, safeFileName, userId, documentId);
        }

        private static ImportResponseDto BuildPreviewResponse(
            JObject aiResult,
            string fileName,
            string userId,
            string documentId)
        {
            var sheetArray = aiResult["sheets"] as JArray ?? new JArray();
            var sheetNames = sheetArray
                .OfType<JObject>()
                .Select(item => (string)item["sheetName"] ?? string.Empty)
                .Where(item => !string.IsNullOrWhiteSpace(item))
                .ToList();

            var tables = new List<JObject>();
            foreach (var sheet in sheetArray.OfType<JObject>())
            {
                var sheetTables = sheet["tables"] as JArray;
                if (sheetTables != null)
                    tables.AddRange(sheetTables.OfType<JObject>());
            }

            var summary = aiResult["summary"] as JObject ?? new JObject();
            var warnings = aiResult["warnings"] as JArray ?? new JArray();
            var firstTable = tables.FirstOrDefault();
            var success = tables.Count > 0;
            var requiresReview = (bool?)aiResult["requiresReview"] ?? !success;

            return new ImportResponseDto
            {
                Success = success,
                Message = success
                    ? "AI đã tách dữ liệu. Hãy kiểm tra bản xem trước trước khi nhập."
                    : "AI chưa phát hiện được vùng bảng trong workbook.",
                FileName = fileName,
                UserId = userId,
                DocumentId = documentId,
                Sheets = sheetNames,
                Data = firstTable == null ? (object)new JArray() : firstTable["data"] ?? new JArray(),
                RowCount = (int?)summary["valueRowCount"] ?? 0,
                ErrorCount = 0,
                Errors = new JArray(),
                SchemaVersion = (string)aiResult["schemaVersion"],
                ModelVersion = (string)aiResult["model"],
                Valid = success,
                RequiresReview = requiresReview,
                Columns = firstTable == null ? (object)new JArray() : firstTable["columns"] ?? new JArray(),
                RowMappings = new JArray(),
                AiResult = aiResult,
                Warnings = warnings,
                TableCount = tables.Count,
                DurationMs = (double?)aiResult["durationMs"] ?? 0
            };
        }

        private static string ReadAiError(string responseJson)
        {
            if (string.IsNullOrWhiteSpace(responseJson))
                return "Không có nội dung phản hồi.";
            try
            {
                var payload = JObject.Parse(responseJson);
                var detail = payload["detail"];
                if (detail != null)
                    return detail.Type == JTokenType.String
                        ? (string)detail
                        : detail.ToString(Formatting.None);
            }
            catch (JsonException)
            {
            }
            return responseJson.Length > 1000 ? responseJson.Substring(0, 1000) : responseJson;
        }

        private static int ReadPositiveSetting(string key, int fallback, int minimum, int maximum)
        {
            int configured;
            if (!int.TryParse(ConfigurationManager.AppSettings[key], out configured))
                return fallback;
            return Math.Max(minimum, Math.Min(maximum, configured));
        }

        private static HttpClient CreateHttpClient()
        {
            var client = new HttpClient();
            client.Timeout = Timeout.InfiniteTimeSpan;
            return client;
        }

        private static ImportResponseDto Failed(
            string message,
            string fileName,
            string userId,
            string documentId)
        {
            return new ImportResponseDto
            {
                Success = false,
                Message = message,
                FileName = fileName,
                UserId = userId,
                DocumentId = documentId,
                Sheets = new List<string>(),
                Data = new JArray(),
                Errors = new JArray(),
                Warnings = new JArray(),
                Valid = false,
                RequiresReview = true,
                Columns = new JArray(),
                RowMappings = new JArray(),
                TableCount = 0
            };
        }
    }
}
