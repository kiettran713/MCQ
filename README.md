# Công cụ soạn Ngân hàng câu hỏi (NHCH) MCQ theo năng lực từ tình huống lâm sàng

Nhận **1 tình huống lâm sàng thô** → soạn ra **10 câu hỏi trắc nghiệm (MCQ)**
bao phủ: chẩn đoán, cận lâm sàng cần chỉ định, đọc/diễn giải kết quả cận
lâm sàng, điều trị, tiên lượng, dự phòng, bệnh sử/khám, quản lý ca và
giao tiếp — theo đúng quy trình và bảng kiểm chất lượng trong tài liệu
*"Các bước soạn NHCH theo năng lực"* và đúng cấu trúc câu hỏi mẫu
*"Sheet 1, dòng 2"*.

## Cách dùng nhanh nhất: Ứng dụng giao diện (khuyên dùng)

Mở app dạng cửa sổ trên máy tính — chọn nguồn tình huống và cách lấy câu
hỏi, bấm nút, ra file Word.

App có 2 **cách lấy câu hỏi**, chọn ở đầu cửa sổ:

1. **"Tự động qua API"** — mặc định dùng Google Gemini (có mức miễn phí
   rộng rãi); có thể đổi sang Anthropic Claude, OpenAI, OpenRouter,
   Cerebras hoặc Groq ngay trong app.
2. **"Thủ công (dán vào Claude.ai / Gemini / ChatGPT)"** — dùng khi bạn
   muốn dùng **tài khoản thường** (Claude Pro, Gemini, ChatGPT...) thay
   vì API key. App tự tạo sẵn prompt, bạn dán vào cửa sổ chat bạn đang
   có, rồi dán kết quả AI trả về ngược lại vào app — app tự kiểm tra kỹ
   thuật và xuất file Word, không cần rời khỏi cửa sổ app.

   **Lưu ý:** đây là cách hợp lệ duy nhất để dùng "tài khoản" thay vì
   API — app không thể tự động đăng nhập hộ bạn vào Claude.ai/Gemini để
   gửi tin nhắn thay bạn, vì các trang chat đó không hỗ trợ việc này
   cho ứng dụng bên ngoài (và làm chui qua phiên đăng nhập web sẽ vi
   phạm điều khoản dịch vụ của họ, có thể bị khoá tài khoản).

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
có thể đổi sang **Anthropic Claude**, **OpenAI (ChatGPT)**, **OpenRouter**,
**Cerebras**, **Groq**, **Mistral AI** hoặc **GitHub Models** nếu muốn. Mỗi nhà cung cấp cần cài thêm thư viện tương
ứng và có API key riêng, lưu tách biệt với nhau trên máy bạn:

| Nhà cung cấp | Cài thêm | Lấy API key tại | Miễn phí? |
|---|---|---|---|
| Google Gemini (mặc định) | `pip install google-genai` | https://aistudio.google.com/apikey | Có (model Flash) |
| Anthropic Claude | `pip install anthropic` | https://console.anthropic.com/settings/keys | Có credit dùng thử |
| OpenAI (ChatGPT) | `pip install openai` | https://platform.openai.com/api-keys | Không, phải nạp tiền trước |
| OpenRouter | `pip install openai` (dùng chung SDK) | https://openrouter.ai/keys | **Có** — model mặc định `openrouter/free` luôn miễn phí |
| Cerebras | `pip install openai` (dùng chung SDK) | https://cloud.cerebras.ai/ | Tuỳ tài khoản — có thể yêu cầu bật thanh toán mới dùng được model |
| Groq | `pip install openai` (dùng chung SDK) | https://console.groq.com/keys | **Có** — hạn mức miễn phí hào phóng, không cần thẻ, tốc độ rất nhanh |
| Mistral AI | `pip install openai` (dùng chung SDK) | https://console.mistral.ai/api-keys | **Có** — free tier rộng rãi (khoảng 1 tỷ token/tháng), không cần thẻ |
| GitHub Models | `pip install openai` (dùng chung SDK) | https://github.com/settings/tokens (tạo Personal Access Token) | **Có** — dùng ngay tài khoản GitHub có sẵn, không cần thẻ |

**Nếu các nhà cung cấp khác gặp trục trặc (hết quota, bị chặn, hết
tiền...), Groq và OpenRouter là 2 lựa chọn dự phòng đáng tin cậy nhất**
— cả hai đều miễn phí và không cần thẻ ngân hàng:
- **Groq**: ổn định, hạn mức miễn phí hào phóng, tốc độ rất nhanh.
- **OpenRouter**: model mặc định `openrouter/free` là một "router" tự
  động chọn 1 trong nhiều model miễn phí đang có sẵn, nên không lo bị
  gỡ tên model như các model free lẻ khác.

**Bảo mật API key:** không chia sẻ key hoặc ảnh chụp màn hình có key cho
ai. Nếu lỡ để lộ key (kể cả dán vào đây để hỏi trợ lý AI), hãy vào trang
tạo key và **xoá/thu hồi key đó, tạo key mới** ngay lập tức.

**Chi phí và giới hạn miễn phí (free tier):** mặc định app dùng
`gemini-3.6-flash`, model có hạn mức dùng miễn phí khá rộng rãi (không
cần thẻ thanh toán). Các model dòng **Pro** (`gemini-2.5-pro`,
`gemini-3.1-pro-preview`) chất lượng cao hơn nhưng hạn mức miễn phí rất
thấp hoặc bằng 0 — nếu dùng sẽ báo lỗi `429 RESOURCE_EXHAUSTED` trừ khi
tài khoản Google của bạn đã bật thanh toán (billing) tại
https://aistudio.google.com/. Nếu muốn thử model khác, gõ tên model vào
ô "Model" trong app (để trống = dùng mặc định).

**Sử dụng (chế độ "Tự động qua API"):**
1. Chọn nhà cung cấp AI (mặc định Gemini đã chọn sẵn).
2. Chọn **nguồn tình huống**:
   - **"Dán tình huống có sẵn"** — dán trực tiếp ca bệnh thô vào ô văn bản, hoặc
   - **"Nhập tên bài — AI tự tạo tình huống"** — chỉ cần gõ tên bài/chủ đề (ví dụ "Tiền sản giật", "Thai ngoài tử cung"), AI sẽ tự soạn 1 ca bệnh giả định hợp lý, hiện ra để bạn xem/sửa lại trước khi tiếp tục.
3. (Chỉ khi chọn "Nhập tên bài") có thể tick thêm **"Mỗi câu hỏi dùng 1 tình huống lâm sàng RIÊNG"** — thay vì 1 tình huống dùng chung cho cả bộ, mỗi câu sẽ có 1 ca bệnh độc lập riêng do AI tự tạo (chậm hơn vì cần gấp đôi số lượt gọi AI, nhưng tránh tình trạng các câu na ná giống nhau vì cùng dựa trên 1 ca).
4. Chọn **số lượng câu hỏi** (1–20, mặc định 10).
5. Chọn **miền năng lực** muốn hỏi — 5 nhóm: Chẩn đoán, Cận lâm sàng, Hướng điều trị, Điều trị cụ thể, Tiên lượng - Dự phòng (mặc định chọn hết; câu hỏi sẽ rải đều qua các miền đã chọn).
6. (Tuỳ chọn) vào menu **"Tài liệu tham chiếu"** → **"Nạp tài liệu tham chiếu chuẩn (.txt)..."** nếu muốn AI bám sát 1 tài liệu cụ thể (phác đồ, ngưỡng chẩn đoán chuẩn của bộ môn...) khi soạn câu hỏi.
7. (Tuỳ chọn) sửa tiêu đề ca bệnh sẽ hiện trong file Word.
8. Bấm **"Tạo bộ câu hỏi"** — app sẽ tự động: (a) [nếu chọn "Nhập tên bài"] nhờ AI tạo tình huống, (b) **nhờ AI biên soạn/chuẩn hoá lại tình huống** đó (sắp xếp đúng trình tự, viết rõ ràng hơn, không bỏ sót dữ kiện), rồi (c) tạo câu hỏi từ bản đã chuẩn hoá. Cả 3 bước chạy tự động nối tiếp, chờ vài chục giây tới hơn 1 phút tuỳ số bước.
9. App hiện **cửa sổ xem trước** ngay trong app — đọc/duyệt toàn bộ câu hỏi tại đây trước.
10. Khi ưng ý, bấm nút **"Xuất ra file Word..."** trong cửa sổ xem trước để mở hộp thoại lưu file `.docx` — việc lưu file là bước riêng, KHÔNG tự động xảy ra ngay sau khi tạo xong.

**Tự động loại câu không đạt:** sau khi sinh xong, app tự kiểm tra từng câu qua bảng kiểm 12 tiêu chí (heuristic + tự chấm của model) — câu nào **không đạt sẽ tự động bị loại** trước khi hiện trong cửa sổ xem trước. App thử tạo bù 1 lượt cho các câu bị loại (dùng lại đúng mã năng lực/mức độ tư duy) để cố gắng giữ đủ số lượng bạn yêu cầu; nếu vẫn thiếu, app hiện số câu đạt cuối cùng và báo rõ đã loại bao nhiêu câu.

**Phần thân được AI lọc từ tình huống gốc, không phải tự sáng tác:** với mỗi câu, AI sẽ CHỌN LỌC dữ kiện cần thiết từ đúng tình huống bạn đã cung cấp — giữ những gì liên quan đến câu hỏi cụ thể đó (theo miền năng lực), lược bỏ chi tiết gây nhiễu không cần thiết. AI **tuyệt đối không được thêm, bịa, hay đổi khác đi** bất kỳ dữ kiện nào không có trong tình huống gốc — chỉ được lược bớt, không được sáng tác. Nếu AI lỡ không trả về phần này, phần mềm tự dùng nguyên văn tình huống gốc làm phương án dự phòng.

Vào menu **Cài đặt** trong app để đổi hoặc xoá API key bất cứ lúc nào.

**Sử dụng (chế độ "Thủ công — dán vào Claude.ai/Gemini/ChatGPT"):**
1. Chọn radio **"Thủ công..."** ở đầu app (khung chọn nhà cung cấp AI sẽ mờ đi vì không cần dùng).
2. Chọn nguồn tình huống, số câu hỏi, miền năng lực như bình thường (lưu ý: chế độ "mỗi câu 1 tình huống riêng" KHÔNG dùng được ở chế độ thủ công, vì cần tự động lặp gọi AI nhiều lần).
3. Bấm **"Bắt đầu (chế độ thủ công)"**.
4. Nếu chọn "Nhập tên bài": cửa sổ **Bước 1/3 — Tạo tình huống** hiện ra — bấm **"Copy vào clipboard"**, dán vào Claude.ai/Gemini/ChatGPT (tài khoản thường của bạn), copy đoạn tình huống AI trả lời, dán vào ô bên dưới, bấm **"Tiếp tục"**. (Nếu chọn "Dán tình huống có sẵn", bỏ qua bước này, vào thẳng bước chuẩn hoá bên dưới.)
5. Cửa sổ **Bước chuẩn hoá tình huống** hiện ra, chứa sẵn prompt nhờ AI biên soạn lại tình huống cho chuẩn (sắp xếp đúng trình tự, viết rõ ràng hơn, không bỏ sót dữ kiện). Dán vào 1 cuộc trò chuyện MỚI, copy đoạn tình huống đã biên soạn lại, dán vào ô bên dưới, bấm "Tiếp tục".
6. Cửa sổ **Bước cuối — Tạo câu hỏi** hiện ra, chứa sẵn prompt tạo câu hỏi (đã gồm đúng tình huống đã chuẩn hoá). Copy, dán vào 1 cuộc trò chuyện MỚI, copy toàn bộ JSON AI trả lời, dán vào ô bên dưới, bấm **"Xử lý JSON này"**.
7. App tự kiểm tra kỹ thuật, tự loại câu không đạt (không có bước tạo bù tự động vì không gọi API), rồi hiện cửa sổ xem trước — bấm "Xuất ra file Word..." khi sẵn sàng.

Tổng cộng: 2 bước dán/copy nếu chọn "Dán tình huống có sẵn" (chuẩn hoá + tạo câu hỏi), hoặc 3 bước nếu chọn "Nhập tên bài" (tạo tình huống + chuẩn hoá + tạo câu hỏi).

## Cách khác: KHÔNG cần API key (dán thủ công qua Claude.ai/Gemini/ChatGPT...)

Nếu bạn không muốn tạo API key, vẫn dùng được công cụ qua dòng lệnh,
đổi lại phải tự copy/paste qua lại với 1 chatbot bất kỳ cho mỗi bước:

```bash
pip install python-docx   # không cần cài "google-genai" hay "anthropic"

# Bước 1: tạo prompt CHUẨN HOÁ tình huống (khuyên dùng, không bắt buộc)
python cli.py prepare --refine --input examples/sample_scenario.txt --prompt-output prompt_refine.txt
# Dán vào chatbot, copy tình huống đã chuẩn hoá trả về, LƯU ĐÈ vào lại
# examples/sample_scenario.txt (hoặc file tình huống của bạn)

# Bước 2: tạo file prompt tạo câu hỏi (dùng tình huống đã chuẩn hoá ở bước 1)
python cli.py prepare --input examples/sample_scenario.txt --prompt-output prompt.txt

# Bước 3: dán toàn bộ nội dung prompt.txt vào 1 cuộc trò chuyện MỚI trên
# Gemini/Claude.ai/ChatGPT... Copy khối JSON trả về, lưu vào answer.json

# Bước 4: kiểm tra kỹ thuật + xuất Word — chạy offline, không cần API key
python cli.py build --json-input answer.json --output output/bo_cau_hoi.docx \
    --scenario-file examples/sample_scenario.txt
```

Bước 1 (chuẩn hoá) là tuỳ chọn — có thể bỏ qua nếu tình huống của bạn
đã viết sẵn rõ ràng, mạch lạc.

Tuỳ chỉnh số câu và miền năng lực trong bước 2:
```bash
python cli.py prepare --input examples/sample_scenario.txt --prompt-output prompt.txt \
    -n 6 --categories chan_doan can_lam_sang dieu_tri_cu_the
```
(Bỏ `--categories` = mặc định dùng tất cả 5 miền. Xem `python cli.py prepare --help` để biết đủ mã miền năng lực.)

Nếu muốn AI tự tạo tình huống từ tên bài thay vì tự dán, dùng `--topic` thay `--input` ở bước 1 — công cụ sẽ tạo prompt riêng để lấy tình huống trước (dán vào chatbot, lưu kết quả), rồi chạy lại `prepare` với tình huống đó để lấy prompt tạo câu hỏi (bước 2):
```bash
python cli.py prepare --topic "Tiền sản giật" --prompt-output prompt_scenario.txt
# dán prompt_scenario.txt vào chatbot, lưu kết quả vào scenario.txt, rồi:
python cli.py prepare --input scenario.txt --prompt-output prompt.txt
```

## Cách khác nữa: dòng lệnh tự động hoàn toàn (cũng cần API key)

`generate` tự động chạy đủ các bước: (nếu có `--topic`) tạo tình huống →
**chuẩn hoá tình huống** → tạo câu hỏi. Thêm `--no-refine` nếu muốn bỏ
qua bước chuẩn hoá (dùng thẳng tình huống gốc, không qua chỉnh sửa).

```bash
pip install -r requirements.txt

# Dùng Gemini (mặc định) — có chuẩn hoá tình huống tự động
export GEMINI_API_KEY=AIza...
python cli.py generate --input examples/sample_scenario.txt --output output/bo_cau_hoi.docx

# Bỏ qua bước chuẩn hoá nếu tình huống đã viết sẵn chuẩn
python cli.py generate --input examples/sample_scenario.txt --no-refine --output output/bo_cau_hoi.docx

# Hoặc dùng Anthropic
export ANTHROPIC_API_KEY=sk-ant-...
python cli.py generate --provider anthropic --input examples/sample_scenario.txt --output output/bo_cau_hoi.docx

# Hoặc dùng OpenAI
export OPENAI_API_KEY=sk-proj-...
python cli.py generate --provider openai --input examples/sample_scenario.txt --output output/bo_cau_hoi.docx

# Hoặc dùng OpenRouter (miễn phí, dự phòng khi provider khác gặp lỗi)
export OPENROUTER_API_KEY=sk-or-...
python cli.py generate --provider openrouter --input examples/sample_scenario.txt --output output/bo_cau_hoi.docx

# Hoặc dùng Cerebras (siêu nhanh, tuỳ tài khoản có thể cần bật thanh toán)
export CEREBRAS_API_KEY=csk-...
python cli.py generate --provider cerebras --input examples/sample_scenario.txt --output output/bo_cau_hoi.docx

# Hoặc dùng Groq (siêu nhanh, miễn phí, không cần thẻ — khuyên dùng nếu các provider khác gặp trục trặc)
export GROQ_API_KEY=gsk_...
python cli.py generate --provider groq --input examples/sample_scenario.txt --output output/bo_cau_hoi.docx

# Tuỳ chỉnh số câu, miền năng lực, hoặc để AI tự tạo tình huống từ tên bài
python cli.py generate --topic "Thai ngoài tử cung" -n 6 \
    --categories chan_doan can_lam_sang tien_luong_du_phong \
    --output output/bo_cau_hoi.docx

# Mỗi câu hỏi dùng 1 tình huống riêng (chỉ dùng kèm --topic)
python cli.py generate --topic "Tiền sản giật" -n 5 \
    --per-question-scenario --output output/bo_cau_hoi.docx

# Dùng kèm tài liệu tham chiếu chuẩn (phác đồ, ngưỡng chẩn đoán riêng của bộ môn)
python cli.py generate --input examples/sample_scenario.txt \
    --reference-file phac_do_benh_vien.txt --output output/bo_cau_hoi.docx
```

CLI cũng tự động loại câu không đạt bảng kiểm 12 tiêu chí và thử tạo bù
1 lượt, giống hệt app giao diện — xem log in ra màn hình để biết đã loại
bao nhiêu câu.

Dùng cách này khi muốn chạy hàng loạt nhiều ca cùng lúc (script hoá),
thay vì mở app từng ca một.

## Tài liệu tham chiếu chuẩn quốc gia

**Mặc định (không cần làm gì thêm):** system prompt đã được cấu hình sẵn
để AI ưu tiên bám sát các văn bản hướng dẫn chuyên môn chính thức của
Bộ Y tế Việt Nam khi soạn câu hỏi, chọn văn bản phù hợp theo nội dung
ca bệnh:

| Văn bản | Quyết định | Dùng cho |
|---|---|---|
| Hướng dẫn chẩn đoán và điều trị các bệnh sản phụ khoa | 315/QĐ-BYT (2015) | Chẩn đoán, phác đồ điều trị bệnh lý sản/phụ khoa/sơ sinh nói chung |
| Hướng dẫn quốc gia về các dịch vụ chăm sóc sức khỏe sinh sản | 4128/QĐ-BYT (2016, đã cập nhật nhiều lần) | Chăm sóc trước/trong khi có thai, KHHGĐ, phá thai an toàn, SKSS vị thành niên, tiền mãn kinh/mãn kinh |
| Hướng dẫn quy trình kỹ thuật về Sản phụ khoa | 1377/QĐ-BYT (2013), cập nhật bởi 1296 & 1396/QĐ-BYT (2026) | Quy trình/thủ thuật kỹ thuật cụ thể (đỡ đẻ, hỗ trợ sinh sản...) |
| Chăm sóc thiết yếu bà mẹ, trẻ sơ sinh trong và ngay sau đẻ/mổ lấy thai (EENC) | 4673/QĐ-BYT (2014, đẻ thường) & 6734/QĐ-BYT (2016, mổ lấy thai) | Da kề da, kẹp dây rốn muộn, cho bú sớm ngay sau sinh |
| Hướng dẫn can thiệp dự phòng lây truyền HIV, viêm gan B, giang mai từ mẹ sang con | 678/QĐ-BYT (2025) | Dự phòng lây truyền mẹ-con 3 bệnh trên |

Đây chỉ là gợi ý theo tên/số quyết định để AI dùng kiến thức nó đã biết
về các văn bản này (nếu có) — không phải toàn văn được nhúng sẵn vào
code (tránh vấn đề bản quyền và vì mỗi văn bản dài hàng trăm trang). AI được
dặn không bịa số liệu/ngưỡng cụ thể nếu không chắc chắn là đúng theo
văn bản gốc.

**Nạp toàn văn để bám sát chính xác hơn (tuỳ chọn):** nếu muốn AI bám
sát đúng nội dung chi tiết (không chỉ dựa vào việc model "nhớ" văn bản),
tải file PDF/text chính thức về và nạp vào công cụ — hỗ trợ cả `.txt`
và `.pdf` (tự trích xuất text từ PDF):
- **App:** menu "Tài liệu tham chiếu" → "Nạp tài liệu tham chiếu chuẩn (.txt hoặc .pdf)...".
- **CLI:** thêm `--reference-file ten_file.pdf` (hoặc `.txt`) vào lệnh `prepare` hoặc `generate`.

Tài liệu tự nạp này luôn được ưu tiên cao hơn các văn bản mặc định nêu
trên nếu có khác biệt. Lưu ý: PDF dạng ảnh scan (không có lớp text) sẽ
không trích được nội dung — cần bản PDF gốc có text hoặc OCR trước.

Bạn có thể tìm các văn bản trên tại các nguồn công khai như thuvienphapluat.vn,
luatvietnam.vn, hoặc cổng thông tin Bộ Y tế/Sở Y tế/bệnh viện (tìm theo
đúng số quyết định nêu trên).

**Về việc lấy nội dung từ NotebookLM:** công cụ này không thể tự động
đọc notebook riêng tư của bạn trên notebooklm.google.com/notebook.google.com
(cần đăng nhập tài khoản Google, không phải trang công khai). Để dùng nội
dung đó, bạn cần tự xuất/copy ra file `.txt`/`.pdf` (hoặc copy trực tiếp
text) rồi nạp vào theo cách trên.

## Công cụ làm gì bên trong

1. **Sinh câu hỏi** — prompt gửi cho model đã mã hoá sẵn khung 04 miền
   năng lực / 11 năng lực, 3 mức độ tư duy (Vận dụng, Phân tích, Đánh
   giá — tương ứng bậc 3 trở lên trong thang Bloom, không bao giờ dừng
   ở mức Nhớ/Hiểu) và bảng kiểm 12 tiêu chí trước khi duyệt câu hỏi.
   Prompt giống
   hệt nhau dù dùng Gemini, Anthropic, OpenAI, OpenRouter, Cerebras,
   Groq, Mistral hay GitHub Models — chỉ khác
   nơi gọi API
   (`src/mcq_generator/providers.py`).
   - **Chỉ dùng tiếng Việt:** cấm chèn thuật ngữ tiếng Anh dưới mọi
     hình thức, kể cả để trong ngoặc đơn kèm bản dịch — toàn bộ câu
     hỏi phải dùng thuật ngữ y khoa tiếng Việt chuẩn.
   - **Liên hệ Danh mục 128 vấn đề chuyên môn cốt lõi** (Quyết định
     22/QĐ-HĐYKQG, 2026, của Hội đồng Y khoa Quốc gia — dùng cho Kỳ
     kiểm tra đánh giá năng lực hành nghề bác sĩ) khi phù hợp, để câu
     hỏi vừa ứng dụng cao vừa bám sát chuẩn thi quốc gia.
   - **Ràng buộc thời gian TRAT (77 giây/câu):** Phần thân + câu hỏi
     dẫn cộng lại không được vượt quá khoảng 5 dòng — đảm bảo thí sinh
     đọc và trả lời kịp trong 77 giây/câu theo cấu trúc bài thi TRAT.
     Validator tự động ước tính độ dài (dựa trên số ký tự) và cảnh báo
     nếu vượt ngưỡng.
   - **Phần thân được lọc từ tình huống gốc:** AI chọn lọc dữ kiện cần
     thiết cho từng câu (theo miền năng lực), lược bỏ chi tiết gây
     nhiễu — nhưng tuyệt đối không được thêm/bịa/đổi dữ kiện nào không
     có trong tình huống gốc (bạn cung cấp, hoặc AI tạo ra ở bước "Nhập
     tên bài"). Nếu AI lỡ không trả về phần thân, phần mềm tự dùng
     nguyên văn tình huống gốc làm phương án dự phòng.
   - **Lựa chọn kiểu TRAT (Team Readiness Assurance Test):** prompt yêu
     cầu 3 mồi nhử phải là phương án GẦN với đáp án đúng (chẩn đoán
     phân biệt thật sự được cân nhắc, cách diễn giải cận lâm sàng dễ
     nhầm lẫn...) — tránh mồi nhử quá xa, dễ loại trừ ngay mà không cần
     đọc kỹ tình huống, để buộc thí sinh phải tư duy thật sự.
2. **Kiểm tra kỹ thuật hai lớp**:
   - Model tự chấm từng câu theo đúng 12 tiêu chí trong bảng kiểm.
   - Một validator độc lập, **không dùng AI**, rà lại bằng heuristic
     khách quan: độ dài lựa chọn có cân đối không, có từ tuyệt đối
     ("luôn luôn", "tất cả", "duy nhất"...), có bẫy hội tụ ("tất cả các
     đáp án trên đều đúng"), lựa chọn trùng nhau, thiếu trường bắt buộc.
   - Câu nào không đạt (ở 1 trong 2 lớp trên) **tự động bị loại**, có
     thử tạo bù 1 lượt (chế độ API) trước khi chốt danh sách cuối cùng.
3. **Xem trước trong app, xuất Word là bước riêng:** kết quả hiện trong
   1 cửa sổ xem trước ngay trong app — đọc/duyệt xong mới bấm "Xuất ra
   file Word..." để lưu file `.docx` đúng bố cục mẫu (Câu N → mã năng
   lực/mức độ tư duy → Phần thân → Câu hỏi dẫn → 4 lựa chọn A–D → Đáp
   án → Giải thích → Kiểm tra kỹ thuật, kèm bảng tóm tắt ở cuối). Việc
   lưu file KHÔNG tự động xảy ra ngay sau khi tạo xong.

**Lưu ý quan trọng:** đây là **trợ lý soạn thảo**, không thay thế việc
giảng viên đọc và duyệt lại từng câu. Bảng kiểm tự động chỉ bắt lỗi kỹ
thuật máy móc — tính chính xác y khoa và mức độ phù hợp lâm sàng vẫn cần
người có chuyên môn thẩm định trước khi đưa vào ngân hàng câu hỏi chính
thức.

## Chọn số lượng câu hỏi và miền năng lực

App và CLI (`prepare`/`generate`) đều cho chọn:
- **Số lượng câu hỏi**: 1–20 (app dùng ô Spinbox; CLI dùng `-n`/`--n-questions`).
- **Miền năng lực muốn hỏi** — 5 nhóm định nghĩa trong
  `QUESTION_CATEGORIES` (`src/mcq_generator/competency_framework.py`):

| Mã (CLI `--categories`) | Nhãn hiển thị | Mã năng lực gốc |
|---|---|---|
| `chan_doan` | Chẩn đoán | B.5 |
| `can_lam_sang` | Cận lâm sàng | B.4 (cả chỉ định và đọc kết quả) |
| `huong_dieu_tri` | Hướng điều trị | C.9 (can thiệp lâm sàng) |
| `dieu_tri_cu_the` | Điều trị cụ thể | C.8 (điều trị bằng thuốc) |
| `tien_luong_du_phong` | Tiên lượng - Dự phòng | B.6 + C.7 |

Không chọn miền nào (app) hoặc bỏ qua `--categories` (CLI) = dùng tất cả
5 miền. Hàm `build_blueprint(n_questions, category_keys)` rải câu hỏi
đều (round-robin) qua các mã năng lực thuộc những miền đã chọn — miền có
2 mã con (như Tiên lượng - Dự phòng) sẽ tự chia đều giữa 2 mã đó.

Muốn đổi cách gộp nhóm (ví dụ tách riêng "Tiên lượng" và "Dự phòng"
thành 2 miền khác nhau, hoặc thêm miền mới), sửa `QUESTION_CATEGORIES`
trong `competency_framework.py`.

Bộ khung mặc định khi không dùng `build_blueprint` (ví dụ khi gọi thẳng
`generate_mcq_set()` không truyền `blueprint=`) vẫn là `DEFAULT_BLUEPRINT`
— 10 câu cố định bao phủ cả bệnh sử/khám và giao tiếp:

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

## Cấu trúc project

```
clinical-mcq-generator/
├── .claude/skills/clinical-mcq-writer/  # SKILL cho Claude Code/Claude.ai — Claude tự soạn câu hỏi trực tiếp, không cần API key riêng (xem README trong thư mục này)
├── gui_app.py                       # ỨNG DỤNG GIAO DIỆN — hỗ trợ cả API tự động lẫn chế độ thủ công (dán vào Claude.ai/Gemini/ChatGPT)
├── run_windows.bat / run_mac.command  # file double-click để mở app
├── cli.py                           # công cụ dòng lệnh: prepare / build / generate
├── requirements.txt
├── .env.example
├── examples/
│   └── sample_scenario.txt
├── src/mcq_generator/
│   ├── competency_framework.py     # khung 4 miền/11 năng lực, 5 miền chọn được (QUESTION_CATEGORIES), bảng kiểm 12 tiêu chí
│   ├── prompts.py                  # build prompt hệ thống + prompt người dùng + prompt "AI tự tạo tình huống từ tên bài"
│   ├── manual_mode.py              # ghép prompt để dán thủ công (không cần API key)
│   ├── providers.py                # gọi Gemini/Anthropic/OpenAI/OpenRouter/Cerebras/Groq/Mistral/GitHub Models — đổi provider chỉ sửa ở đây
│   ├── generator.py                # orchestration: chuẩn hoá tình huống → build prompt → gọi provider → parse JSON; có cả chế độ "1 tình huống chung" và "mỗi câu 1 tình huống riêng"
│   ├── json_utils.py                # bóc tách/parse JSON khoan dung, báo lỗi kèm ngữ cảnh — dùng chung cho cả API lẫn thủ công
│   ├── reference_loader.py          # đọc file tài liệu tham chiếu chuẩn (.txt/.pdf)
│   ├── config.py                   # lưu/đọc API key cục bộ theo từng provider
│   ├── validator.py                # kiểm tra kỹ thuật tự động (không cần AI)
│   └── docx_export.py              # xuất file Word đúng mẫu
└── tests/
    └── test_pipeline_offline.py    # test validator + docx export, KHÔNG gọi API thật
```

### Dùng qua Claude Code thay vì app Python

Nếu bạn mở repo này bằng **Claude Code**, không cần chạy `gui_app.py`
hay lo API key — Claude sẽ tự đọc skill ở `.claude/skills/clinical-mcq-writer/`
và tự soạn câu hỏi trực tiếp khi bạn yêu cầu. Xem chi tiết trong
`.claude/skills/clinical-mcq-writer/README.md`.

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
