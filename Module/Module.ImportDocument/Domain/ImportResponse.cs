namespace EForm.ImportDocument.Domain
{
    public sealed class FlatImportResult
    {
        public string Json { get; set; }
        public string ModelVersion { get; set; }
        public bool Valid { get; set; }
        public int RowCount { get; set; }
    }
}
