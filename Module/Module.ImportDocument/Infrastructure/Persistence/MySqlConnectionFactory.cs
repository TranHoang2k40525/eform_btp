using System;
using System.Data.Common;
using MySql.Data.MySqlClient;

namespace EForm.ImportDocument.Infrastructure
{
    public class MySqlConnectionFactory
    {
        private readonly string _connectionString;
        public MySqlConnectionFactory(string connectionString)
        {
            if (string.IsNullOrWhiteSpace(connectionString)) throw new ArgumentNullException("connectionString");
            _connectionString = connectionString;
        }

        public DbConnection Create() { return new MySqlConnection(_connectionString); }
    }
}
