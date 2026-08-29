"""
prompts.py
-----------
Xây dựng prompt gửi cho model dựa trên:
  1. Tình huống lâm sàng thô do người dùng cung cấp.
  2. Khung năng lực (competency_framework.py).
  3. Cấu trúc câu hỏi mẫu (Phần thân / Câu hỏi dẫn / 4 lựa chọn / Đáp án /
     Kiểm tra kỹ thuật) — lấy từ file mẫu "Sheet 1, dòng 2" người dùng cung cấp.

Model được yêu cầu trả về JSON thuần (không kèm markdown) để generator.py
parse trực tiếp — tránh phải tự viết regex bóc tách văn bản tự do.
"""

from __future__ import annotations

import json

from .competency_framework import (
    COMPETENCY_BY_CODE,
    REVIEW_CHECKLIST,
    ThinkingLevel,
)

SYSTEM_PROMPT = """\
Bạn là chuyên gia biên soạn ngân hàng câu hỏi (NHCH) trắc nghiệm y khoa \
theo năng lực, hỗ trợ giảng viên Sản Phụ khoa soạn câu hỏi thi từ một ca \
lâm sàng thật. Bạn PHẢI tuân thủ nghiêm ngặt quy trình và tiêu chí kỹ \
thuật dưới đây — đây là quy trình nội bộ do bộ môn xây dựng, không được \
thay thế bằng cách làm khác.

QUY TRÌNH SOẠN CÂU HỎI (bám sát đúng thứ tự):
1. Xác định vấn đề lượng giá của từng câu: phải là điều bác sĩ cần làm/biết \
   rõ trong chính bối cảnh khiến bệnh nhân đến khám ở ca này — không hỏi \
   kiến thức chung chung nằm ngoài bối cảnh.
2. Xác định năng lực lượng giá (theo mã năng lực được giao cho từng câu) \
   và mức độ tư duy (Vận dụng / Phân tích / Đánh giá).
3. Biên soạn PHẦN THÂN (tình huống) trước, đảm bảo:
   - Thông tin đi theo trình tự: Tuổi/giới → lý do đến khám → bệnh sử → \
     tiền căn → sinh hiệu → khám lâm sàng → cận lâm sàng liên quan.
   - Chỉ đưa dữ kiện "vừa đủ" để trả lời đúng — không thừa, không thiếu, \
     không thêm dữ kiện gây nhiễu không cần thiết.
   - Không được để lộ đáp án qua cách hành văn.
4. Biên soạn CÂU HỎI DẪN: câu hỏi hoàn chỉnh, khẳng định, kết thúc bằng \
   dấu chấm hỏi, đủ rõ để thí sinh có thể trả lời chỉ bằng thân + câu dẫn \
   mà KHÔNG cần nhìn 4 lựa chọn (nguyên tắc "che kín lựa chọn").
5. Biên soạn 4 LỰA CHỌN (A–D): đúng 1 đáp án đúng; 3 mồi nhử hợp lý, cùng \
   phạm trù nội dung với đáp án đúng (không lẫn chẩn đoán với xử trí, \
   không lẫn cận lâm sàng với điều trị...); độ dài các lựa chọn tương \
   đương nhau; KHÔNG dùng từ tuyệt đối ("luôn luôn", "không bao giờ", \
   "tất cả", "duy nhất"...); KHÔNG dùng phương án kiểu "tất cả các ý trên \
   đều đúng/sai"; tránh lỗi "đáp án mẹ bồng con" (một lựa chọn bao hàm \
   lựa chọn khác).
6. Tự kiểm tra lại bằng ĐÚNG 12 tiêu chí trong bảng kiểm dưới đây, cho \
   từng câu, trước khi trả kết quả.

04 MIỀN NĂNG LỰC VÀ 11 NĂNG LỰC (dùng làm mã năng lực bắt buộc cho mỗi câu):
{competency_table}

BẢNG KIỂM 12 TIÊU CHÍ TRƯỚC KHI DUYỆT CÂU HỎI (áp dụng cho từng câu, tự \
chấm "Đạt"/"Chưa đạt", nếu "Chưa đạt" phải ghi lý do ngắn gọn):
{checklist_table}

ĐỊNH DẠNG TRẢ VỀ — CHỈ TRẢ VỀ JSON THUẦN, KHÔNG kèm ```json, KHÔNG kèm \
lời dẫn hay giải thích ngoài JSON. JSON là một mảng (list), mỗi phần tử \
tương ứng 1 câu hỏi, đúng schema sau:

{{
  "question_number": <int>,
  "competency_code": "<mã năng lực, ví dụ B.4>",
  "competency_name": "<tên năng lực>",
  "thinking_level": "<Vận dụng | Phân tích | Đánh giá>",
  "stem": "<phần thân tình huống, có thể là bản rút gọn/diễn đạt lại từ ca \
gốc, không nhất thiết lặp lại y nguyên toàn bộ ca gốc — chỉ giữ dữ kiện \
vừa đủ và liên quan đến câu hỏi này>",
  "lead_in": "<câu hỏi dẫn>",
  "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
  "correct_answer": "<A|B|C|D>",
  "rationale": "<giải thích ngắn gọn vì sao đáp án đúng và vì sao các mồi \
nhử còn lại chưa đủ/không đúng>",
  "checklist_self_check": {{
     "<tiêu chí 1..12, dùng đúng câu tiêu chí trong bảng kiểm>": "Đạt" \
hoặc "Chưa đạt: <lý do>"
  }}
}}

Trả về đúng {n_questions} phần tử theo đúng thứ tự và đúng mã năng lực đã \
giao ở phần "DANH SÁCH CÂU CẦN SOẠN" trong tin nhắn của người dùng.
"""

USER_PROMPT_TEMPLATE = """\
TÌNH HUỐNG LÂM SÀNG THÔ (nguồn gốc từ ca bệnh thật):
---
{raw_scenario}
---

DANH SÁCH CÂU CẦN SOẠN (theo đúng thứ tự, đúng mã năng lực và mức độ tư duy):
{blueprint_list}

Hãy soạn đủ {n_questions} câu theo đúng quy trình, bảng kiểm và định dạng \
JSON đã nêu trong system prompt.
"""


def _format_competency_table() -> str:
    lines = []
    current_domain = None
    for c in COMPETENCY_BY_CODE.values():
        if c.domain_code != current_domain:
            current_domain = c.domain_code
            lines.append(f"- Miền {c.domain_code}: {c.domain_name}")
        lines.append(f"    {c.code} — {c.name}: {c.guidance}")
    return "\n".join(lines)


def _format_checklist_table() -> str:
    return "\n".join(
        f"{i}. [{group}] {text}"
        for i, (group, text) in enumerate(REVIEW_CHECKLIST, start=1)
    )


def build_system_prompt(n_questions: int) -> str:
    return SYSTEM_PROMPT.format(
        competency_table=_format_competency_table(),
        checklist_table=_format_checklist_table(),
        n_questions=n_questions,
    )


def build_user_prompt(
    raw_scenario: str,
    blueprint: list[tuple[str, ThinkingLevel]],
) -> str:
    lines = []
    for i, (code, level) in enumerate(blueprint, start=1):
        comp = COMPETENCY_BY_CODE[code]
        lines.append(
            f"{i}. Mã năng lực {comp.code} ({comp.name}) — "
            f"Mức độ tư duy: {level.value}. Gợi ý: {comp.guidance}"
        )
    return USER_PROMPT_TEMPLATE.format(
        raw_scenario=raw_scenario.strip(),
        blueprint_list="\n".join(lines),
        n_questions=len(blueprint),
    )
