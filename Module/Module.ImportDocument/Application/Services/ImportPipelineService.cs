using System;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using EForm.ImportDocument.Domain;

namespace EForm.ImportDocument.Application
{
    public class StoredWorkbook
    {
        public string FullPath { get; set; }
        public string OriginalName { get; set; }
        public string Sha256 { get; set; }
        public long Size { get; set; }
    }

    public class ImportPermissionResult
    {
        public bool Allowed { get; set; }
        public bool Locked { get; set; }
        public string Reason { get; set; }
    }

    public interface IImportPermission
    {
        Task<ImportPermissionResult> CheckAsync(long documentId, long userId, long? organizationId, CancellationToken cancellationToken);
    }

    public interface IWorkbookStorage
    {
        Task<StoredWorkbook> SaveAsync(Stream stream, string originalName, CancellationToken cancellationToken);
        Task DeleteAsync(string fullPath, CancellationToken cancellationToken);
    }

    public interface IImportAiClient
    {
        Task<FlatImportResult> ParseAsync(string fullPath, string targetSchemaJson, CancellationToken cancellationToken);
    }

    public class ImportPipelineService
    {
        private readonly IImportPermission _permission;
        private readonly IWorkbookStorage _storage;
        private readonly IImportAiClient _ai;

        public ImportPipelineService(IImportPermission permission, IWorkbookStorage storage, IImportAiClient ai)
        {
            _permission = permission ?? throw new ArgumentNullException("permission");
            _storage = storage ?? throw new ArgumentNullException("storage");
            _ai = ai ?? throw new ArgumentNullException("ai");
        }

        public async Task<FlatImportResult> ParseAsync(ImportRequestContext context, Stream workbook,
            string originalName, CancellationToken cancellationToken)
        {
            if (context == null || context.DocumentId <= 0 || context.UserId <= 0)
                throw new ImportRequestException("documentId/userId không hợp lệ.");
            if (string.IsNullOrWhiteSpace(context.TargetSchemaJson))
                throw new ImportRequestException("Thiếu targetSchemaJson.");
            var permission = await _permission.CheckAsync(context.DocumentId, context.UserId,
                context.OrganizationId, cancellationToken).ConfigureAwait(false);
            if (permission == null || !permission.Allowed || permission.Locked)
                throw new ImportPermissionException(permission == null ? "Không xác định được quyền." : permission.Reason ?? "Không có quyền hoặc văn bản đã khóa.");

            StoredWorkbook stored = null;
            try
            {
                stored = await _storage.SaveAsync(workbook, originalName, cancellationToken).ConfigureAwait(false);
                return await _ai.ParseAsync(stored.FullPath, context.TargetSchemaJson, cancellationToken).ConfigureAwait(false);
            }
            finally
            {
                if (stored != null)
                    await _storage.DeleteAsync(stored.FullPath, cancellationToken).ConfigureAwait(false);
            }
        }
    }

    public class ImportRequestException : Exception
    {
        public ImportRequestException(string message) : base(message) { }
    }

    public class ImportPermissionException : Exception
    {
        public ImportPermissionException(string message) : base(message) { }
    }
}
