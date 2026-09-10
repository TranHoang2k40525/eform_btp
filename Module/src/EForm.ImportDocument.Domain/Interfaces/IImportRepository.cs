using System.Threading;
using System.Threading.Tasks;
using EForm.ImportDocument.Domain.Entities;
namespace EForm.ImportDocument.Domain.Interfaces
{
    public interface IImportRepository
    {
        Task SaveAsync(FlatImportResult result, CancellationToken cancellationToken);
    }
}
