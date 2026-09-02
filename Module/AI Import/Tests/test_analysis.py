from ai_import.config import Settings
from ai_import.excel import WorkbookAnalyzer


def test_analyzer_detects_visible_table(sample_workbook):
    result = WorkbookAnalyzer(Settings()).analyze(str(sample_workbook))
    assert len(result.sheets) == 1
    assert result.sheets[0].name == "Báo cáo"
    assert result.sheets[0].regions
    region = result.sheets[0].regions[0]
    assert "Tên đơn vị" in region.headers
    assert region.data_start_row >= 4


def test_analyzer_can_include_hidden_sheet(sample_workbook):
    result = WorkbookAnalyzer(Settings()).analyze(str(sample_workbook), include_hidden=True)
    assert {sheet.name for sheet in result.sheets} == {"Báo cáo", "Danh mục"}

