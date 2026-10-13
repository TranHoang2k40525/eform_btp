using System.Data.Entity;
using System.Configuration;
using ImportDocument.Domain.Entities;
using ImportDocument.Infrastructure.Configuration;
using MySql.Data.MySqlClient;
namespace ImportDocument.Infrastructure
{
    public class ImportDbContext : DbContext
    {
        public ImportDbContext() : base(BuildConnection(), true) { }
        public DbSet<ImportRecord> ImportRecords { get; set; }

        private static MySqlConnection BuildConnection()
        {
            var configured = ConfigurationManager.ConnectionStrings["ImportDb"];
            if (configured == null || string.IsNullOrWhiteSpace(configured.ConnectionString))
                throw new ConfigurationErrorsException("Thiếu connection string ImportDb.");

            var dataSource = ConfigurationManager.AppSettings["EformDataSource"];
            var builder = new MySqlConnectionStringBuilder(configured.ConnectionString);
            if (!string.IsNullOrWhiteSpace(dataSource))
                builder.Database = dataSource;
            return new MySqlConnection(builder.ConnectionString);
        }

        protected override void OnModelCreating(DbModelBuilder modelBuilder)
        {
            modelBuilder.Configurations.Add(new ImportRecordConfiguration());
            base.OnModelCreating(modelBuilder);
        }
    }
}
