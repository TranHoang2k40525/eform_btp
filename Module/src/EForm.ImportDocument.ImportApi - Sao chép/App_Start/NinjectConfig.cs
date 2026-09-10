using System;
using System.Collections.Generic;
using System.Web.Http;
using System.Web.Http.Dependencies;
using Ninject;
using EForm.ImportDocument.Application.Services;
namespace EForm.ImportDocument.ImportApi.App_Start
{
    public class NinjectDependencyResolver : NinjectDependencyScope, IDependencyResolver
    {
        private readonly IKernel kernel;
        public NinjectDependencyResolver(IKernel kernel) : base(kernel) { this.kernel = kernel; }
        public IDependencyScope BeginScope() { return new NinjectDependencyScope(kernel.BeginBlock()); }
    }
    public class NinjectDependencyScope : IDependencyScope
    {
        protected readonly IResolutionRoot ResolutionRoot;
        public NinjectDependencyScope(IResolutionRoot root) { ResolutionRoot = root; }
        public object GetService(Type serviceType) { return serviceType == null ? null : ResolutionRoot.TryGet(serviceType); }
        public IEnumerable<object> GetServices(Type serviceType) { return serviceType == null ? new object[0] : ResolutionRoot.GetAll(serviceType); }
        public void Dispose() { }
    }
    public static class NinjectConfig
    {
        public static void Register(HttpConfiguration config)
        {
            var kernel = new StandardKernel();
            kernel.Bind<IImportService>().To<ImportService>().InThreadScope();
            config.DependencyResolver = new NinjectDependencyResolver(kernel);
        }
    }
}
