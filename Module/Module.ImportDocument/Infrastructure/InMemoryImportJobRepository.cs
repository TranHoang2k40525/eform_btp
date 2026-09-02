using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using EForm.ImportDocument.Application;
using EForm.ImportDocument.Domain;

namespace EForm.ImportDocument.Infrastructure
{
    public sealed class InMemoryImportJobRepository : IImportJobRepository
    {
        private readonly ConcurrentDictionary<Guid, ImportJob> _items = new ConcurrentDictionary<Guid, ImportJob>();

        public Task AddAsync(ImportJob job, CancellationToken cancellationToken)
        {
            cancellationToken.ThrowIfCancellationRequested();
            if (!_items.TryAdd(job.Id, job)) throw new ImportConcurrencyException("Import job đã tồn tại.");
            return Task.CompletedTask;
        }

        public Task<ImportJob> GetAsync(Guid id, CancellationToken cancellationToken)
        {
            cancellationToken.ThrowIfCancellationRequested();
            ImportJob value;
            _items.TryGetValue(id, out value);
            return Task.FromResult(value);
        }

        public Task SaveAsync(ImportJob job, int expectedVersion, CancellationToken cancellationToken)
        {
            cancellationToken.ThrowIfCancellationRequested();
            if (job.Version != expectedVersion + 1)
                throw new ImportConcurrencyException("Version của import job không hợp lệ.");
            ImportJob current;
            if (!_items.TryGetValue(job.Id, out current)) throw new ImportNotFoundException("Không tìm thấy import job.");
            // Production repository must use: UPDATE ... WHERE id=@id AND version=@expectedVersion.
            _items[job.Id] = job;
            return Task.CompletedTask;
        }

        public Task<IReadOnlyList<ImportError>> GetErrorsAsync(Guid jobId, CancellationToken cancellationToken)
        {
            IReadOnlyList<ImportError> empty = Enumerable.Empty<ImportError>().ToList();
            return Task.FromResult(empty);
        }
    }
}

