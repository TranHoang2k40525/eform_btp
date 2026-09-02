using System;
using EForm.ImportDocument.Application;

namespace EForm.ImportDocument.Infrastructure
{
    public sealed class SystemClock : IClock
    {
        public DateTime UtcNow { get { return DateTime.UtcNow; } }
    }
}

