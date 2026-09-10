namespace EForm.ImportDocument.Domain.Entities
{
    public class FlatImportResult
    {
        public string FileName { get; set; }
        public string SheetName { get; set; }
        public string DocTypeCode { get; set; }
        public int RowCount { get; set; }
        public object Data { get; set; }
        public string UserId { get; set; }
        public string DocumentId { get; set; }
        public System.DateTime CreatedAt { get; set; }
    }
}
