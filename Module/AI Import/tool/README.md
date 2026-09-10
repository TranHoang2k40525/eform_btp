# Bộ công cụ AI Import

Thư mục này là bản đóng gói độc lập của phần Python/prompt/dataset. Không có file C# và không yêu cầu sửa mã C# hiện tại.

## Thứ tự chạy

1. Mở `01_BuildDatasetComplete.ipynb` và chạy từ trên xuống.
2. Duyệt `work/Labels/mappings.jsonl`: điền target đúng, đặt `verified=true` và `verification_method` là `human`, `reviewed` hoặc `curated`; dòng không phải dữ liệu đặt `ignore=true`.
3. Chạy lại notebook `01` để sinh `artifacts/dataset/Train/train.jsonl`, `Validation/validation.jsonl`, `Test/test.jsonl` và `Test/ground_truth.jsonl`.
4. Mở `02_TrainModelFromDataset.ipynb`, bật GPU nếu dùng Colab, rồi chạy từ trên xuống để tạo `artifacts/model/EFormExcelMapper-v1`.

Notebook tự tìm `Module/AI Import` từ thư mục làm việc. Chỉ cần đặt `MODULE_ROOT_OVERRIDE` khi notebook được chép ra ngoài repository.

## Nội dung

- `BaoCao_AI_Import.html`: báo cáo đầy đủ và hướng dẫn vận hành.
- `01_BuildDatasetComplete.ipynb`: file duy nhất dùng để tạo dataset hoàn chỉnh.
- `02_TrainModelFromDataset.ipynb`: huấn luyện model trên chính dataset của notebook `01`.
- `runtime/`: API Python, test, requirements và ví dụ request.
- `Prompts/`: prompt hierarchy và JSON Schema đầu ra.
- `docs/`: tài liệu kỹ thuật liên quan.

## Chạy API từ gói tool

Từ PowerShell tại repository:

```powershell
& '.\Module\AI Import\tool\run-api.ps1'
```

API chạy tại `http://127.0.0.1:8010`. Script tự tìm môi trường `.venv` ở các thư mục cha.

## Quy tắc dữ liệu bắt buộc

- Không dùng `candidate_fields` chưa được người duyệt xác nhận để train.
- Chia train/validation/test theo workbook, không chia ngẫu nhiên theo từng cột.
- Test input không chứa đáp án; đáp án nằm riêng trong `ground_truth.jsonl`.
- Không đưa giá trị báo cáo vào target text để tránh học thuộc số liệu.
- Các cấp `Tổng số`, `I`, `1`, `1.1` phải được kiểm tra bằng cả `kind`, `level`, `parent_ref` và `path`.

