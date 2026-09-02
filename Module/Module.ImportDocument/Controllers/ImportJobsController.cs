using System;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using EForm.ImportDocument.Application;
using EForm.ImportDocument.Domain;

namespace EForm.ImportDocument.Controllers
{
    /// <summary>
    /// Framework-neutral controller facade. The eForm Web API controller resolves the authenticated
    /// user from its existing authentication context and delegates here; it must never accept userId from JSON.
    /// </summary>
    public sealed class ImportJobsController
    {
        private readonly ImportJobService _service;
        public ImportJobsController(ImportJobService service) { _service = service; }

        public Task<ImportJob> Upload(long documentId, long authenticatedUserId, long? organizationId,
            Stream file, string fileName, CancellationToken cancellationToken)
        {
            return _service.CreateAsync(documentId, authenticatedUserId, organizationId, file, fileName, cancellationToken);
        }

        public Task<ImportJob> Analyze(Guid id, long authenticatedUserId, CancellationToken cancellationToken)
            => _service.AnalyzeAsync(id, authenticatedUserId, cancellationToken);

        public Task<ImportJob> Map(Guid id, long authenticatedUserId, string targetSchemaJson, CancellationToken cancellationToken)
            => _service.MapAsync(id, authenticatedUserId, targetSchemaJson, cancellationToken);

        public Task<ImportJob> Validate(Guid id, long authenticatedUserId, string targetSchemaJson, CancellationToken cancellationToken)
            => _service.ValidateAsync(id, authenticatedUserId, targetSchemaJson, cancellationToken);

        public Task<ImportJob> Confirm(Guid id, long authenticatedUserId, CancellationToken cancellationToken)
            => _service.ConfirmAsync(id, authenticatedUserId, cancellationToken);

        public Task<CommitResult> Commit(Guid id, long authenticatedUserId, CancellationToken cancellationToken)
            => _service.CommitAsync(id, authenticatedUserId, cancellationToken);

        public Task<ImportJob> Get(Guid id, long authenticatedUserId, CancellationToken cancellationToken)
            => _service.GetAsync(id, authenticatedUserId, cancellationToken);
    }
}

