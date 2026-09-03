using System.Collections.Generic;

namespace EForm.ImportDocument.Domain
{
    public sealed class ImportTargetField
    {
        public string FieldId { get; set; }
        public string Label { get; set; }
        public IList<string> Aliases { get; set; } = new List<string>();
        public string DataType { get; set; } = "string";
        public bool Required { get; set; }
        public string Description { get; set; }
    }

    public sealed class ImportRequestContext
    {
        public long DocumentId { get; set; }
        public long UserId { get; set; }
        public long? OrganizationId { get; set; }
        public string TargetSchemaJson { get; set; }
    }
}
