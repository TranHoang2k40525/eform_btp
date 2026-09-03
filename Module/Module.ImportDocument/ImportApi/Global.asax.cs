using System;
using System.Configuration;
using System.IO;
using System.Net.Http;
using System.Web;
using System.Web.Http;

namespace EForm.ImportDocument.ImportApi
{
    public class WebApiApplication : HttpApplication
    {
        protected void Application_Start()
        {
            var configuredRoot = ConfigurationManager.AppSettings["ImportUploadRoot"];
            var uploadRoot = string.IsNullOrWhiteSpace(configuredRoot) ? Server.MapPath("~/App_Data/Uploads") : configuredRoot;
            if (uploadRoot.StartsWith("~", StringComparison.Ordinal)) uploadRoot = Server.MapPath(uploadRoot);
            var aiUrl = ConfigurationManager.AppSettings["ImportAiBaseUrl"] ?? "http://127.0.0.1:8010/";
            GlobalConfiguration.Configure(App_Start.WebApiConfig.Register);
            App_Start.DependencyConfig.Register(GlobalConfiguration.Configuration, uploadRoot, aiUrl);
        }
    }
}
