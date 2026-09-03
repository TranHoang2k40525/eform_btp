using System.Threading;
using System.Threading.Tasks;
using EForm.ImportDocument.Application;

namespace EForm.ImportDocument.Infrastructure
{
    // Chỉ dùng để chạy local; production phải thay bằng EFormImportPermission.
    public sealed class DevelopmentImportPermission : IImportPermission
    {
        public Task<ImportPermissionResult> CheckAsync(long documentId, long userId, long? organizationId, CancellationToken cancellationToken)
        {
            cancellationToken.ThrowIfCancellationRequested();
            return Task.FromResult(new ImportPermissionResult { Allowed = true, Locked = false });
        }
    }
}
