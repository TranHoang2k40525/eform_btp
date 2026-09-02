namespace EForm.ImportDocument.Domain
{
    public enum ImportJobStatus
    {
        Uploaded = 10,
        Analyzing = 20,
        Analyzed = 30,
        Mapped = 40,
        Validating = 50,
        WaitingConfirmation = 60,
        Confirmed = 70,
        Committing = 80,
        Committed = 90,
        Failed = 100,
        Cancelled = 110
    }
}

