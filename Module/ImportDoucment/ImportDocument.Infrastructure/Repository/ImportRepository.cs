using System.Threading;
using System.Threading.Tasks;
using ImportDocument.Domain.Entities;
using ImportDocument.Domain.Interfaces;
namespace ImportDocument.Infrastructure.Repository
{
    public class ImportRepository : IImportRepository
    {
        private readonly ImportDbContext context;
        public ImportRepository(ImportDbContext context) { this.context = context; }
        public async Task SaveAsync(ImportRecord result, CancellationToken cancellationToken)
        {
            context.ImportRecords.Add(result);
            await context.SaveChangesAsync(cancellationToken);
        }
    }
}
