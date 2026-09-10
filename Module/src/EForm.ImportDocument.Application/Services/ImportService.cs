using System.IO;
using System.Threading;
using System.Threading.Tasks;
using EForm.ImportDocument.Application.Dto;
namespace EForm.ImportDocument.Application.Services
{
    public class ImportService : IImportService
    {
        public async Task<ImportResponseDto> ImportAsync(Stream file, string fileName, string userId, string documentId, CancellationToken cancellationToken)
        {
            await Task.Yield();
            cancellationToken.ThrowIfCancellationRequested();
            if (file == null || file.Length == 0) return new ImportResponseDto { Success = false, Message = "File Excel rỗng." };
            // Mock AI contract: replace this block with HttpClient call to AiUrl later.
            var data = new object[0];
            return new ImportResponseDto { Success = true, Message = "Bóc tách thành công dữ liệu bảng biểu thành JSON.", FileName = fileName, UserId = userId, DocumentId = documentId, Sheets = new System.Collections.Generic.List<string> { "Sheet1" }, Data = data, RowCount = 0, ErrorCount = 0 };
        }
    }
}
