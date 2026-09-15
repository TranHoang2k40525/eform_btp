using System.IO;
using System.Threading;
using System.Threading.Tasks;
using ImportDocument.Application.Dto;
namespace ImportDocument.Application.Services
{
    public interface IImportService
    {
        Task<object> GetHealthAsync(CancellationToken cancellationToken);

        Task<ImportResponseDto> ImportAsync(
            Stream file,
            string fileName,
            string userId,
            string documentId,
            CancellationToken cancellationToken);
    }
}

