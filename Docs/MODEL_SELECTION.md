# Lựa chọn model

## Quyết định

Không xây hoặc huấn luyện LLM từ đầu. Giải pháp phù hợp là pipeline hybrid:

1. deterministic parser phát hiện sheet/vùng bảng/header;
2. exact/alias/fuzzy cho trường hợp rõ ràng;
3. multilingual embedding để xếp hạng semantic;
4. confidence threshold và human confirmation;
5. validation nghiệp vụ deterministic của eForm;
6. LLM cục bộ chỉ là fallback tùy chọn cho ca mơ hồ, mặc định tắt.

## Model đề xuất

| Vai trò | Model | Lý do | Hạn chế |
|---|---|---|---|
| Mặc định | `intfloat/multilingual-e5-base` | Hỗ trợ tiếng Việt/đa ngôn ngữ, 768 chiều, MIT, đủ nhẹ để thử nghiệm | Tối đa 512 token; phải giữ prefix `query:`/`passage:` |
| Challenger | `BAAI/bge-m3` | 100+ ngôn ngữ, context 8192, dense/sparse/multi-vector, MIT | Nặng và chậm hơn; cần benchmark trên máy triển khai |
| Fallback tùy chọn | `Qwen/Qwen3-8B` | Apache-2.0, đa ngôn ngữ, context dài; có thể self-host | 8B tham số, cần GPU/quantization, khó kiểm soát hơn embedding |
| Không chọn làm chính | `paraphrase-multilingual-mpnet-base-v2` | Dễ dùng, Apache-2.0 | max sequence ngắn (128) và không có lợi thế rõ so với E5 cho bài toán này |

Nguồn model card: [multilingual-e5-base](https://huggingface.co/intfloat/multilingual-e5-base), [BGE-M3](https://huggingface.co/BAAI/bge-m3), [Qwen3-8B](https://huggingface.co/Qwen/Qwen3-8B), [multilingual MPNet](https://huggingface.co/sentence-transformers/paraphrase-multilingual-mpnet-base-v2).

## Vì sao không tự xây LLM

Ba workbook là dữ liệu kiểm thử/khởi tạo, không đủ độ đa dạng để huấn luyện LLM. Train từ đầu cần corpus rất lớn, GPU đắt, MLOps phức tạp và làm tăng rủi ro ghi nhớ dữ liệu nhạy cảm. Bài toán thực tế chủ yếu là retrieval/ranking giữa header nguồn và field đích, nên embedding nhỏ phù hợp hơn về chi phí, latency, khả năng giải thích và rollback.

## Khi nào fine-tune

- Không fine-tune bằng seed 10 mẫu; seed chỉ chứng minh pipeline.
- Bắt đầu thử nghiệm khi có ít nhất 500 cặp header–field đã được xác nhận, phủ nhiều loại biểu mẫu/đơn vị/kỳ.
- Giữ một test set cố định chưa từng train.
- Model mới chỉ được phát hành nếu top-1/top-3/MRR không giảm, test bảo mật/tích hợp qua và có người phê duyệt.

## Threshold mặc định

- `confidence >= 0.88` và margin so với hạng hai `>= 0.08`: có thể đánh dấu auto nhưng vẫn hiển thị preview.
- `0.62 <= confidence < 0.88`: bắt buộc review.
- `< 0.62`: unmapped.

Các ngưỡng phải hiệu chỉnh bằng validation set thật; không xem đây là hằng số nghiệp vụ.

