using System;
namespace ImportDocument.Domain.Entities
{
    public class ImportRecord
    {
        public int Id { get; set; }
        public string DocumentId { get; set; }
        public string UserId { get; set; }
        public string FileName { get; set; }
        public string JsonData { get; set; }
        public DateTime CreatedAt { get; set; }
    }
}

