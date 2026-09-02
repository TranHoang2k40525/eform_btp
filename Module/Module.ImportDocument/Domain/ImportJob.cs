using System;
using System.Collections.Generic;

namespace EForm.ImportDocument.Domain
{
    public sealed class ImportJob
    {
        private static readonly IDictionary<ImportJobStatus, ImportJobStatus[]> Allowed =
            new Dictionary<ImportJobStatus, ImportJobStatus[]>
            {
                { ImportJobStatus.Uploaded, new[] { ImportJobStatus.Analyzing, ImportJobStatus.Cancelled, ImportJobStatus.Failed } },
                { ImportJobStatus.Analyzing, new[] { ImportJobStatus.Analyzed, ImportJobStatus.Failed } },
                { ImportJobStatus.Analyzed, new[] { ImportJobStatus.Mapped, ImportJobStatus.Cancelled, ImportJobStatus.Failed } },
                { ImportJobStatus.Mapped, new[] { ImportJobStatus.Validating, ImportJobStatus.Cancelled, ImportJobStatus.Failed } },
                { ImportJobStatus.Validating, new[] { ImportJobStatus.WaitingConfirmation, ImportJobStatus.Mapped, ImportJobStatus.Failed } },
                { ImportJobStatus.WaitingConfirmation, new[] { ImportJobStatus.Confirmed, ImportJobStatus.Mapped, ImportJobStatus.Cancelled } },
                { ImportJobStatus.Confirmed, new[] { ImportJobStatus.Committing, ImportJobStatus.Cancelled } },
                { ImportJobStatus.Committing, new[] { ImportJobStatus.Committed, ImportJobStatus.Failed } },
                { ImportJobStatus.Failed, new[] { ImportJobStatus.Analyzing, ImportJobStatus.Mapped, ImportJobStatus.Cancelled } }
            };

        public Guid Id { get; set; }
        public long DocumentId { get; set; }
        public long UserId { get; set; }
        public long? OrganizationId { get; set; }
        public ImportJobStatus Status { get; private set; }
        public string OriginalFileName { get; set; }
        public string StoredFilePath { get; set; }
        public string FileSha256 { get; set; }
        public long FileSize { get; set; }
        public string AnalysisJson { get; set; }
        public string MappingJson { get; set; }
        public string ValidationJson { get; set; }
        public string ModelVersion { get; set; }
        public string CommitReference { get; set; }
        public int ErrorCount { get; set; }
        public int WarningCount { get; set; }
        public DateTime CreatedUtc { get; set; }
        public DateTime UpdatedUtc { get; set; }
        public DateTime? ExpiresUtc { get; set; }
        public int Version { get; private set; }

        public static ImportJob Create(long documentId, long userId, long? organizationId, DateTime utcNow)
        {
            if (documentId <= 0) throw new ArgumentOutOfRangeException("documentId");
            if (userId <= 0) throw new ArgumentOutOfRangeException("userId");
            return new ImportJob
            {
                Id = Guid.NewGuid(), DocumentId = documentId, UserId = userId, OrganizationId = organizationId,
                Status = ImportJobStatus.Uploaded, CreatedUtc = utcNow, UpdatedUtc = utcNow,
                ExpiresUtc = utcNow.AddDays(7), Version = 1
            };
        }

        public void TransitionTo(ImportJobStatus next, DateTime utcNow)
        {
            ImportJobStatus[] targets;
            if (!Allowed.TryGetValue(Status, out targets) || Array.IndexOf(targets, next) < 0)
                throw new InvalidOperationException(string.Format("Không thể chuyển import job từ {0} sang {1}.", Status, next));
            Status = next;
            UpdatedUtc = utcNow;
            checked { Version++; }
        }
    }
}

