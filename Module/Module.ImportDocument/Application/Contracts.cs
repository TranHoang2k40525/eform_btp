using System;
using System.Collections.Generic;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using EForm.ImportDocument.Domain;

namespace EForm.ImportDocument.Application
{
    public sealed class StoredImportFile
    {
        public string OriginalName { get; set; }
        public string FullPath { get; set; }
        public string Sha256 { get; set; }
        public long Size { get; set; }
    }

    public sealed class AuthorizationDecision
    {
        public bool Allowed { get; set; }
        public bool IsLocked { get; set; }
        public string Reason { get; set; }
    }

    public sealed class AiAnalysisResult
    {
        public string Json { get; set; }
        public string ModelVersion { get; set; }
    }

    public sealed class AiValidationResult
    {
        public string Json { get; set; }
        public bool IsValid { get; set; }
        public int ErrorCount { get; set; }
        public int WarningCount { get; set; }
    }

    public sealed class CommitResult
    {
        public string Reference { get; set; }
        public int InsertedRows { get; set; }
        public int UpdatedRows { get; set; }
    }

    public interface IImportJobRepository
    {
        Task AddAsync(ImportJob job, CancellationToken cancellationToken);
        Task<ImportJob> GetAsync(Guid id, CancellationToken cancellationToken);
        Task SaveAsync(ImportJob job, int expectedVersion, CancellationToken cancellationToken);
        Task<IReadOnlyList<ImportError>> GetErrorsAsync(Guid jobId, CancellationToken cancellationToken);
    }

    public interface IImportFileStorage
    {
        Task<StoredImportFile> SaveAsync(Stream input, string originalName, CancellationToken cancellationToken);
        Task DeleteAsync(string fullPath, CancellationToken cancellationToken);
    }

    public interface IDocumentAuthorizationService
    {
        Task<AuthorizationDecision> CanImportAsync(long documentId, long userId, long? organizationId, CancellationToken cancellationToken);
    }

    public interface IAiImportClient
    {
        Task<AiAnalysisResult> AnalyzeAsync(string fullPath, CancellationToken cancellationToken);
        Task<string> MapAsync(string analysisJson, string targetSchemaJson, CancellationToken cancellationToken);
        Task<AiValidationResult> ValidateAsync(string mappingJson, string targetSchemaJson, CancellationToken cancellationToken);
    }

    public interface IImportCommitGateway
    {
        Task<CommitResult> CommitAsync(long documentId, string mappingJson, string validationJson, string idempotencyKey,
            long userId, CancellationToken cancellationToken);
    }

    public interface IClock
    {
        DateTime UtcNow { get; }
    }
}

