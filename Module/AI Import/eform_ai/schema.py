from __future__ import annotations

MODEL_NAME = "eform_excel_table_extractor_v2"
MODEL_FILENAME = f"{MODEL_NAME}.eformmodel"
FORMAT_VERSION = "eformmodel-2.0"

CELL_CLASS_NAMES = ("outside", "header_title", "header_code", "value")
CELL_OUTSIDE = 0
CELL_HEADER_TITLE = 1
CELL_HEADER_CODE = 2
CELL_VALUE = 3

COL_ROLE_NAMES = ("outside", "code_col", "label_col", "data_col", "note_col")
COL_OUTSIDE = 0
COL_CODE = 1
COL_LABEL = 2
COL_DATA = 3
COL_NOTE = 4

ROW_TYPE_NAMES = (
    "outside_or_header",
    "grand_total",
    "section",
    "item",
    "subitem",
    "detail",
    "data",
    "empty",
    "unclassified",
)
ROW_OUTSIDE_OR_HEADER = 0
ROW_GRAND_TOTAL = 1
ROW_SECTION = 2
ROW_ITEM = 3
ROW_SUBITEM = 4
ROW_DETAIL = 5
ROW_DATA = 6
ROW_EMPTY = 7
ROW_UNCLASSIFIED = 8

IGNORE_INDEX = -100

STRUCTURAL_CHANNELS = 28
TEXT_HASH_DIM = 32
FEATURE_CHANNELS = STRUCTURAL_CHANNELS + TEXT_HASH_DIM

# Channel indices (kept explicit so augmentations and encoder always stay in sync)
CH_NONEMPTY = 0
CH_TEXT = 1
CH_NUMERIC = 2
CH_NUMERIC_TEXT = 3
CH_FORMULA = 4
CH_TEMPORAL = 5
CH_BOOLEAN = 6
CH_FORMULA_ERROR = 7
CH_BOLD = 8
CH_CENTERED = 9
CH_BORDER = 10
CH_MERGED = 11
CH_MERGE_ANCHOR = 12
CH_MERGE_ROWSPAN = 13
CH_MERGE_COLSPAN = 14
CH_PLACEHOLDER = 15
CH_PAREN_CODE = 16
CH_LETTER_CODE = 17
CH_NEG_INT = 18
CH_CODE_SEQ_ROW = 19
CH_ROMAN_CODE = 20
CH_INT_INDEX = 21
CH_DECIMAL_INDEX = 22
CH_TEXT_LEN = 23
CH_ALPHA_RATIO = 24
CH_UPPER_RATIO = 25
CH_BULLET_START = 26
CH_HAS_COLON = 27
CH_TEXT_HASH_START = STRUCTURAL_CHANNELS
