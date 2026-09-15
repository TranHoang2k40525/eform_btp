using System.Configuration;
namespace ImportDocument.Infrastructure.Configuration
{
    public class ImportSettings
    {
        public string AiUrl { get { return ConfigurationManager.AppSettings["AiUrl"] ?? "http://127.0.0.1:8010/api/eform/extract"; } }
        public string ConnectionString { get { return ConfigurationManager.ConnectionStrings["ImportDb"] == null ? "" : ConfigurationManager.ConnectionStrings["ImportDb"].ConnectionString; } }
    }
}

