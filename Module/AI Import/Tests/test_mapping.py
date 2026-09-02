from ai_import.config import Settings
from ai_import.mapping import HybridFieldMapper
from ai_import.models import MapRequest, TargetFieldDto


def test_exact_alias_mapping_is_auto():
    mapper = HybridFieldMapper(Settings(embedding_enabled=False))
    response = mapper.map(MapRequest(
        headers=["Tên đơn vị", "Tổng số"],
        target_fields=[
            TargetFieldDto(field_id="organization_name", label="Tên cơ quan", aliases=["Tên đơn vị"]),
            TargetFieldDto(field_id="total", label="Số lượng", aliases=["Tổng số"], data_type="number"),
        ],
    ))
    assert [item.target_field_id for item in response.mappings] == ["organization_name", "total"]
    assert all(item.decision == "auto" for item in response.mappings)
    assert all("exact-or-alias" in item.provenance for item in response.mappings)


def test_unknown_header_requires_review_or_unmapped():
    mapper = HybridFieldMapper(Settings(embedding_enabled=False))
    response = mapper.map(MapRequest(headers=["xyz hoàn toàn lạ"], target_fields=[
        TargetFieldDto(field_id="total", label="Số lượng")
    ]))
    assert response.mappings[0].decision != "auto"

