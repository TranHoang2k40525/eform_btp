using System.Collections.Generic;
namespace ImportDocument.Application.Dto
{
    public class ImportResponseDto
    {
        public bool Success { get; set; }
        public string Message { get; set; }
        public string FileName { get; set; }
        public List<string> Sheets { get; set; }
        public object Data { get; set; }
        public int RowCount { get; set; }
        public int ErrorCount { get; set; }
        public string UserId { get; set; }
        public string DocumentId { get; set; }
        public object Errors { get; set; }
    }
}

