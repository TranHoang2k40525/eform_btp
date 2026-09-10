import json
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ai_import.config import settings
from ai_import.hierarchy import DeterministicHierarchyMapper, enrich_indicators
from ai_import.llm import LlmOutputError, validate_llm_mapping
from ai_import.models import HierarchyMapRequest, IndicatorDto, TargetIndicatorDto
from ai_import.prompting import build_hierarchy_messages


class HierarchyMappingTests(unittest.TestCase):
    def setUp(self):
        self.request = HierarchyMapRequest(
            doc_type_code="04a/TP/PBGDPL",
            use_llm=False,
            source_indicators=[
                IndicatorDto(source_ref="s0", code="", label="Tổng số trên địa bàn"),
                IndicatorDto(source_ref="s1", code="I", label="Tại cấp tỉnh"),
                IndicatorDto(source_ref="s2", code="1", label="Cơ quan chuyên môn"),
                IndicatorDto(source_ref="s3", code="1.1", label="Sở Tư pháp"),
                IndicatorDto(source_ref="s4", code="II", label="Tại cấp xã"),
                IndicatorDto(source_ref="s5", code="1", label="Ủy ban nhân dân cấp xã"),
            ],
            target_indicators=[
                TargetIndicatorDto(target_ref="t0", code="", label="Tổng số trên địa bàn"),
                TargetIndicatorDto(target_ref="t1", code="I", label="Tại cấp tỉnh"),
                TargetIndicatorDto(target_ref="t2", code="1", label="Cơ quan chuyên môn"),
                TargetIndicatorDto(target_ref="t3", code="1.1", label="Sở Tư pháp"),
                TargetIndicatorDto(target_ref="t4", code="II", label="Tại cấp xã"),
                TargetIndicatorDto(target_ref="t5", code="1", label="Ủy ban nhân dân cấp xã"),
            ],
        )

    def test_builds_parent_paths_and_resets_number_under_new_section(self):
        rows = enrich_indicators(self.request.source_indicators)
        self.assertEqual([row.level for row in rows], [0, 1, 2, 3, 1, 2])
        self.assertEqual(rows[3].parent_ref, "s2")
        self.assertEqual(rows[5].parent_ref, "s4")
        self.assertIn("Tại cấp xã", rows[5].path)
        self.assertNotIn("Tại cấp tỉnh", rows[5].path)

    def test_maps_repeated_number_by_parent_branch(self):
        result = DeterministicHierarchyMapper(settings).map(self.request)
        selected = {item.source_ref: item.target_ref for item in result.mappings}
        self.assertEqual(selected, {f"s{i}": f"t{i}" for i in range(6)})
        self.assertFalse(result.requires_review)
        json.loads(result.model_dump_json())

    def test_notary_business_label_is_not_a_total_row(self):
        rows = enrich_indicators([
            IndicatorDto(source_ref="s0", code="1", label="Công chứng hợp đồng, giao dịch")
        ])
        self.assertEqual(rows[0].kind, "group")

    def test_prompt_contains_hierarchy_but_not_report_values(self):
        messages = build_hierarchy_messages(self.request)
        prompt = messages[1]["content"]
        self.assertIn('"parent_ref":"s4"', prompt)
        self.assertIn('"path"', prompt)
        self.assertNotIn("sample_values", prompt)

    def test_rejects_unknown_llm_target(self):
        output = {
            "schema_version": "1.0",
            "mappings": [
                {"source_ref": f"s{i}", "target_ref": ("invented" if i == 2 else f"t{i}"), "confidence": 0.99}
                for i in range(6)
            ],
        }
        with self.assertRaises(LlmOutputError):
            validate_llm_mapping(self.request, json.dumps(output))

    def test_rejects_llm_level_confusion(self):
        output = {
            "schema_version": "1.0",
            "mappings": [
                {"source_ref": f"s{i}", "target_ref": f"t{i}", "confidence": 0.99}
                for i in range(6)
            ],
        }
        output["mappings"][2]["target_ref"] = "t3"
        output["mappings"][3]["target_ref"] = "t2"
        with self.assertRaises(LlmOutputError):
            validate_llm_mapping(self.request, "```json\n" + json.dumps(output) + "\n```")


if __name__ == "__main__":
    unittest.main()
