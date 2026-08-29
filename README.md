# Công cụ soạn Ngân hàng câu hỏi (NHCH) MCQ theo năng lực từ tình huống lâm sàng

Nhận **1 tình huống lâm sàng thô** → soạn ra **10 câu hỏi trắc nghiệm (MCQ)**
bao phủ: chẩn đoán, cận lâm sàng cần chỉ định, đọc/diễn giải kết quả cận
lâm sàng, điều trị, tiên lượng, dự phòng, bệnh sử/khám, quản lý ca và
giao tiếp — theo đúng quy trình và bảng kiểm chất lượng trong tài liệu
*"Các bước soạn NHCH theo năng lực"* và đúng cấu trúc câu hỏi mẫu
*"Sheet 1, dòng 2"*.

## Cách dùng nhanh nhất: Ứng dụng giao diện (khuyên dùng)

Mở app dạng cửa sổ trên máy tính — dán tình huống, bấm 1 nút, ra file Word.
**Mặc định dùng Google Gemini** (có mức miễn phí rộng rãi); có thể đổi
sang Anthropic Claude ngay trong app nếu muốn.

**Cài đặt (chỉ làm 1 lần):**

```bash
# 1. Cài Python từ python.org nếu máy chưa có (Windows/Mac đã có sẵn tkinter)
#    Trên Ubuntu/Linux cần thêm: sudo apt install python3-tk

# 2. Cài thư viện cần thiết (mặc định dùng Gemini)
pip install google-genai python-docx
```

**Chạy app:**

- Windows: double-click `run_windows.bat`
- Mac: double-click `run_mac.command` (lần đầu có thể cần chuột phải > Open)
- Linux / dòng lệnh: `python3 gui_app.py`

**Lần đầu mở app** sẽ hỏi **Gemini API key** — lấy miễn phí tại
https://aistudio.google.com/apikey (đăng nhập bằng tài khoản Google, bấm
"Create API key"). Key được lưu lại trên máy bạn (tại
`~/.clinical_mcq_generator/config.json`), **chỉ cần nhập 1 lần**, các lần
sau mở app dùng lại luôn.

App có nút chọn nhà cung cấp AI ở đầu cửa sổ — mặc định **Google Gemini**,
có thể đổi sang **Anthropic Claude** nếu muốn (khi đó cần cài thêm
`pip install anthropic` và nhập Anthropic API key riêng, lưu tách biệt
với key Gemini).

**Bảo mật API key:** không chia sẻ key hoặc ảnh chụp màn hình có key cho
ai. Nếu lỡ để lộ key (kể cả dán vào đây để hỏi trợ lý AI), hãy vào trang
tạo key và **xoá/thu hồi key đó, tạo key mới** ngay lập tức.

**Chi phí:** Gemini có mức miễn phí (free tier) khá rộng rãi cho lượng
dùng cá nhân/thử nghiệm hằng ngày; nếu vượt mức miễn phí, chi phí mỗi
lần tạo 10 câu hỏi vẫn ở mức rất nhỏ. Đây là phí Google tính trực tiếp
theo tài khoản của bạn, không phải phí của công cụ này.

**Sử dụng:**
1. Chọn nhà cung cấp AI (mặc định Gemini đã chọn sẵn).
2. Dán tình huống lâm sàng thô vào ô văn bản lớn.
3. (Tuỳ chọn) sửa tiêu đề ca bệnh sẽ hiện trong file Word.
4. Bấm **"Tạo bộ 10 câu hỏi"** — chờ vài chục giây.
5. App tự mở hộp thoại chọn nơi lưu, xuất file `.docx` đúng format mẫu.
6. Danh sách cảnh báo kỹ thuật tự động (nếu có) hiện ngay trong app.

Vào menu **Cài đặt** trong app để đổi hoặc xoá API key bất cứ lúc nào.

## Cách khác: KHÔNG cần API key (dán thủ công qua Claude.ai/Gemini/ChatGPT...)

Nếu bạn không muốn tạo API key, vẫn dùng được công cụ qua dòng lệnh,
đổi lại phải tự copy/paste qua lại với 1 chatbot bất kỳ một lần cho mỗi ca:

```bash
pip install python-docx   # không cần cài "google-genai" hay "anthropic"

# Bước 1: tạo file prompt
python cli.py prepare --input examples/sample_scenario.txt --prompt-output prompt.txt

# Bước 2: dán toàn bộ nội dung prompt.txt vào 1 cuộc trò chuyện MỚI trên
# Gemini/Claude.ai/ChatGPT... Copy khối JSON trả về, lưu vào answer.json

# Bước 3: kiểm tra kỹ thuật + xuất Word — chạy offline, không cần API key
python cli.py build --json-input answer.json --output output/bo_cau_hoi.docx \
    --scenario-file examples/sample_scenario.txt
```

## Cách khác nữa: dòng lệnh tự động hoàn toàn (cũng cần API key)

```bash
pip install -r requirements.txt

# Dùng Gemini (mặc định)
export GEMINI_API_KEY=AIza...
python cli.py generate --input examples/sample_scenario.txt --output output/bo_cau_hoi.docx

# Hoặc dùng Anthropic
export ANTHROPIC_API_KEY=sk-ant-...
python cli.py generate --provider anthropic --input examples/sample_scenario.txt --output output/bo_cau_hoi.docx
```

Dùng cách này khi muốn chạy hàng loạt nhiều ca cùng lúc (script hoá),
thay vì mở app từng ca một.

## Công cụ làm gì bên trong

1. **Sinh câu hỏi** — prompt gửi cho model đã mã hoá sẵn khung 04 miền
   năng lực / 11 năng lực, 3 mức độ tư duy (Vận dụng, Phân tích, Đánh
   giá) và bảng kiểm 12 tiêu chí trước khi duyệt câu hỏi. Prompt giống
   hệt nhau dù dùng Gemini hay Anthropic — chỉ khác nơi gọi API
   (`src/mcq_generator/providers.py`).
2. **Kiểm tra kỹ thuật hai lớp**:
   - Model tự chấm từng câu theo đúng 12 tiêu chí trong bảng kiểm.
   - Một validator độc lập, **không dùng AI**, rà lại bằng heuristic
     khách quan: độ dài lựa chọn có cân đối không, có từ tuyệt đối
     ("luôn luôn", "tất cả", "duy nhất"...), có bẫy hội tụ ("tất cả các
     đáp án trên đều đúng"), lựa chọn trùng nhau, thiếu trường bắt buộc.
3. **Xuất file Word (.docx)** đúng bố cục mẫu: Câu N → mã năng lực/mức độ
   tư duy → Phần thân → Câu hỏi dẫn → 4 lựa chọn A–D → Đáp án → Giải
   thích → Kiểm tra kỹ thuật, kèm bảng tóm tắt cấu trúc năng lực ở cuối.

**Lưu ý quan trọng:** đây là **trợ lý soạn thảo**, không thay thế việc
giảng viên đọc và duyệt lại từng câu. Bảng kiểm tự động chỉ bắt lỗi kỹ
thuật máy móc — tính chính xác y khoa và mức độ phù hợp lâm sàng vẫn cần
người có chuyên môn thẩm định trước khi đưa vào ngân hàng câu hỏi chính
thức.

## Tuỳ chỉnh bộ khung 10 câu (blueprint)

Mặc định, 10 câu được phân bổ theo `DEFAULT_BLUEPRINT` trong
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

Sửa trực tiếp `DEFAULT_BLUEPRINT` (hoặc `COMPETENCIES`) trong file đó
nếu muốn đổi tỉ lệ hoặc bộ môn cập nhật khung năng lực.

## Cấu trúc project

```
clinical-mcq-generator/
├── gui_app.py                       # ỨNG DỤNG GIAO DIỆN (khuyên dùng, mặc định Gemini)
├── run_windows.bat / run_mac.command  # file double-click để mở app
├── cli.py                           # công cụ dòng lệnh: prepare / build / generate
├── requirements.txt
├── .env.example
├── examples/
│   └── sample_scenario.txt
├── src/mcq_generator/
│   ├── competency_framework.py     # khung 4 miền/11 năng lực, bảng kiểm 12 tiêu chí
│   ├── prompts.py                  # build prompt hệ thống + prompt người dùng
│   ├── manual_mode.py              # ghép prompt để dán thủ công (không cần API key)
│   ├── providers.py                # gọi Gemini hoặc Anthropic — đổi provider chỉ sửa ở đây
│   ├── generator.py                # orchestration: build prompt → gọi provider → parse JSON
│   ├── config.py                   # lưu/đọc API key cục bộ theo từng provider
│   ├── validator.py                # kiểm tra kỹ thuật tự động (không cần AI)
│   └── docx_export.py              # xuất file Word đúng mẫu
└── tests/
    └── test_pipeline_offline.py    # test validator + docx export, KHÔNG gọi API thật
```

## Chạy test (không tốn API call)

```bash
python tests/test_pipeline_offline.py
```

## Việc cần làm tiếp theo (gợi ý)

- Đóng gói app thành file .exe/.app độc lập bằng PyInstaller, để người
  dùng không cần cài Python (`pip install pyinstaller` rồi
  `pyinstaller --onefile --windowed gui_app.py`).
- Thêm chế độ xuất trực tiếp sang định dạng Moodle GIFT/Aiken hoặc Excel.
- Ghi log các ca đã soạn để truy vết khi có chỉnh sửa về sau.
