using System;
using System.Threading;
using System.Threading.Tasks;
using EForm.ImportDocument.Application;

namespace EForm.ImportDocument.Integration
{
    /// <summary>Ports that must be wired to DocumentPermissions.SuaVanBan and TaskReportPeriod.IsLock.</summary>
    public interface IEFormPermissionPort
    {
        bool CanEditDocument(long documentId, long userId, long? organizationId);
        bool IsDocumentLocked(long documentId);
    }

    public sealed class EFormDocumentAuthorizationAdapter : IDocumentAuthorizationService
    {
        private readonly IEFormPermissionPort _port;
        public EFormDocumentAuthorizationAdapter(IEFormPermissionPort port) { _port = port; }

        public Task<AuthorizationDecision> CanImportAsync(long documentId, long userId, long? organizationId,
            CancellationToken cancellationToken)
        {
            cancellationToken.ThrowIfCancellationRequested();
            var locked = _port.IsDocumentLocked(documentId);
            var canEdit = _port.CanEditDocument(documentId, userId, organizationId);
            return Task.FromResult(new AuthorizationDecision
            {
                Allowed = canEdit && !locked,
                IsLocked = locked,
                Reason = locked ? "Kỳ báo cáo/biểu mẫu đã khóa." : canEdit ? null : "Thiếu quyền Sửa văn bản."
            });
        }
    }

    /// <summary>
    /// Implement this port using the existing eForm save service that persists DocumentContent.SourceData,
    /// ValueData, FormConfig and FormStyle in one transaction. Do not write those tables from the AI service.
    /// </summary>
    public interface IEFormDocumentWritePort
    {
        CommitResult SaveImportedDocument(long documentId, string mappingJson, string validationJson,
            string idempotencyKey, long userId);
    }

    public sealed class EFormCommitGateway : IImportCommitGateway
    {
        private readonly IEFormDocumentWritePort _port;
        public EFormCommitGateway(IEFormDocumentWritePort port) { _port = port; }

        public Task<CommitResult> CommitAsync(long documentId, string mappingJson, string validationJson,
            string idempotencyKey, long userId, CancellationToken cancellationToken)
        {
            cancellationToken.ThrowIfCancellationRequested();
            return Task.FromResult(_port.SaveImportedDocument(documentId, mappingJson, validationJson, idempotencyKey, userId));
        }
    }
}

