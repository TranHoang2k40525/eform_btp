# SƠ ĐỒ KIẾN TRÚC VÀ DATA FLOW

## 1. Ranh giới hệ thống

```mermaid
flowchart LR
    U[Người dùng chọn Excel] --> P[Parser đọc cell, merge, style]
    P --> M[EFormExcelStructureExtractor-v1]
    M --> D[Hậu xử lý xác định]
    D --> J[PreviewData JSON]
    J --> H[Handsontable preview]
    H --> C{Người dùng xác nhận?}
    C -->|Không| R[Chọn/sửa lại vùng bảng]
    R --> H
    C -->|Nhập dữ liệu| E[Logic eForm hiện có]
    E --> V[Mapping + validation]
    V --> I[IMPORT_EXCEL_DONE]
    I --> DOC[Document SourceData/ValueData]

    subgraph AI_SCOPE[Phạm vi module AI mới]
        P
        M
        D
        J
    end

    subgraph OLD_SCOPE[Phạm vi giao diện eForm hiện hữu]
        H
        C
        R
        E
        V
        I
        DOC
    end
```

Nguyên tắc ranh giới:

- AI dừng ở `PreviewData JSON`.
- AI không nhận `DocumentContent`.
- AI không chọn DataField.
- AI không ghi hoặc sửa document.
- Giá trị ô được copy từ workbook, không do model sinh.

## 2. Kiến trúc nội bộ module AI

```mermaid
flowchart TB
    F[Workbook .xlsx/.xlsm] --> SEC[Kiểm tra an toàn và giới hạn]
    SEC --> X[Excel reader]
    X --> CELL[Cell matrix + merge + style + formula]
    CELL --> FE[Feature extractor]
    FE --> MODEL[Local multi-task Transformer]
    MODEL --> RR[Row-role probabilities]
    MODEL --> CR[Cell-role probabilities]
    MODEL --> BR[Boundary probabilities]
    RR --> DEC[Constrained decoder]
    CR --> DEC
    BR --> DEC
    DEC --> REG[Table regions]
    REG --> COPY[Copy raw/display/formula từ workbook]
    COPY --> HDR[Rebuild header rows + header paths]
    HDR --> OUT[PreviewData v1.0]
    OUT --> VALID[JSON schema + invariant validation]
```

## 3. Luồng dữ liệu suy luận

```mermaid
sequenceDiagram
    actor User as Người dùng
    participant FE as Trang import
    participant API as Excel Extract API
    participant Parser as Excel parser
    participant Model as Model local
    participant Post as Hậu xử lý
    participant Old as Logic eForm cũ

    User->>FE: Chọn file Excel
    FE->>API: POST /api/excel/extract (file)
    API->>Parser: Đọc workbook
    Parser-->>Model: Cell/row features
    Model-->>Post: Role + boundary probabilities
    Post->>Parser: Lấy lại cell theo tọa độ
    Parser-->>Post: Raw/display value, formula, merge
    Post-->>API: PreviewData JSON
    API-->>FE: Sheets + tables + header + rows + issues
    FE-->>User: Hiển thị Handsontable preview
    User->>FE: Bấm Nhập dữ liệu
    FE->>Old: Preview rows + FormConfig đang có
    Old->>Old: Mapping, required, readonly, sum rules
    Old-->>FE: IMPORT_EXCEL_DONE / lỗi validation
```

Không có lời gọi LLM hoặc API bên ngoài trong sequence này.

## 4. Data flow huấn luyện

```mermaid
flowchart LR
    RAW[1.232 Raw workbooks] --> SCAN[Scan workbook metadata]
    SCAN --> FP[Layout fingerprint]
    FP --> FAMILY[Layout families]
    FAMILY --> SILVER[Rule/parser tạo silver labels]
    SILVER --> REVIEW[Human review theo family]
    REVIEW --> GOLD[Gold structure labels]
    GOLD --> SPLIT[Split theo family]
    SPLIT --> TRAIN[Train 70%]
    SPLIT --> VAL[Validation 15%]
    SPLIT --> TEST[Test 15%]
    TRAIN --> FIT[Train model]
    VAL --> SELECT[Early stop + threshold]
    FIT --> SELECT
    SELECT --> LOCK[Khóa checkpoint]
    LOCK --> EVAL[Đánh giá Test một lần]
    TEST --> EVAL
    EVAL --> EXPORT[ONNX + model card + metrics]
```

## 5. Một workbook thành sample như thế nào?

```mermaid
flowchart TB
    WB[Workbook] --> S1[Sheet 1]
    WB --> S2[Sheet 2]
    S1 --> T1[Table 1]
    S1 --> T2[Table 2]
    T1 --> R1[Row labels]
    T1 --> C1[Cell labels]
    T1 --> B1[Boundary labels]
    T1 --> P1[Expected PreviewData]
    T2 --> R2[Row labels]
    T2 --> P2[Expected PreviewData]
    S2 --> NEG[Blank/cover/note sheet negative sample]
```

Toàn bộ workbook và layout family phải nằm trong cùng một split.

## 6. Trạng thái row-role điển hình

```mermaid
stateDiagram-v2
    [*] --> TITLE
    TITLE --> TITLE
    TITLE --> METADATA
    METADATA --> METADATA
    METADATA --> HEADER
    TITLE --> HEADER
    HEADER --> HEADER
    HEADER --> COLUMN_CODE
    COLUMN_CODE --> DATA
    HEADER --> DATA
    DATA --> DATA
    DATA --> NOTE
    DATA --> FOOTER
    DATA --> TABLE_SEPARATOR
    TABLE_SEPARATOR --> HEADER
    NOTE --> FOOTER
    FOOTER --> FOOTER
    FOOTER --> [*]
```

Decoder không bắt buộc đúng duy nhất chuỗi trên, nhưng dùng nó để loại các chuyển trạng thái vô lý.

## 7. Cách tạo preview và cách nhập document

```mermaid
flowchart LR
    subgraph PREVIEW[Trước nút Nhập dữ liệu]
        A[header_rows] --> H[Handsontable]
        B[merged_cells] --> H
        C[rows dạng array] --> H
        D[raw/display value] --> H
    end

    subgraph IMPORT[Sau nút Nhập dữ liệu]
        H --> MAP[Frontend lấy FormConfig]
        MAP --> COL[So cột/mã/visible fields]
        COL --> OBJ[rows array → object theo DataField ID]
        OBJ --> RULE[Validation eForm]
        RULE --> MSG[IMPORT_EXCEL_DONE]
    end
```

## 8. Fallback khi model không chắc chắn

```mermaid
flowchart TD
    O[Model output] --> Q{Confidence và invariants đạt?}
    Q -->|Có| AUTO[Hiển thị preview tự động]
    Q -->|Không| WARN[Hiển thị cảnh báo]
    WARN --> PICK[Người dùng chọn sheet/table/header/data range]
    PICK --> REBUILD[Code dựng lại PreviewData]
    REBUILD --> AUTO
    PICK --> FEEDBACK[Lưu correction đã kiểm soát]
    FEEDBACK --> NEXT[Dataset phiên bản tiếp theo]
```
