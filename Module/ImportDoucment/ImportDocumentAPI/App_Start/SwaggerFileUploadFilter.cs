using System.Collections.Generic;
using System.Web.Http.Description;
using Swashbuckle.Swagger;

namespace ImportDocumentAPI.App_Start
{
    public class SwaggerFileUploadFilter : IOperationFilter
    {
        public void Apply(Operation operation, SchemaRegistry schemaRegistry, ApiDescription apiDescription)
        {
            if (apiDescription.RelativePath != "api/import/parse") return;
            operation.consumes = new List<string> { "multipart/form-data" };
            operation.parameters = new List<Parameter>
            {
                new Parameter { name = "file", @in = "formData", required = true, type = "file", description = "Tệp Excel .xlsx hoặc .xls" },
                new Parameter { name = "userId", @in = "formData", required = true, type = "string" },
                new Parameter { name = "documentId", @in = "formData", required = true, type = "string" }
            };
        }
    }
}
