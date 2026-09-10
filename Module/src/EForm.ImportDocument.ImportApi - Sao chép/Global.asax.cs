using System.Web.Http;
using System.Web.Mvc;
using System.Web.Routing;
using System.Web;
using Ninject;
using EForm.ImportDocument.Infrastructure.DependencyInjection;
namespace EForm.ImportDocument.ImportApi
{
    public class WebApiApplication : HttpApplication
    {
        protected void Application_Start()
        {
            AreaRegistration.RegisterAllAreas();
            GlobalConfiguration.Configure(App_Start.WebApiConfig.Register);
            App_Start.NinjectConfig.Register(GlobalConfiguration.Configuration);
            RouteConfig.RegisterRoutes(RouteTable.Routes);
        }
    }
}
