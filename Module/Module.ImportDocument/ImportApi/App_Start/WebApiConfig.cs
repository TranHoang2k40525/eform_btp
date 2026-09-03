using System.Web.Http;

namespace EForm.ImportDocument.ImportApi.App_Start
{
    public static class WebApiConfig
    {
        public static void Register(HttpConfiguration configuration)
        {
            configuration.MapHttpAttributeRoutes();
            SwaggerConfig.Register(configuration);
            configuration.Routes.MapHttpRoute("DefaultApi", "api/{controller}/{id}", new { id = RouteParameter.Optional });
        }
    }
}
