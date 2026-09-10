using System.IO;
using System.Threading;
using System.Threading.Tasks;
using EForm.ImportDocument.Application.Dto;
namespace EForm.ImportDocument.Application.Services
{
    public interface IImportService
    {
        Task<ImportResponseDto> ImportAsync(Stream file, string fileName, string userId, string documentId, CancellationToken cancellationToken);
    }
}
