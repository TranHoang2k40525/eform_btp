using System.Web.Http.Dependencies;
using Ninject;
using Ninject.Web.Common;
using EForm.ImportDocument.Application.Services;
namespace EForm.ImportDocument.Infrastructure.DependencyInjection
{
    public class DependencyConfig
    {
        public static IKernel CreateKernel()
        {
            var kernel = new StandardKernel();
            kernel.Bind<IImportService>().To<ImportService>().InRequestScope();
            return kernel;
        }
    }
}
