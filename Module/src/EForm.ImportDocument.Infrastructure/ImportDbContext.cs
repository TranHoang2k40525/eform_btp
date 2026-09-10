using System.Data.Entity;
using EForm.ImportDocument.Domain.Entities;
namespace EForm.ImportDocument.Infrastructure
{
    public class ImportDbContext : DbContext
    {
        public ImportDbContext() : base("ImportDb") { }
        public DbSet<ImportRecord> ImportRecords { get; set; }
    }
}
