using System;

namespace EForm.ImportDocument.Domain
{
    public sealed class ImportMapping
    {
        public long Id { get; set; }
        public Guid JobId { get; set; }
        public int SourceColumn { get; set; }
        public string SourceHeader { get; set; }
        public string TargetFieldId { get; set; }
        public decimal Confidence { get; set; }
        public string Decision { get; set; }
        public string ProvenanceJson { get; set; }
        public bool UserConfirmed { get; set; }
    }

    public sealed class ImportError
    {
        public long Id { get; set; }
        public Guid JobId { get; set; }
        public int? RowNumber { get; set; }
        public int? ColumnNumber { get; set; }
        public string FieldId { get; set; }
        public string Severity { get; set; }
        public string Code { get; set; }
        public string Message { get; set; }
    }

    public sealed class ImportMappingFeedback
    {
        public long Id { get; set; }
        public Guid JobId { get; set; }
        public string SourceHeader { get; set; }
        public string SuggestedFieldId { get; set; }
        public string SelectedFieldId { get; set; }
        public bool Accepted { get; set; }
        public decimal Confidence { get; set; }
        public long UserId { get; set; }
        public DateTime CreatedUtc { get; set; }
    }

    public sealed class ModelVersion
    {
        public long Id { get; set; }
        public string Name { get; set; }
        public string Version { get; set; }
        public string Sha256 { get; set; }
        public string MetricsJson { get; set; }
        public bool IsActive { get; set; }
        public DateTime CreatedUtc { get; set; }
    }
}

