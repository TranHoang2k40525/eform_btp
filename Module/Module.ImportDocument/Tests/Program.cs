using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using EForm.ImportDocument.Application;
using EForm.ImportDocument.Domain;
using EForm.ImportDocument.Infrastructure;

namespace EForm.ImportDocument.Tests
{
    internal static class Program
    {
        private static int _passed;

        private static void Assert(bool condition, string name)
        {
            if (!condition) throw new Exception("FAILED: " + name);
            _passed++;
            Console.WriteLine("PASS " + name);
        }

        private static async Task RunAsync()
        {
            var now = new DateTime(2026, 9, 3, 0, 0, 0, DateTimeKind.Utc);
            var domain = ImportJob.Create(1, 2, null, now);
            domain.TransitionTo(ImportJobStatus.Analyzing, now.AddSeconds(1));
            domain.TransitionTo(ImportJobStatus.Analyzed, now.AddSeconds(2));
            Assert(domain.Status == ImportJobStatus.Analyzed && domain.Version == 3, "state-machine-valid-transition");

            var rejected = false;
            try { domain.TransitionTo(ImportJobStatus.Committed, now); }
            catch (InvalidOperationException) { rejected = true; }
            Assert(rejected, "state-machine-rejects-skip");

            var repository = new InMemoryImportJobRepository();
            var service = new ImportJobService(repository, new FakeStorage(), new AllowAuthorization(),
                new FakeAi(), new IdempotentCommitGateway(), new FixedClock(now));
            var stream = new MemoryStream(Encoding.UTF8.GetBytes("fake-workbook"));
            var job = await service.CreateAsync(77, 9, 3, stream, "bao-cao.xlsx", CancellationToken.None);
            Assert(job.Status == ImportJobStatus.Uploaded, "upload-creates-job");
            await service.AnalyzeAsync(job.Id, 9, CancellationToken.None);
            await service.MapAsync(job.Id, 9, "{}", CancellationToken.None);
            await service.ValidateAsync(job.Id, 9, "{}", CancellationToken.None);
            await service.ConfirmAsync(job.Id, 9, CancellationToken.None);
            var first = await service.CommitAsync(job.Id, 9, CancellationToken.None);
            var second = await service.CommitAsync(job.Id, 9, CancellationToken.None);
            Assert(job.Status == ImportJobStatus.Committed, "full-flow-committed");
            Assert(first.Reference == second.Reference, "commit-is-idempotent");

            var unauthorized = false;
            try { await service.GetAsync(job.Id, 10, CancellationToken.None); }
            catch (ImportAuthorizationException) { unauthorized = true; }
            Assert(unauthorized, "job-owner-enforced");

            var lockedService = new ImportJobService(new InMemoryImportJobRepository(), new FakeStorage(),
                new LockedAuthorization(), new FakeAi(), new IdempotentCommitGateway(), new FixedClock(now));
            var locked = false;
            try { await lockedService.CreateAsync(1, 9, null, new MemoryStream(new byte[] { 1 }), "a.xlsx", CancellationToken.None); }
            catch (ImportAuthorizationException) { locked = true; }
            Assert(locked, "locked-document-rejected");

            var temp = Path.Combine(Path.GetTempPath(), "eform-import-tests-" + Guid.NewGuid().ToString("N"));
            Directory.CreateDirectory(temp);
            try
            {
                var storage = new SecureImportFileStorage(temp, 1024);
                var badExtension = false;
                try { await storage.SaveAsync(new MemoryStream(new byte[] { 1 }), "payload.exe", CancellationToken.None); }
                catch (ImportValidationException) { badExtension = true; }
                Assert(badExtension, "upload-extension-allowlist");
            }
            finally { Directory.Delete(temp, true); }
        }

        private static int Main()
        {
            try
            {
                RunAsync().GetAwaiter().GetResult();
                Console.WriteLine("RESULT: " + _passed + " tests passed");
                return 0;
            }
            catch (Exception exception)
            {
                Console.Error.WriteLine(exception);
                return 1;
            }
        }

        private sealed class FixedClock : IClock
        {
            public FixedClock(DateTime value) { UtcNow = value; }
            public DateTime UtcNow { get; private set; }
        }

        private sealed class FakeStorage : IImportFileStorage
        {
            public Task<StoredImportFile> SaveAsync(Stream input, string originalName, CancellationToken token)
                => Task.FromResult(new StoredImportFile { OriginalName = originalName, FullPath = "C:\\safe\\test.xlsx", Sha256 = "abc", Size = input.Length });
            public Task DeleteAsync(string path, CancellationToken token) => Task.CompletedTask;
        }

        private sealed class AllowAuthorization : IDocumentAuthorizationService
        {
            public Task<AuthorizationDecision> CanImportAsync(long documentId, long userId, long? organizationId, CancellationToken token)
                => Task.FromResult(new AuthorizationDecision { Allowed = true });
        }

        private sealed class LockedAuthorization : IDocumentAuthorizationService
        {
            public Task<AuthorizationDecision> CanImportAsync(long documentId, long userId, long? organizationId, CancellationToken token)
                => Task.FromResult(new AuthorizationDecision { Allowed = false, IsLocked = true, Reason = "locked" });
        }

        private sealed class FakeAi : IAiImportClient
        {
            public Task<AiAnalysisResult> AnalyzeAsync(string path, CancellationToken token)
                => Task.FromResult(new AiAnalysisResult { Json = "{\"sheets\":[]}", ModelVersion = "test-v1" });
            public Task<string> MapAsync(string analysis, string schema, CancellationToken token)
                => Task.FromResult("{\"mappings\":[]}");
            public Task<AiValidationResult> ValidateAsync(string mapping, string schema, CancellationToken token)
                => Task.FromResult(new AiValidationResult { Json = "{\"valid\":true}", IsValid = true });
        }

        private sealed class IdempotentCommitGateway : IImportCommitGateway
        {
            private readonly Dictionary<string, CommitResult> _results = new Dictionary<string, CommitResult>();
            public Task<CommitResult> CommitAsync(long documentId, string mapping, string validation, string key, long userId, CancellationToken token)
            {
                CommitResult result;
                if (!_results.TryGetValue(key, out result))
                {
                    result = new CommitResult { Reference = "commit-" + key, InsertedRows = 1 };
                    _results.Add(key, result);
                }
                return Task.FromResult(result);
            }
        }
    }
}

