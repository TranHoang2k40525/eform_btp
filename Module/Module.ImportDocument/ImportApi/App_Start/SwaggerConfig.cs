using System.Web.Http;
using Swashbuckle.Application;

namespace EForm.ImportDocument.ImportApi.App_Start
{
    public static class SwaggerConfig
    {
        public static void Register(HttpConfiguration configuration)
        {
            configuration.EnableSwagger(c => c.SingleApiVersion("v1", "eForm Import API"))
                .EnableSwaggerUi();
        }
    }
}
