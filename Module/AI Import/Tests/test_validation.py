from ai_import.models import MapRequest, MappingCandidateDto, TargetFieldDto, ValidateRequest, ValidationRuleDto
from ai_import.validation import DeterministicValidator


def test_required_type_and_range_validation():
    fields = [
        TargetFieldDto(field_id="name", label="Tên đơn vị", required=True),
        TargetFieldDto(field_id="total", label="Tổng số", required=True, data_type="number"),
    ]
    mappings = [
        MappingCandidateDto(source_column=0, source_header="Tên", target_field_id="name", confidence=1,
                            decision="auto", provenance=["test"]),
        MappingCandidateDto(source_column=1, source_header="Số", target_field_id="total", confidence=1,
                            decision="auto", provenance=["test"]),
    ]
    result = DeterministicValidator().validate(ValidateRequest(
        headers=["Tên", "Số"], rows=[["", "abc"], ["A", -1]], mappings=mappings, target_fields=fields,
        rules=[ValidationRuleDto(rule_id="positive", field_id="total", rule_type="min",
                                 message="Phải không âm", parameters={"value": 0})],
    ))
    assert not result.valid
    assert result.error_count == 3
    assert {issue.code for issue in result.issues} == {"REQUIRED_VALUE", "INVALID_TYPE", "RULE_positive"}

