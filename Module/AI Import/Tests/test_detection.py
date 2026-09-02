from ai_import.detection import choose_header_rows, find_row_bands, flatten_headers


def test_detects_row_band_after_title():
    matrix = [["Tiêu đề", None], [None, None], ["Mã", "Tên"], [1, "A"], [2, "B"]]
    assert find_row_bands(matrix) == [(2, 4)]
    start, end, confidence = choose_header_rows(matrix, 2, 4, {2})
    assert (start, end) == (2, 2)
    assert confidence > 0.7


def test_flattens_two_level_headers():
    matrix = [["Thông tin", None, "Giá trị"], ["Mã", "Tên", "Năm 2026"]]
    assert flatten_headers(matrix, 0, 1, 0, 2) == [
        "Thông tin / Mã", "Thông tin / Tên", "Giá trị / Năm 2026"
    ]

