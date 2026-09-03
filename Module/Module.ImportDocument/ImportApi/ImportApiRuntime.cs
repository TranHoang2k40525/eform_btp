using System;
using EForm.ImportDocument.Application;

namespace EForm.ImportDocument.ImportApi
{
    public static class ImportApiRuntime
    {
        private static ImportPipelineService _service;
        public static ImportPipelineService Service
        {
            get { return _service ?? throw new InvalidOperationException("ImportApi chưa được cấu hình."); }
        }

        public static void Configure(ImportPipelineService service)
        {
            _service = service ?? throw new ArgumentNullException("service");
        }
    }
}
