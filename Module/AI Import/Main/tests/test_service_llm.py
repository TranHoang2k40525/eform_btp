import unittest
from dataclasses import replace

from ai_import.config import settings
from ai_import.models import (
    HierarchyMapRequest,
    IndicatorDto,
    LlmHierarchyMappingDto,
    LlmHierarchyResponse,
    MappingDecision,
    TargetIndicatorDto,
)
from ai_import.service import ImportAiService


class _FakeLlm:
    def __init__(self, mappings):
        self._response = LlmHierarchyResponse(schema_version="1.0", mappings=mappings)

    def map_hierarchy(self, _request):
        return self._response


class LlmMergePolicyTests(unittest.TestCase):
    def test_llm_confirmation_cannot_promote_ambiguous_baseline(self):
        request = HierarchyMapRequest(
            doc_type_code="04c/TP/PBGDPL",
            source_indicators=[
                IndicatorDto(source_ref="s0", code="", label="Tổng số"),
                IndicatorDto(source_ref="s1", code="", label="664"),
                IndicatorDto(source_ref="s2", code="", label="66464"),
            ],
            target_indicators=[
                TargetIndicatorDto(target_ref="t0", code="", label="Tổng số"),
                TargetIndicatorDto(target_ref="t1", code="", label="664"),
                TargetIndicatorDto(target_ref="t2", code="", label="66464"),
            ],
        )
        service = ImportAiService(replace(settings, llm_enabled=True))
        service.llm = _FakeLlm([
            LlmHierarchyMappingDto(source_ref=f"s{i}", target_ref=f"t{i}", confidence=0.99)
            for i in range(3)
        ])

        result = service.map_hierarchy(request)
        by_source = {item.source_ref: item for item in result.mappings}
        self.assertEqual(by_source["s0"].decision, MappingDecision.auto)
        self.assertEqual(by_source["s1"].decision, MappingDecision.review)
        self.assertIn("BASELINE_REVIEW_PRESERVED", by_source["s1"].reason_codes)
        self.assertIn("SUSPECTED_SHIFTED_VALUE", by_source["s1"].reason_codes)

    def test_llm_null_does_not_silently_discard_an_auto_mapping(self):
        request = HierarchyMapRequest(
            doc_type_code="04c/TP/PBGDPL",
            source_indicators=[IndicatorDto(source_ref="s0", code="", label="Tổng số")],
            target_indicators=[TargetIndicatorDto(target_ref="t0", code="", label="Tổng số")],
        )
        service = ImportAiService(replace(settings, llm_enabled=True))
        service.llm = _FakeLlm([
            LlmHierarchyMappingDto(source_ref="s0", target_ref=None, confidence=0.4)
        ])

        result = service.map_hierarchy(request)
        self.assertEqual(result.mappings[0].target_ref, "t0")
        self.assertEqual(result.mappings[0].decision, MappingDecision.review)
        self.assertTrue(result.requires_review)
        self.assertEqual(result.issues[-1].code, "LLM_BASELINE_DISAGREEMENT")


if __name__ == "__main__":
    unittest.main()
