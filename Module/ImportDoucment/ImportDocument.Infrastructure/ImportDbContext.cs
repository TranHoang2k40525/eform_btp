using System.Data.Entity;
using ImportDocument.Domain.Entities;
using ImportDocument.Infrastructure.Configuration;
namespace ImportDocument.Infrastructure
{
    public class ImportDbContext : DbContext
    {
        public ImportDbContext() : base("ImportDb") { }
        public DbSet<ImportRecord> ImportRecords { get; set; }
        protected override void OnModelCreating(DbModelBuilder modelBuilder)
        {
            modelBuilder.Configurations.Add(new ImportRecordConfiguration());
            base.OnModelCreating(modelBuilder);
        }
    }
}
