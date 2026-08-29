# Công cụ soạn Ngân hàng câu hỏi (NHCH) MCQ theo năng lực từ tình huống lâm sàng

Công cụ này nhận **1 tình huống lâm sàng thô** (tiền sử, bệnh sử, lâm sàng,
cận lâm sàng, xử trí...) và soạn ra **10 câu hỏi trắc nghiệm (MCQ)** bao
phủ: chẩn đoán, cận lâm sàng cần chỉ định, đọc/diễn giải kết quả cận lâm
sàng, điều trị, tiên lượng, dự phòng, bệnh sử/khám, quản lý ca và giao
tiếp — theo đúng quy trình và bảng kiểm chất lượng trong tài liệu
*"Các bước soạn NHCH theo năng lực"* và đúng cấu trúc câu hỏi mẫu
*"Sheet 1, dòng 2"* mà bộ môn đã cung cấp.

## Hai cách dùng

Việc "soạn câu hỏi" cần một LLM; việc "kiểm tra kỹ thuật + xuất file Word"
thì không. Công cụ tách riêng hai việc này, nên bạn có thể chọn:

### Cách 1 — KHÔNG CẦN API key (dùng chính Claude.ai/Claude app bạn đang có)

```bash
pip install python-docx   # chỉ cần thư viện này, KHÔNG cần "anthropic"

# Bước 1: tạo file prompt
python cli.py prepare --input examples/sample_scenario.txt --prompt-output prompt.txt

# Bước 2: mở prompt.txt, copy toàn bộ nội dung, dán vào MỘT CUỘC TRÒ
# CHUYỆN MỚI trên Claude.ai hoặc Claude app. Claude sẽ trả lời bằng một
# khối JSON. Copy toàn bộ JSON đó (chỉ phần JSON, bỏ phần chữ thừa nếu
# có) và lưu vào 1 file, ví dụ answer.json

# Bước 3: kiểm tra kỹ thuật + xuất Word — chạy hoàn toàn bằng Python,
# không gọi mạng, không cần API key
python cli.py build --json-input answer.json --output output/bo_cau_hoi.docx \
    --scenario-file examples/sample_scenario.txt \
    --title "Thai trong tử cung giai đoạn sớm chưa xác định khả năng sống"
```

Nếu Claude.ai trả JSON kèm rào ```` ```json ... ``` ````, chỉ cần xoá 2
dòng rào đó trước khi lưu file — `build` cần đúng một mảng JSON thuần.

### Cách 2 — Tự động hoàn toàn, CẦN ANTHROPIC_API_KEY

Dùng khi bạn muốn tích hợp vào quy trình tự động (ví dụ chạy hàng loạt
nhiều ca), không cần dán tay qua lại.

```bash
pip install -r requirements.txt   # cài thêm "anthropic"
export ANTHROPIC_API_KEY=sk-ant-...   # lấy tại console.anthropic.com/settings/keys

python cli.py generate --input examples/sample_scenario.txt \
    --output output/bo_cau_hoi.docx --json-output output/bo_cau_hoi.json
```

## Công cụ làm gì

1. **Sinh câu hỏi** (bằng Claude, qua Cách 1 hoặc Cách 2) — dùng một
   prompt đã mã hoá sẵn toàn bộ khung 04 miền năng lực / 11 năng lực, 3
   mức độ tư duy (Vận dụng, Phân tích, Đánh giá) và bảng kiểm 12 tiêu
   chí trước khi duyệt câu hỏi.
2. **Tự kiểm tra kỹ thuật hai lớp**:
   - Lớp 1: model tự chấm từng câu theo đúng 12 tiêu chí trong bảng kiểm.
   - Lớp 2: một validator độc lập (`validator.py`, **không dùng AI, không
     cần mạng**) rà lại bằng heuristic khách quan — độ dài lựa chọn có
     cân đối không, có dùng từ tuyệt đối ("luôn luôn", "tất cả", "duy
     nhất"...) không, có dùng bẫy hội tụ ("tất cả các đáp án trên đều
     đúng") không, có lựa chọn trùng nhau không, thiếu trường bắt buộc
     không.
3. **Xuất file Word (.docx)** đúng bố cục mẫu: Câu N → mã năng lực/mức độ
   tư duy → Phần thân → Câu hỏi dẫn → 4 lựa chọn A–D → Đáp án → Giải
   thích → Kiểm tra kỹ thuật, kèm bảng tóm tắt cấu trúc năng lực ở cuối.

**Lưu ý quan trọng:** công cụ này là **trợ lý soạn thảo**, không thay thế
việc giảng viên đọc và duyệt lại từng câu. Bảng kiểm tự động chỉ bắt được
các lỗi kỹ thuật máy móc — tính chính xác y khoa và mức độ phù hợp lâm
sàng vẫn cần người có chuyên môn thẩm định trước khi đưa vào ngân hàng
câu hỏi chính thức.

## Cài đặt

```bash
git clone <repo-url-của-bạn>
cd clinical-mcq-generator
python3 -m venv .venv && source .venv/bin/activate
pip install python-docx          # đủ dùng cho Cách 1 (không cần API key)
# pip install -r requirements.txt  # nếu muốn dùng thêm Cách 2 (cần "anthropic")
```

## Sử dụng như thư viện Python (không cần API key)

```python
from mcq_generator import build_manual_prompt, validate_all, export_to_docx
import json

raw_scenario = "..."  # tình huống lâm sàng thô của bạn

# 1. Tạo prompt, tự dán vào Claude.ai, copy JSON trả về
prompt = build_manual_prompt(raw_scenario)

# 2. Sau khi có JSON (ví dụ đọc từ file bạn đã lưu):
questions = json.loads(open("answer.json", encoding="utf-8").read())

# 3. Kiểm tra + xuất file — không cần AI ở bước này
results = validate_all(questions)
export_to_docx(questions, "output/bo_cau_hoi.docx",
                raw_scenario=raw_scenario,
                validation_results=results)
```

## Tuỳ chỉnh bộ khung 10 câu (blueprint)

M��c định, 10 câu được phân bổ theo `DEFAULT_BLUEPRINT` trong
`src/mcq_generator/competency_framework.py`:

| # | Mã năng lực | Nội dung | Mức độ tư duy |
|---|---|---|---|
| 1 | B.3 | Bệnh sử/tiền sử/thăm khám | Vận dụng |
| 2 | A.1 | Khái niệm y học cơ bản áp dụng vào ca | Vận dụng |
| 3 | B.4 | Cận lâm sàng cần chỉ định tiếp theo | Phân tích |
| 4 | B.4 | Đọc/diễn giải kết quả cận lâm sàng | Phân tích |
| 5 | B.5 | Chẩn đoán | Đánh giá |
| 6 | B.6 | Tiên lượng/kết cục | Đánh giá |
| 7 | C.7 | Dự phòng/duy trì sức khỏe | Đánh giá |
| 8 | C.8 | Điều trị bằng thuốc | Đánh giá |
| 9 | C.9 | Can thiệp lâm sàng | Đánh giá |
| 10 | D.11 | Giao tiếp và tính chuyên nghiệp | Đánh giá |

Muốn đổi tỉ lệ (ví dụ muốn 2 câu điều trị, bỏ câu giao tiếp), truyền
`blueprint=` riêng:

```python
from mcq_generator import build_manual_prompt, ThinkingLevel

blueprint = [
    ("B.3", ThinkingLevel.APPLY),
    ("B.4", ThinkingLevel.ANALYZE),
    ("B.5", ThinkingLevel.EVALUATE),
    ("C.8", ThinkingLevel.EVALUATE),
    ("C.8", ThinkingLevel.EVALUATE),  # 2 câu điều trị
    # ... đủ số câu bạn muốn
]
prompt = build_manual_prompt(raw_scenario, blueprint=blueprint)
```

Toàn bộ 11 năng lực và mô tả gợi ý cho từng năng lực nằm trong
`COMPETENCIES` (cùng file), có thể sửa trực tiếp nếu bộ môn cập nhật
khung năng lực.

## Cấu trúc project

```
clinical-mcq-generator/
├── cli.py                          # công cụ dòng lệnh: prepare / build / generate
├── requirements.txt                 # chỉ cần cho lệnh "generate" (Cách 2)
├── .env.example
├── examples/
│   └── sample_scenario.txt         # tình huống mẫu để test nhanh
├── src/mcq_generator/
│   ├── competency_framework.py     # khung 4 miền/11 năng lực, bảng kiểm 12 tiêu chí
│   ├── prompts.py                  # build prompt hệ thống + prompt người dùng
│   ├── manual_mode.py              # ghép prompt để dán thủ công (Cách 1, không cần API key)
│   ├── generator.py                # gọi Anthropic API (Cách 2, cần API key)
│   ├── validator.py                # kiểm tra kỹ thuật tự động (không cần AI)
│   └── docx_export.py              # xuất file Word đúng mẫu
└── tests/
    └── test_pipeline_offline.py    # test validator + docx export, KHÔNG gọi API thật
```

## Chạy test (không tốn API call, không cần API key)

```bash
python tests/test_pipeline_offline.py
```

## Việc cần làm tiếp theo (gợi ý)

- Thêm giao diện web đơn giản (Streamlit/Gradio) cho lệnh `build`, để
  không cần dùng dòng lệnh.
- Thêm chế độ xuất trực tiếp sang định dạng import của phần mềm thi trắc
  nghiệm bộ môn đang dùng (ví dụ Moodle GIFT/Aiken, hoặc file Excel).
- Ghi log các ca đã soạn + phiên bản blueprint dùng, để truy vết khi có
  chỉnh sửa về sau.
