using System;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using EForm.ImportDocument.Domain;

namespace EForm.ImportDocument.Application
{
    public sealed class ImportJobService
    {
        private readonly IImportJobRepository _jobs;
        private readonly IImportFileStorage _files;
        private readonly IDocumentAuthorizationService _authorization;
        private readonly IAiImportClient _ai;
        private readonly IImportCommitGateway _commit;
        private readonly IClock _clock;

        public ImportJobService(IImportJobRepository jobs, IImportFileStorage files,
            IDocumentAuthorizationService authorization, IAiImportClient ai,
            IImportCommitGateway commit, IClock clock)
        {
            _jobs = jobs ?? throw new ArgumentNullException("jobs");
            _files = files ?? throw new ArgumentNullException("files");
            _authorization = authorization ?? throw new ArgumentNullException("authorization");
            _ai = ai ?? throw new ArgumentNullException("ai");
            _commit = commit ?? throw new ArgumentNullException("commit");
            _clock = clock ?? throw new ArgumentNullException("clock");
        }

        public async Task<ImportJob> CreateAsync(long documentId, long userId, long? organizationId,
            Stream stream, string fileName, CancellationToken cancellationToken)
        {
            await DemandAccess(documentId, userId, organizationId, cancellationToken).ConfigureAwait(false);
            var stored = await _files.SaveAsync(stream, fileName, cancellationToken).ConfigureAwait(false);
            var job = ImportJob.Create(documentId, userId, organizationId, _clock.UtcNow);
            job.OriginalFileName = stored.OriginalName;
            job.StoredFilePath = stored.FullPath;
            job.FileSha256 = stored.Sha256;
            job.FileSize = stored.Size;
            try
            {
                await _jobs.AddAsync(job, cancellationToken).ConfigureAwait(false);
                return job;
            }
            catch
            {
                await _files.DeleteAsync(stored.FullPath, cancellationToken).ConfigureAwait(false);
                throw;
            }
        }

        public async Task<ImportJob> AnalyzeAsync(Guid jobId, long userId, CancellationToken cancellationToken)
        {
            var job = await GetOwned(jobId, userId, cancellationToken).ConfigureAwait(false);
            await DemandAccess(job.DocumentId, userId, job.OrganizationId, cancellationToken).ConfigureAwait(false);
            var expected = job.Version;
            job.TransitionTo(ImportJobStatus.Analyzing, _clock.UtcNow);
            await _jobs.SaveAsync(job, expected, cancellationToken).ConfigureAwait(false);
            try
            {
                var analysis = await _ai.AnalyzeAsync(job.StoredFilePath, cancellationToken).ConfigureAwait(false);
                expected = job.Version;
                job.AnalysisJson = analysis.Json;
                job.ModelVersion = analysis.ModelVersion;
                job.TransitionTo(ImportJobStatus.Analyzed, _clock.UtcNow);
                await _jobs.SaveAsync(job, expected, cancellationToken).ConfigureAwait(false);
                return job;
            }
            catch
            {
                expected = job.Version;
                job.TransitionTo(ImportJobStatus.Failed, _clock.UtcNow);
                await _jobs.SaveAsync(job, expected, cancellationToken).ConfigureAwait(false);
                throw;
            }
        }

        public async Task<ImportJob> MapAsync(Guid jobId, long userId, string targetSchemaJson, CancellationToken cancellationToken)
        {
            var job = await GetOwned(jobId, userId, cancellationToken).ConfigureAwait(false);
            Require(job.Status == ImportJobStatus.Analyzed || job.Status == ImportJobStatus.Failed, "Job chưa sẵn sàng ánh xạ.");
            await DemandAccess(job.DocumentId, userId, job.OrganizationId, cancellationToken).ConfigureAwait(false);
            var mapping = await _ai.MapAsync(job.AnalysisJson, targetSchemaJson, cancellationToken).ConfigureAwait(false);
            var expected = job.Version;
            job.MappingJson = mapping;
            job.TransitionTo(ImportJobStatus.Mapped, _clock.UtcNow);
            await _jobs.SaveAsync(job, expected, cancellationToken).ConfigureAwait(false);
            return job;
        }

        public async Task<ImportJob> ValidateAsync(Guid jobId, long userId, string targetSchemaJson, CancellationToken cancellationToken)
        {
            var job = await GetOwned(jobId, userId, cancellationToken).ConfigureAwait(false);
            Require(job.Status == ImportJobStatus.Mapped, "Job chưa được ánh xạ.");
            await DemandAccess(job.DocumentId, userId, job.OrganizationId, cancellationToken).ConfigureAwait(false);
            var expected = job.Version;
            job.TransitionTo(ImportJobStatus.Validating, _clock.UtcNow);
            await _jobs.SaveAsync(job, expected, cancellationToken).ConfigureAwait(false);
            var validation = await _ai.ValidateAsync(job.MappingJson, targetSchemaJson, cancellationToken).ConfigureAwait(false);
            expected = job.Version;
            job.ValidationJson = validation.Json;
            job.ErrorCount = validation.ErrorCount;
            job.WarningCount = validation.WarningCount;
            job.TransitionTo(validation.IsValid ? ImportJobStatus.WaitingConfirmation : ImportJobStatus.Mapped, _clock.UtcNow);
            await _jobs.SaveAsync(job, expected, cancellationToken).ConfigureAwait(false);
            return job;
        }

        public async Task<ImportJob> ConfirmAsync(Guid jobId, long userId, CancellationToken cancellationToken)
        {
            var job = await GetOwned(jobId, userId, cancellationToken).ConfigureAwait(false);
            Require(job.Status == ImportJobStatus.WaitingConfirmation && job.ErrorCount == 0, "Job còn lỗi hoặc chưa chờ xác nhận.");
            await DemandAccess(job.DocumentId, userId, job.OrganizationId, cancellationToken).ConfigureAwait(false);
            var expected = job.Version;
            job.TransitionTo(ImportJobStatus.Confirmed, _clock.UtcNow);
            await _jobs.SaveAsync(job, expected, cancellationToken).ConfigureAwait(false);
            return job;
        }

        public async Task<CommitResult> CommitAsync(Guid jobId, long userId, CancellationToken cancellationToken)
        {
            var job = await GetOwned(jobId, userId, cancellationToken).ConfigureAwait(false);
            if (job.Status == ImportJobStatus.Committed)
                return new CommitResult { Reference = job.CommitReference };
            Require(job.Status == ImportJobStatus.Confirmed, "Job chưa được xác nhận.");
            await DemandAccess(job.DocumentId, userId, job.OrganizationId, cancellationToken).ConfigureAwait(false);
            var expected = job.Version;
            job.TransitionTo(ImportJobStatus.Committing, _clock.UtcNow);
            await _jobs.SaveAsync(job, expected, cancellationToken).ConfigureAwait(false);
            try
            {
                var result = await _commit.CommitAsync(job.DocumentId, job.MappingJson, job.ValidationJson,
                    job.Id.ToString("N"), userId, cancellationToken).ConfigureAwait(false);
                expected = job.Version;
                job.CommitReference = result.Reference;
                job.TransitionTo(ImportJobStatus.Committed, _clock.UtcNow);
                await _jobs.SaveAsync(job, expected, cancellationToken).ConfigureAwait(false);
                return result;
            }
            catch
            {
                expected = job.Version;
                job.TransitionTo(ImportJobStatus.Failed, _clock.UtcNow);
                await _jobs.SaveAsync(job, expected, cancellationToken).ConfigureAwait(false);
                throw;
            }
        }

        public Task<ImportJob> GetAsync(Guid jobId, long userId, CancellationToken cancellationToken)
        {
            return GetOwned(jobId, userId, cancellationToken);
        }

        private async Task<ImportJob> GetOwned(Guid id, long userId, CancellationToken cancellationToken)
        {
            var job = await _jobs.GetAsync(id, cancellationToken).ConfigureAwait(false);
            if (job == null) throw new ImportNotFoundException("Không tìm thấy import job.");
            if (job.UserId != userId) throw new ImportAuthorizationException("Import job không thuộc người dùng hiện tại.");
            return job;
        }

        private async Task DemandAccess(long documentId, long userId, long? organizationId, CancellationToken cancellationToken)
        {
            var decision = await _authorization.CanImportAsync(documentId, userId, organizationId, cancellationToken).ConfigureAwait(false);
            if (decision == null || !decision.Allowed || decision.IsLocked)
                throw new ImportAuthorizationException(decision == null ? "Không xác định được quyền." : decision.Reason ?? "Không có quyền hoặc biểu mẫu đã khóa.");
        }

        private static void Require(bool condition, string message)
        {
            if (!condition) throw new ImportValidationException(message);
        }
    }
}

