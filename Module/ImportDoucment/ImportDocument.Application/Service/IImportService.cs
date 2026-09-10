using System.IO;
using System.Threading;
using System.Threading.Tasks;
using ImportDocument.Application.Dto;
namespace ImportDocument.Application.Services
{
    public interface IImportService
    {
        Task<ImportResponseDto> ImportAsync(
            Stream file,
            string fileName,
            string userId,
            string documentId,
            string targetSchemaJson,
            string docTypeCode,
            int formIndex,
            CancellationToken cancellationToken);
    }
}

