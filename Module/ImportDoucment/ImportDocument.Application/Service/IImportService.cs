using System.IO;
using System.Threading.Tasks;
using ImportDocument.Application.Dto;
namespace ImportDocument.Application.Services
{
    public interface IImportService
    {
        Task<object> GetHealthAsync();

        Task<ImportResponseDto> ImportAsync(
            Stream file,
            string fileName,
            string userId,
            string documentId);

        Task<SaveReportResponseDto> SaveReportAsync(
            SaveReportRequestDto request);
    }
}
