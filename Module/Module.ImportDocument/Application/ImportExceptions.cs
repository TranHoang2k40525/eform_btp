using System;

namespace EForm.ImportDocument.Application
{
    public sealed class ImportNotFoundException : Exception
    {
        public ImportNotFoundException(string message) : base(message) { }
    }

    public sealed class ImportAuthorizationException : Exception
    {
        public ImportAuthorizationException(string message) : base(message) { }
    }

    public sealed class ImportValidationException : Exception
    {
        public ImportValidationException(string message) : base(message) { }
    }

    public sealed class ImportConcurrencyException : Exception
    {
        public ImportConcurrencyException(string message) : base(message) { }
    }
}

