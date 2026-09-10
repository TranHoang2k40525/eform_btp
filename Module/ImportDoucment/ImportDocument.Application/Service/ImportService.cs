using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using System.Configuration;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Text.RegularExpressions;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using ImportDocument.Domain.Entities;
using ImportDocument.Domain.Interfaces;
using ImportDocument.Application.Dto;
namespace ImportDocument.Application.Services
{
	public class ImportService : IImportService
	{
		private static readonly HttpClient Http = new HttpClient();
		private readonly IImportRepository repository;
		public ImportService(IImportRepository repository) { this.repository = repository; }
		public async Task<ImportResponseDto> ImportAsync(
			Stream file,
			string fileName,
			string userId,
			string documentId,
			string targetSchemaJson,
			string docTypeCode,
			int formIndex,
			CancellationToken cancellationToken)
		{
			cancellationToken.ThrowIfCancellationRequested();
			if (file == null || (file.CanSeek && file.Length == 0))
				return Failed("File Excel rỗng.", fileName, userId, documentId);

			bool useMock;
			bool.TryParse(ConfigurationManager.AppSettings["UseMockAi"], out useMock);
			if (useMock)
				return await ImportMockAsync(fileName, userId, documentId, cancellationToken);

			if (string.IsNullOrWhiteSpace(targetSchemaJson))
				return Failed("Thiếu targetSchemaJson (DocumentContents/FormConfig của biểu đích).", fileName, userId, documentId);
			try
			{
				JToken.Parse(targetSchemaJson);
			}
			catch (JsonException ex)
			{
				return Failed("targetSchemaJson không hợp lệ: " + ex.Message, fileName, userId, documentId);
			}

			var extension = Path.GetExtension(fileName ?? string.Empty).ToLowerInvariant();
			if (extension != ".xlsx" && extension != ".xlsm")
				return Failed("AI Import chỉ nhận .xlsx hoặc .xlsm.", fileName, userId, documentId);

			var uploadRoot = ResolveConfiguredPath(
				ConfigurationManager.AppSettings["AiUploadDir"] ?? @"..\..\AI Import\Main\runtime\uploads");
			Directory.CreateDirectory(uploadRoot);
			var uploadPath = Path.Combine(uploadRoot, Guid.NewGuid().ToString("N") + extension);
			try
			{
				using (var output = new FileStream(uploadPath, FileMode.CreateNew, FileAccess.Write, FileShare.None))
				{
					await file.CopyToAsync(output, 81920, cancellationToken);
				}
				return await ImportWithAiAsync(
					uploadPath, fileName, userId, documentId, targetSchemaJson,
					docTypeCode, formIndex, cancellationToken);
			}
			finally
			{
				if (File.Exists(uploadPath)) File.Delete(uploadPath);
			}
		}

		private async Task<ImportResponseDto> ImportWithAiAsync(
			string uploadPath,
			string fileName,
			string userId,
			string documentId,
			string targetSchemaJson,
			string docTypeCode,
			int formIndex,
			CancellationToken cancellationToken)
		{
			var aiUrl = ConfigurationManager.AppSettings["AiUrl"] ?? "http://127.0.0.1:8010/parse";
			var request = new JObject
			{
				["path"] = uploadPath,
				["target_schema_json"] = targetSchemaJson,
				["doc_type_code"] = docTypeCode ?? string.Empty,
				["form_index"] = Math.Max(0, formIndex),
				["include_hidden"] = false,
				["max_rows"] = 50000
			};
			var timeoutSeconds = 60;
			int configuredTimeout;
			if (int.TryParse(ConfigurationManager.AppSettings["AiTimeoutSeconds"], out configuredTimeout))
				timeoutSeconds = Math.Max(5, configuredTimeout);

			string responseJson;
			using (var linked = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken))
			using (var content = new StringContent(request.ToString(Formatting.None), Encoding.UTF8, "application/json"))
			{
				linked.CancelAfter(TimeSpan.FromSeconds(timeoutSeconds));
				HttpResponseMessage response;
				try
				{
					response = await Http.PostAsync(aiUrl, content, linked.Token);
					responseJson = await response.Content.ReadAsStringAsync();
				}
				catch (Exception ex) when (ex is HttpRequestException || ex is TaskCanceledException)
				{
					return Failed("Không gọi được AI service: " + ex.Message, fileName, userId, documentId);
				}
				if (!response.IsSuccessStatusCode)
				{
					var detail = responseJson.Length > 1000 ? responseJson.Substring(0, 1000) : responseJson;
					return Failed("AI service từ chối workbook: " + detail, fileName, userId, documentId);
				}
			}

			JObject aiResult;
			try
			{
				aiResult = JObject.Parse(responseJson);
			}
			catch (JsonException ex)
			{
				return Failed("AI service trả JSON không hợp lệ: " + ex.Message, fileName, userId, documentId);
			}
			var rows = aiResult["rows"] as JArray ?? new JArray();
			var issues = aiResult["issues"] as JArray ?? new JArray();
			var errorCount = issues.Count(item =>
				string.Equals((string)item["severity"], "error", StringComparison.OrdinalIgnoreCase));
			var valid = (bool?)aiResult["valid"] ?? false;
			var requiresReview = (bool?)aiResult["requires_review"] ?? true;

			var record = new ImportRecord
			{
				FileName = Path.GetFileName(fileName),
				UserId = userId,
				DocumentId = documentId,
				JsonData = aiResult.ToString(Formatting.None),
				CreatedAt = DateTime.UtcNow
			};
			await repository.SaveAsync(record, cancellationToken);
			return new ImportResponseDto
			{
				Success = true,
				Message = requiresReview ? "Đã bóc tách; cần duyệt các ánh xạ được cảnh báo." : "Bóc tách và lưu dữ liệu thành công.",
				FileName = fileName,
				UserId = userId,
				DocumentId = documentId,
				Sheets = new List<string> { (string)aiResult["sheet"] ?? string.Empty },
				Data = rows,
				RowCount = (int?)aiResult["row_count"] ?? rows.Count,
				ErrorCount = errorCount,
				Errors = issues,
				SchemaVersion = (string)aiResult["schema_version"],
				ModelVersion = (string)aiResult["model_version"],
				Valid = valid,
				RequiresReview = requiresReview,
				Columns = aiResult["columns"],
				RowMappings = aiResult["row_mappings"],
				AiResult = aiResult
			};
		}

		private async Task<ImportResponseDto> ImportMockAsync(
			string fileName, string userId, string documentId, CancellationToken cancellationToken)
		{
			await Task.Yield();
			var mockPath = ConfigurationManager.AppSettings["MockAiFile"] ?? @"C:\Users\hoang\Downloads\mới 1.txt";
			if (!Path.IsPathRooted(mockPath)) mockPath = Path.Combine(System.AppDomain.CurrentDomain.BaseDirectory, mockPath);
			if (!File.Exists(mockPath) && !Path.IsPathRooted(ConfigurationManager.AppSettings["MockAiFile"]))
			{
				var rootPath = System.AppDomain.CurrentDomain.BaseDirectory.TrimEnd('\\');
				mockPath = Path.Combine(Directory.GetParent(rootPath).FullName, ConfigurationManager.AppSettings["MockAiFile"] ?? "App_Data\\mock-ai-response.txt");
			}
			if (!File.Exists(mockPath)) return Failed("Không tìm thấy dữ liệu AI mô phỏng.", fileName, userId, documentId);
			var source = File.ReadAllText(mockPath, System.Text.Encoding.UTF8);
			var match = Regex.Match(source, "\\\"ValueData\\\"\\s*:\\s*\\\"((?:\\\\.|[^\\\"\\\\])*)\\\"", RegexOptions.Singleline);
			if (!match.Success) return Failed("File mock không có ValueData.", fileName, userId, documentId);
			var json = JsonConvert.DeserializeObject<string>("\"" + match.Groups[1].Value + "\"");
			var data = JToken.Parse(json);
			var rowCount = data is JArray ? ((JArray)data).Count : 1;
			var record = new ImportRecord { FileName = fileName, UserId = userId, DocumentId = documentId, JsonData = data.ToString(Formatting.None), CreatedAt = System.DateTime.UtcNow };
			await repository.SaveAsync(record, cancellationToken);
			return new ImportResponseDto { Success = true, Message = "Bóc tách và lưu dữ liệu mock thành công.", FileName = fileName, UserId = userId, DocumentId = documentId, Sheets = new List<string> { "MockAI" }, Data = data, RowCount = rowCount, ErrorCount = 0, Valid = true };
		}

		private static string ResolveConfiguredPath(string configuredPath)
		{
			return Path.GetFullPath(Path.IsPathRooted(configuredPath)
				? configuredPath
				: Path.Combine(AppDomain.CurrentDomain.BaseDirectory, configuredPath));
		}

		private static ImportResponseDto Failed(string message, string fileName, string userId, string documentId)
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
				Valid = false,
				RequiresReview = true
			};
		}
	}
}

