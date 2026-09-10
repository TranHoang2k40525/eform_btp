using System.Web.Http;
using Swashbuckle.Application;

namespace ImportDocumentAPI.App_Start
{
    public static class SwaggerConfig
    {
        public static void Register(HttpConfiguration config)
        {
            config.EnableSwagger(c =>
            {
                c.SingleApiVersion("v1", "Import Document API");
                c.OperationFilter<SwaggerFileUploadFilter>();
            })
                  .EnableSwaggerUi();
        }
    }
}
