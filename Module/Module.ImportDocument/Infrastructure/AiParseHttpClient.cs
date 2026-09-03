using System;
using System.IO;
using System.Net.Http;
using System.Runtime.Serialization;
using System.Runtime.Serialization.Json;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using EForm.ImportDocument.Application;
using EForm.ImportDocument.Domain;

namespace EForm.ImportDocument.Infrastructure
{
    public sealed class AiParseHttpClient : IImportAiClient
    {
        private readonly HttpClient _http;
        public AiParseHttpClient(HttpClient http, Uri baseAddress)
        {
            _http = http ?? throw new ArgumentNullException("http");
            _http.BaseAddress = baseAddress ?? throw new ArgumentNullException("baseAddress");
            _http.Timeout = TimeSpan.FromSeconds(90);
        }

        public async Task<FlatImportResult> ParseAsync(string fullPath, string targetSchemaJson, CancellationToken cancellationToken)
        {
            var request = Serialize(new ParseRequest { Path = fullPath, TargetSchemaJson = targetSchemaJson,
                IncludeHidden = false, MaxRows = 50000 });
            using (var content = new StringContent(request, Encoding.UTF8, "application/json"))
            using (var response = await _http.PostAsync("parse", content, cancellationToken).ConfigureAwait(false))
            {
                var json = await response.Content.ReadAsStringAsync().ConfigureAwait(false);
                if (!response.IsSuccessStatusCode) throw new HttpRequestException("AI service lỗi " + (int)response.StatusCode + ": " + json);
                return new FlatImportResult { Json = json, ModelVersion = "from-ai-service" };
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

        [DataContract]
        private sealed class ParseRequest
        {
            [DataMember(Name = "path")] public string Path { get; set; }
            [DataMember(Name = "target_schema_json")] public string TargetSchemaJson { get; set; }
            [DataMember(Name = "include_hidden")] public bool IncludeHidden { get; set; }
            [DataMember(Name = "max_rows")] public int MaxRows { get; set; }
        }
    }
}
