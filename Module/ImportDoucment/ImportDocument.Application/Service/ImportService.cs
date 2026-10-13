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
using ImportDocument.Domain.Entities;
using ImportDocument.Domain.Interfaces;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace ImportDocument.Application.Services
{
    public class ImportService : IImportService
    {
        private static readonly HttpClient Http = CreateHttpClient();
        private readonly IImportRepository repository;
        public ImportService()
        {
        }

        public ImportService(IImportRepository repository)
        {
            this.repository = repository;
        }

        public async Task<object> GetHealthAsync()
        {
            var extractUrl = ConfigurationManager.AppSettings["AiUrl"]
                ?? "http://127.0.0.1:8010/api/eform/extract";
            var healthUri = new UriBuilder(extractUrl) { Path = "/health", Query = string.Empty }.Uri;
            try
            {
                using (var response = await Http.GetAsync(healthUri))
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

        public async Task<ImportResponseDto> ImportAsync(
            Stream file,
            string fileName,
            string userId,
            string documentId)
        {
            if (file == null || (file.CanSeek && file.Length == 0))
                return Failed("File Excel rỗng (0 bytes). Vui lòng chọn file có dữ liệu.", fileName, userId, documentId);

            if (file.CanSeek && file.Length > 52428800)
                return Failed("File Excel vượt giới hạn dung lượng 50 MB.", fileName, userId, documentId);

            var safeFileName = Path.GetFileName(fileName ?? string.Empty);
            var extension = Path.GetExtension(safeFileName).ToLowerInvariant();
            if (extension != ".xlsx" && extension != ".xlsm")
                return Failed("Chỉ chấp nhận file .xlsx hoặc .xlsm.", safeFileName, userId, documentId);

            if (file.CanSeek && file.Length >= 4)
            {
                byte[] header = new byte[4];
                file.Position = 0;
                int read = file.Read(header, 0, 4);
                file.Position = 0;
                if (read == 4 && (header[0] != 0x50 || header[1] != 0x4B))
                {
                    return Failed("Tệp tin không phải định dạng Excel OpenXML hợp lệ hoặc đã bị lỗi.", safeFileName, userId, documentId);
                }
            }

            var aiUrl = ConfigurationManager.AppSettings["AiUrl"]
                ?? "http://127.0.0.1:8010/api/eform/extract";

            if (file.CanSeek)
                file.Position = 0;

            string responseJson;
            using (var multipart = new MultipartFormDataContent())
            using (var fileContent = new StreamContent(file))
            {
                fileContent.Headers.ContentType = new MediaTypeHeaderValue(
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet");
                multipart.Add(fileContent, "file", safeFileName);
                multipart.Add(new StringContent(safeFileName, Encoding.UTF8), "originalFileName");

                try
                {
                    using (var response = await Http.PostAsync(aiUrl, multipart))
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
                    return Failed("AI service xử lý quá thời gian cho phép: " + ex.Message, safeFileName, userId, documentId);
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
            var schemaVersion = (string)aiResult["schemaVersion"];
            if (!string.Equals(schemaVersion, "2.0", StringComparison.Ordinal))
            {
                return Failed(
                    "AI trả về schema không được hỗ trợ: " + (schemaVersion ?? "(trống)") + ".",
                    fileName,
                    userId,
                    documentId);
            }

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
            var success = tables.Count > 0 &&
                tables.All(table => table["data"] is JArray);
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
                SchemaVersion = schemaVersion,
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

        public async Task<SaveReportResponseDto> SaveReportAsync(SaveReportRequestDto request)
        {
            if (request == null)
            {
                return new SaveReportResponseDto
                {
                    Success = false,
                    Message = "Dữ liệu yêu cầu rỗng."
                };
            }

            var docId = string.IsNullOrWhiteSpace(request.DocumentId) ? "EFORM_DOC_DEFAULT" : request.DocumentId;
            var userId = string.IsNullOrWhiteSpace(request.UserId) ? "stp_tphn_bc" : request.UserId;
            var fileName = string.IsNullOrWhiteSpace(request.FileName) ? "Workbook.xlsx" : request.FileName;

            var jsonPayload = request.RawJson;
            if (string.IsNullOrWhiteSpace(jsonPayload))
            {
                jsonPayload = JsonConvert.SerializeObject(new
                {
                    sheetName = request.SheetName,
                    sourceRange = request.SourceRange,
                    tableData = request.TableData,
                    corrections = request.Corrections,
                    aiModelVersion = request.AiModelVersion,
                    savedAt = DateTime.Now
                });
            }

            var record = new ImportRecord
            {
                DocumentId = docId,
                UserId = userId,
                FileName = fileName,
                JsonData = jsonPayload,
                CreatedAt = DateTime.Now
            };

            try
            {
                if (repository == null)
                {
                    return new SaveReportResponseDto
                    {
                        Success = false,
                        Message = "Chưa cấu hình repository lưu dữ liệu import."
                    };
                }

                await repository.SaveAsync(record);
            }
            catch (Exception ex)
            {
                System.Diagnostics.Trace.TraceWarning("Database save warning: " + ex.Message);
                return new SaveReportResponseDto
                {
                    Success = false,
                    Message = "Không thể lưu dữ liệu import vào cơ sở dữ liệu: " + ex.Message
                };
            }

            return new SaveReportResponseDto
            {
                Success = true,
                RecordId = record.Id,
                Message = "Đã lưu thành công dữ liệu báo cáo vào hệ thống eForm.",
                CreatedAt = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss")
            };
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
