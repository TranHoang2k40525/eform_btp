# Hướng dẫn huấn luyện và kiểm thử model

## 1. Bạn nên chạy gì?

Không train LLM từ đầu. Trình tự hợp lý:

1. Chạy lexical baseline.
2. Chạy pretrained `multilingual-e5-base` không fine-tune để có mốc semantic.
3. Khi có ít nhất 500 mapping đã xác nhận, fine-tune E5.
4. Chạy `BAAI/bge-m3` như challenger trên cùng test set.
5. Chỉ phát hành model vượt baseline/release gate.

Seed 10 dòng trong repository chỉ dùng kiểm tra pipeline. Script `train_embedding.py` cố ý từ chối dưới 20 mẫu; ngưỡng kỹ thuật này không có nghĩa 20 mẫu đủ production.

## 2. Chuẩn bị môi trường local Windows

Yêu cầu Python 3.11 x64 và Git. GPU NVIDIA là tùy chọn; NVIDIA driver phải tương thích bản PyTorch bạn cài.

```powershell
cd 'C:\Users\hoang\Downloads\eform_btp\Module\AI Import\Train'
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-training.txt
python -c "import torch; print(torch.__version__); print('CUDA:', torch.cuda.is_available())"
```

Nếu PowerShell chặn activate:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\.venv\Scripts\Activate.ps1
```

Nếu chỉ dùng CPU, cài `Main/requirements.txt` để chạy service/baseline; fine-tune sẽ rất chậm. Không cần cài CUDA Toolkit riêng nếu wheel PyTorch phù hợp đã chứa CUDA runtime.

## 3. Chạy trên Google Colab (khuyến nghị cho fine-tune)

1. Zip thư mục `eform_btp` nhưng loại `.vs`, `bin`, `obj`, `.venv`, raw workbook và model binary.
2. Upload zip lên Google Drive cá nhân được phép chứa dữ liệu dự án, hoặc clone repository private.
3. Colab: `Runtime → Change runtime type → T4 GPU`.
4. Mount Drive và vào thư mục Train:

```python
from google.colab import drive
drive.mount('/content/drive')
%cd '/content/drive/MyDrive/eform_btp/Module/AI Import/Train'
!pip install -q -r requirements-training.txt
!nvidia-smi
```

Không upload workbook chứa tài khoản/secret lên Colab. Tốt nhất chỉ upload JSONL header–field đã scrub. Nếu chính sách đơn vị cấm cloud, chạy trên GPU nội bộ.

## 4. Tạo dữ liệu thật

Mỗi dòng JSONL phải có:

```json
{"group_id":"family-01","source":"Tổng số hồ sơ đã xử lý","target_id":"processed_total","target_text":"Tổng hồ sơ đã xử lý; Số hồ sơ giải quyết; processed_total"}
```

Quy trình:

1. Export field ID/label/description/alias từ schema/config eForm.
2. Chỉ trích header workbook; không trích cell value nếu không cần.
3. Người nghiệp vụ xác nhận field đúng.
4. `group_id` theo template family/source file, không dùng tên người.
5. Xóa mọi account/token/password/email/phone.
6. Lưu vào `Data/train/mapping-approved-v1.jsonl`; không commit nếu dữ liệu nội bộ.

Kiểm tra secret thủ công và bằng tìm kiếm:

```powershell
rg -n -i 'password|passwd|api.?key|secret|token|bearer|connectionstring' '..\Data'
```

Review kết quả; chuỗi `target_id` có chữ “token” hợp lệ vẫn cần phân biệt với credential thật.

## 5. Sinh synthetic có kiểm soát (tùy chọn)

```powershell
python generate_synthetic.py `
  --input '..\Data\train\mapping-approved-v1.jsonl' `
  --output '..\Data\synthetic\mapping-synthetic-v1.jsonl' `
  --per-record 3 --seed 42
```

Synthetic chỉ vào train, không vào validation/test. Mở ngẫu nhiên ít nhất 50 mẫu để loại câu vô nghĩa.

## 6. Chia train/validation/test chống leakage

```powershell
python prepare_dataset.py `
  --input '..\Data\train\mapping-approved-v1.jsonl' `
  --input '..\Data\synthetic\mapping-synthetic-v1.jsonl' `
  --output '..\Data\processed\v1' --seed 42
Get-Content '..\Data\processed\v1\manifest.json'
```

Lưu ý: script group-isolated. Với dữ liệu thật, `group_id` phải đại diện template family/source để alias rất giống nhau không rò rỉ giữa các tập. Synthetic cùng group với mẫu gốc để không lọt vào test.

Kiểm tra phân bố bằng notebook `01_data_analysis.ipynb`/`02_data_preprocessing.ipynb`; xác nhận test có đủ field quan trọng, file family và trường hợp khó.

## 7. Đo baseline lexical

Từ thư mục `Train`, thêm `Main` vào module path:

```powershell
$env:PYTHONPATH = (Resolve-Path '..\Main').Path
python evaluate_baseline.py `
  --test '..\Data\processed\v1\test.jsonl' `
  --output '..\Models\baseline-evaluation.json'
```

Lưu top-1, top-3, top-5, MRR. Không thay test set sau khi nhìn kết quả chỉ để tăng metric.

## 8. Đánh giá pretrained E5 trước khi train

`evaluate_model.py` chấp nhận Hugging Face model ID:

```powershell
python evaluate_model.py `
  --model 'intfloat/multilingual-e5-base' `
  --test '..\Data\processed\v1\test.jsonl' `
  --output '..\Models\e5-pretrained-evaluation.json'
```

Lần đầu sẽ tải model. Trong môi trường offline, tải model trên máy được phép rồi trỏ `--model` vào thư mục artifact đã kiểm SHA-256.

## 9. Fine-tune E5

Sửa `config/training.yaml`: seed 42, epoch 3, batch 16, learning rate `2e-5`, max length 256. Sau đó:

```powershell
python train_embedding.py `
  --config '.\config\training.yaml' `
  --train '..\Data\processed\v1\train.jsonl' `
  --validation '..\Data\processed\v1\validation.jsonl' `
  --output '..\Models\mapping-e5-v1'
```

Ghi chú:

- Luôn giữ `query:`/`passage:` cả train và inference.
- Nếu CUDA out-of-memory, giảm batch 16 → 8 → 4; không tăng max length khi header ngắn.
- Nếu loss thành NaN, kiểm tra text rỗng/duplicate, hạ learning rate `1e-5`.
- Với ít dữ liệu, thử 1–3 epoch; epoch cao dễ overfit.
- Script lưu checkpoint và `training-metadata.json`.

## 10. Đánh giá model đã train

```powershell
python evaluate_model.py `
  --model '..\Models\mapping-e5-v1' `
  --test '..\Data\processed\v1\test.jsonl' `
  --output '..\Models\mapping-e5-v1\evaluation.json'

python compare_release.py `
  --baseline '..\Models\baseline-evaluation.json' `
  --candidate '..\Models\mapping-e5-v1\evaluation.json' `
  --min-top1 0.85 --min-top3 0.95
```

Exit code 2 nghĩa là không đạt; không deploy. Ngưỡng 0.85/0.95 là khởi điểm, cần được chủ đề tài/nghiệp vụ phê duyệt theo độ khó dataset.

Ngoài metric tổng, bắt buộc kiểm tra:

- accuracy theo form/template và field;
- false auto-accept (sai nhưng confidence >= 0.88);
- coverage/unmapped rate;
- confusion pairs như tổng/nữ/đã xử lý;
- latency CPU và memory;
- ít nhất 50 lỗi được đọc thủ công.

## 11. Benchmark BGE-M3

Không fine-tune ngay. Trước hết đánh giá pretrained trên đúng test set:

```powershell
python evaluate_model.py `
  --model 'BAAI/bge-m3' `
  --test '..\Data\processed\v1\test.jsonl' `
  --output '..\Models\bge-m3-pretrained-evaluation.json'
```

So sánh accuracy, p95 latency và RAM/VRAM. Chỉ chọn BGE-M3 nếu cải thiện đủ lớn để bù chi phí. Vì runtime mapper hiện dùng contract E5 prefix, trước production cần contract test model-specific và hiệu chỉnh semantic score.

## 12. Bật model trong service

Tạo env vars ở terminal test:

```powershell
$env:AI_IMPORT_EMBEDDING_ENABLED = 'true'
$env:AI_IMPORT_EMBEDDING_MODEL = (Resolve-Path '..\Models\mapping-e5-v1').Path
$env:AI_IMPORT_MODEL_CACHE = (Resolve-Path '..\Models').Path
cd '..\Main'
python -m uvicorn ai_import.api:app --host 127.0.0.1 --port 8010
```

Terminal khác:

```powershell
Invoke-RestMethod 'http://127.0.0.1:8010/health'
Invoke-RestMethod 'http://127.0.0.1:8010/model/version'
```

Test mapping:

```powershell
$body = @{
  headers = @('Tên cơ quan', 'Tổng cộng')
  sample_rows = @(@('Đơn vị A', 12))
  target_fields = @(
    @{ field_id='organization_name'; label='Tên đơn vị'; aliases=@('Tên cơ quan'); data_type='string'; required=$true },
    @{ field_id='total'; label='Tổng số'; aliases=@('Tổng cộng'); data_type='number'; required=$true }
  )
} | ConvertTo-Json -Depth 6
Invoke-RestMethod 'http://127.0.0.1:8010/map' -Method Post -ContentType 'application/json' -Body $body
```

## 13. Chạy test phần mềm

### Python

Từ `Main`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r '..\Tests\requirements-test.txt'
$env:PYTHONPATH = (Get-Location).Path
python -m pytest '..\Tests' -q --cov=ai_import --cov-report=term-missing
```

### Analyzer với workbook được phép dùng

```powershell
python -m ai_import.cli 'D:\du-lieu-test\workbook.xlsx' --preview-rows 10
python benchmark.py --rows 100 1000 10000 --sheets 1 --output benchmark-result.json
python benchmark.py --rows 1000 --sheets 10 --output benchmark-multisheet.json
```

Không commit JSON preview nếu chứa cell value nhạy cảm.

### .NET

Từ root dự án:

```powershell
dotnet build '.\Module\Module.ImportDocument\Tests\Module.ImportDocument.Tests.csproj' -c Release
& '.\Module\Module.ImportDocument\Tests\bin\Release\net48\Module.ImportDocument.Tests.exe'
```

## 14. Test tích hợp/UAT

Tạo database staging và tài khoản test:

1. User có quyền + kỳ mở: full flow phải commit đúng.
2. User không quyền: upload/get/commit bị từ chối.
3. Kỳ khóa sau confirm: commit vẫn bị từ chối vì kiểm tra lại.
4. File giả extension, quá dung lượng, zip bomb: bị chặn trước analyze.
5. Multi-sheet/merged header/formula: preview đúng; formula không được thực thi.
6. Mapping mơ hồ: decision review, không auto.
7. Validation error: không confirm/commit.
8. Commit lặp lại: cùng reference, không nhân đôi dữ liệu.
9. AI service down/timeout: job failed/retry, không có partial commit.
10. User A không đọc job của User B.

Đối chiếu `DocumentContent.SourceData`, `ValueData`, `FormConfig`, `FormStyle` trước/sau trong một transaction và chạy rule hiện hữu sau import.

## 15. Incremental training

Chỉ export feedback đã duyệt:

```powershell
python incremental_training.py `
  --approved-feedback '..\Data\processed\approved-feedback.jsonl' `
  --existing '..\Data\processed\v1\train.jsonl' `
  --merged '..\Data\processed\incremental-train.jsonl' `
  --minimum-new 100
```

Sau đó tạo dataset version mới, train `mapping-e5-v2`, đánh giá trên test cố định, chạy release gate, test tích hợp và phê duyệt. Không overwrite v1. Rollback bằng đổi `AI_IMPORT_EMBEDDING_MODEL` về artifact v1 rồi restart service.

## 16. Minh chứng cần nộp

- ảnh chụp/console log cài đặt và GPU (không lộ path/user/secret);
- dataset manifest, không nộp raw nhạy cảm;
- training metadata và loss log;
- baseline/pretrained/fine-tuned metric JSON;
- benchmark 100/1.000/10.000 dòng;
- kết quả Python/.NET test;
- 5–10 ví dụ đúng, sai, mơ hồ kèm giải thích confidence;
- version/hash artifact và quyết định release/không release.

