using System;
using System.Net.Http;
using System.Web.Http;
using Autofac;
using Autofac.Integration.WebApi;
using AutoMapper;
using EForm.ImportDocument.Application;
using EForm.ImportDocument.Infrastructure;

namespace EForm.ImportDocument.ImportApi.App_Start
{
    public static class DependencyConfig
    {
        public static void Register(HttpConfiguration configuration, string uploadRoot, string aiBaseUrl)
        {
            var builder = new ContainerBuilder();
            builder.RegisterApiControllers(typeof(DependencyConfig).Assembly);
            builder.Register(ctx => new MapperConfiguration(c => c.AddProfile<ImportMappingProfile>())).SingleInstance();
            builder.Register(ctx => ctx.Resolve<MapperConfiguration>().CreateMapper()).As<IMapper>().SingleInstance();
            builder.RegisterType<DevelopmentImportPermission>().As<IImportPermission>().SingleInstance();
            builder.Register(c => new SecureWorkbookStorage(uploadRoot)).As<IWorkbookStorage>().SingleInstance();
            builder.Register(c => new AiParseHttpClient(new HttpClient(), new Uri(aiBaseUrl))).As<IImportAiClient>().SingleInstance();
            builder.RegisterType<ImportPipelineService>().InstancePerRequest();
            configuration.DependencyResolver = new AutofacWebApiDependencyResolver(builder.Build());
        }
    }

    public sealed class ImportMappingProfile : Profile
    {
        public ImportMappingProfile() { }
    }
}
