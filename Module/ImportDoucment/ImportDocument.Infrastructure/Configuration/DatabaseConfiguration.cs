using System.Data.Entity.ModelConfiguration;
using ImportDocument.Domain.Entities;
namespace ImportDocument.Infrastructure.Configuration
{
    public class ImportRecordConfiguration : EntityTypeConfiguration<ImportRecord>
    {
        public ImportRecordConfiguration()
        {
            ToTable("import_records");
            HasKey(x => x.Id);
            Property(x => x.DocumentId).HasMaxLength(100).IsRequired();
            Property(x => x.UserId).HasMaxLength(100).IsRequired();
            Property(x => x.FileName).HasMaxLength(255).IsRequired();
            Property(x => x.JsonData).IsRequired();
        }
    }
}
