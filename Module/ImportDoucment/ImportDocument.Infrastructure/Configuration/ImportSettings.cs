using System.Configuration;
namespace ImportDocument.Infrastructure.Configuration
{
    public class ImportSettings
    {
        public string AiUrl { get { return ConfigurationManager.AppSettings["AiUrl"] ?? "http://localhost:5005/api/ai/import"; } }
        public string ConnectionString { get { return ConfigurationManager.ConnectionStrings["ImportDb"] == null ? "" : ConfigurationManager.ConnectionStrings["ImportDb"].ConnectionString; } }
    }
}

