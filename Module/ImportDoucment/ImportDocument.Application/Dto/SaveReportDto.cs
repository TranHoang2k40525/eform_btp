using System;
using System.Collections.Generic;

namespace ImportDocument.Application.Dto
{
    public class SaveReportRequestDto
    {
        public string DocumentId { get; set; }
        public string UserId { get; set; }
        public string FileName { get; set; }
        public string SheetName { get; set; }
        public string SourceRange { get; set; }
        public object TableData { get; set; }
        public object Corrections { get; set; }
        public string AiModelVersion { get; set; }
        public string RawJson { get; set; }
    }

    public class SaveReportResponseDto
    {
        public bool Success { get; set; }
        public int RecordId { get; set; }
        public string Message { get; set; }
        public string CreatedAt { get; set; }
    }
}
