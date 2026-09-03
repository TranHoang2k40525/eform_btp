using System.Threading;
using System.Threading.Tasks;
using EForm.ImportDocument.Application;

namespace EForm.ImportDocument.Infrastructure
{
    public interface IEFormImportPermissionPort
    {
        bool CanEditDocument(long documentId, long userId, long? organizationId);
        bool IsDocumentLocked(long documentId);
    }

    public sealed class EFormImportPermission : IImportPermission
    {
        private readonly IEFormImportPermissionPort _port;
        public EFormImportPermission(IEFormImportPermissionPort port) { _port = port; }
        public Task<ImportPermissionResult> CheckAsync(long documentId, long userId, long? organizationId, CancellationToken cancellationToken)
        {
            cancellationToken.ThrowIfCancellationRequested();
            var locked = _port.IsDocumentLocked(documentId);
            var allowed = _port.CanEditDocument(documentId, userId, organizationId);
            return Task.FromResult(new ImportPermissionResult { Allowed = allowed && !locked, Locked = locked,
                Reason = locked ? "TaskReportPeriod.IsLock đang bật." : allowed ? null : "DocumentPermissions.SuaVanBan bị từ chối." });
        }
    }
}
