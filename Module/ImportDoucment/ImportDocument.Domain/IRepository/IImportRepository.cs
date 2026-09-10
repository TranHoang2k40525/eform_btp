using System.Threading;
using System.Threading.Tasks;
using ImportDocument.Domain.Entities;
namespace ImportDocument.Domain.Interfaces
{
    public interface IImportRepository
    {
        Task SaveAsync(FlatImportResult result, CancellationToken cancellationToken);
    }
}

