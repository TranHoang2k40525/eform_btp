using System;
using System.IO;
using System.Net.Http;
using System.Runtime.Serialization;
using System.Runtime.Serialization.Json;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using EForm.ImportDocument.Application;

namespace EForm.ImportDocument.Infrastructure
{
    public sealed class AiImportHttpClient : IAiImportClient
    {
        private readonly HttpClient _client;

        public AiImportHttpClient(HttpClient client, Uri baseAddress)
        {
            _client = client ?? throw new ArgumentNullException("client");
            _client.BaseAddress = baseAddress ?? throw new ArgumentNullException("baseAddress");
            _client.Timeout = TimeSpan.FromSeconds(60);
        }

        public async Task<AiAnalysisResult> AnalyzeAsync(string fullPath, CancellationToken cancellationToken)
        {
            var payload = Serialize(new AnalyzeRequest { Path = fullPath, IncludeHidden = false, PreviewRows = 100 });
            var json = await PostAsync("analyze", payload, cancellationToken).ConfigureAwait(false);
            var version = await GetAsync("model/version", cancellationToken).ConfigureAwait(false);
            return new AiAnalysisResult { Json = json, ModelVersion = version };
        }

        public Task<string> MapAsync(string analysisJson, string targetSchemaJson, CancellationToken cancellationToken)
        {
            // Adapter layer extracts the selected region and target fields into the stable AI /map contract.
            return PostAsync("map", targetSchemaJson, cancellationToken);
        }

        public async Task<AiValidationResult> ValidateAsync(string mappingJson, string targetSchemaJson, CancellationToken cancellationToken)
        {
            var json = await PostAsync("validate", targetSchemaJson, cancellationToken).ConfigureAwait(false);
            var compact = json.Replace(" ", string.Empty).ToLowerInvariant();
            return new AiValidationResult
            {
                Json = json,
                IsValid = compact.Contains("\"valid\":true"),
                ErrorCount = ReadInteger(json, "error_count"),
                WarningCount = ReadInteger(json, "warning_count")
            };
        }

        private async Task<string> PostAsync(string relative, string json, CancellationToken cancellationToken)
        {
            using (var content = new StringContent(json ?? "{}", Encoding.UTF8, "application/json"))
            using (var response = await _client.PostAsync(relative, content, cancellationToken).ConfigureAwait(false))
            {
                var body = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
                if (!response.IsSuccessStatusCode) throw new HttpRequestException("AI service lỗi " + (int)response.StatusCode + ": " + body);
                return body;
            }
        }

        private async Task<string> GetAsync(string relative, CancellationToken cancellationToken)
        {
            using (var response = await _client.GetAsync(relative, cancellationToken).ConfigureAwait(false))
            {
                var body = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
                if (!response.IsSuccessStatusCode) throw new HttpRequestException("AI service không phản hồi: " + body);
                return body;
            }
        }

        private static string Serialize<T>(T value)
        {
            var serializer = new DataContractJsonSerializer(typeof(T));
            using (var stream = new MemoryStream())
            {
                serializer.WriteObject(stream, value);
                return Encoding.UTF8.GetString(stream.ToArray());
            }
        }

        private static int ReadInteger(string json, string property)
        {
            var marker = "\"" + property + "\":";
            var start = json.IndexOf(marker, StringComparison.OrdinalIgnoreCase);
            if (start < 0) return 0;
            start += marker.Length;
            var end = start;
            while (end < json.Length && char.IsDigit(json[end])) end++;
            int value;
            return int.TryParse(json.Substring(start, end - start), out value) ? value : 0;
        }

        [DataContract]
        private sealed class AnalyzeRequest
        {
            [DataMember(Name = "path")] public string Path { get; set; }
            [DataMember(Name = "include_hidden")] public bool IncludeHidden { get; set; }
            [DataMember(Name = "preview_rows")] public int PreviewRows { get; set; }
        }
    }
}

