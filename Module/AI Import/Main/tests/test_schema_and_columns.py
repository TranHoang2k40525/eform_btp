import json
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ai_import.config import settings
from ai_import.mapping import HybridFieldMapper
from ai_import.models import MapRequest, TargetFieldDto
from ai_import.schema import parse_target_schema


class SchemaAndColumnMappingTests(unittest.TestCase):
    def test_reads_current_eform_document_contract(self):
        field_keys = ["stt_a!!STT", "chitiet_b!!Chi tiết", "tongso!!Kết quả - Tổng số"]
        form_config = {
            "header": {field_keys[0]: "string", field_keys[1]: "string", field_keys[2]: "int"},
            "data": [],
            "extra": {
                "headerSetting": [["STT", "Chi tiết", "Kết quả"], ["A", "B", "(1)"]],
                "columnSetting": {
                    field_keys[0]: {"Required": False, "Hidden": False},
                    field_keys[1]: {"Required": True, "Hidden": False},
                    field_keys[2]: {"Required": True, "Hidden": False},
                },
            },
        }
        source_rows = [
            {"stt_a": "", "chitiet_b": "Tổng số", "tongso": "=SUM(C2:C3)"},
            {"stt_a": "I", "chitiet_b": "Tại cấp tỉnh", "tongso": 2},
            {"stt_a": "1", "chitiet_b": "Sở Tư pháp", "tongso": 2},
        ]
        payload = {
            "DocTypeCode": "04a/TP/PBGDPL",
            "DocumentContents": [{
                "FormId": "form-id",
                "ContentName": "Kết quả PBGDPL",
                "FormConfig": json.dumps(form_config, ensure_ascii=False),
                "SourceData": json.dumps(source_rows, ensure_ascii=False),
                "DefineConfigJson": json.dumps({"data": [["A"], ["B"], ["(1)"]]}),
            }],
        }
        parsed = parse_target_schema(json.dumps(payload, ensure_ascii=False))
        self.assertEqual([field.column_code for field in parsed.fields], ["A", "B", "(1)"])
        self.assertEqual(parsed.fields[2].data_type, "int")
        self.assertEqual(len(parsed.indicators), 3)
        self.assertEqual(parsed.indicators[0].label, "Tổng số")

    def test_same_leaf_header_is_disambiguated_by_full_path(self):
        fields = [
            TargetFieldDto(
                field_id="issued_total",
                label="Tổng số",
                column_code="(1)",
                header_path=["Văn bản đã ban hành", "Tổng số"],
            ),
            TargetFieldDto(
                field_id="reviewed_total",
                label="Tổng số",
                column_code="(2)",
                header_path=["Văn bản đã thẩm định", "Tổng số"],
            ),
        ]
        result = HybridFieldMapper(settings).map(MapRequest(
            headers=["Tổng số", "Tổng số"],
            header_paths=[["Văn bản đã thẩm định", "Tổng số"], ["Văn bản đã ban hành", "Tổng số"]],
            column_codes=["(2)", "(1)"],
            target_fields=fields,
        ))
        self.assertEqual([item.target_field_id for item in result.mappings], ["reviewed_total", "issued_total"])
        self.assertEqual(len({item.target_field_id for item in result.mappings}), 2)
        json.loads(result.model_dump_json())

    def test_exact_structural_column_code_preserves_current_importer_contract(self):
        result = HybridFieldMapper(settings).map(MapRequest(
            headers=["II. SỐ VĂN BẢN ĐÃ BAN HÀNH"],
            header_paths=[["II. SỐ VĂN BẢN ĐÃ BAN HÀNH"]],
            column_codes=["A"],
            doc_type_code="01d",
            target_fields=[TargetFieldDto(
                field_id="chitiet_a",
                field_name="chitiet_a",
                label="#chitiet - A",
                column_code="A",
                doc_type_code="01d",
            )],
        ))
        self.assertEqual(result.mappings[0].target_field_id, "chitiet_a")
        self.assertEqual(result.mappings[0].decision, "auto")

    def test_declared_target_from_other_doc_type_is_not_mapped_by_code_only(self):
        result = HybridFieldMapper(settings).map(MapRequest(
            headers=["Tổng số"],
            column_codes=["(1)"],
            doc_type_code="04b",
            target_fields=[TargetFieldDto(
                field_id="wrong",
                label="Tổng số",
                column_code="(1)",
                doc_type_code="02b",
            )],
        ))
        self.assertEqual(result.mappings[0].decision, "unmapped")

    def test_chitiet_first_column_does_not_use_numeric_value_column_as_hierarchy_code(self):
        form_config = {
            "header": {
                "chitiet_a!!#chitiet - A": "string",
                "tongso!!Tổng số": "int",
                "loaivanban!!Loại văn bản": "int",
            },
            "extra": {"headerSetting": [["A", "(1)", "(2)"]], "columnSetting": {}},
        }
        rows = [
            {"chitiet_a": "Tổng số văn bản", "tongso": 1, "loaivanban": 1},
            {"chitiet_a": "Trong đó: văn bản cấp xã", "tongso": 0, "loaivanban": 0},
        ]
        payload = {
            "DocTypeCode": "01d",
            "DocumentContents": [{
                "FormConfig": json.dumps(form_config, ensure_ascii=False),
                "SourceData": json.dumps(rows, ensure_ascii=False),
            }],
        }
        parsed = parse_target_schema(json.dumps(payload, ensure_ascii=False))
        self.assertEqual([item.code for item in parsed.indicators], ["", ""])
        self.assertEqual([item.label for item in parsed.indicators], [
            "Tổng số văn bản", "Trong đó: văn bản cấp xã"
        ])


if __name__ == "__main__":
    unittest.main()
