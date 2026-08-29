"""
generator.py
-------------
Gọi Anthropic API (Claude) để sinh bộ câu hỏi MCQ từ 1 tình huống lâm sàng
thô, dựa trên prompts.py và competency_framework.py.

Cách dùng cơ bản:

    from mcq_generator.generator import generate_mcq_set

    questions = generate_mcq_set(raw_scenario="....")

Yêu cầu biến môi trường ANTHROPIC_API_KEY (xem README.md / .env.example).
"""

from __future__ import annotations

import json
import os

from .competency_framework import DEFAULT_BLUEPRINT, ThinkingLevel
from .prompts import build_system_prompt, build_user_prompt

DEFAULT_MODEL = "claude-sonnet-4-6"


class GenerationError(RuntimeError):
    """Lỗi khi gọi model hoặc khi parse kết quả trả về."""


def _extract_json_array(raw_text: str) -> list[dict]:
    """Model được yêu cầu trả JSON thuần, nhưng vẫn phòng trường hợp
    model lỡ bọc thêm ```json ... ``` hoặc thêm vài dòng giải thích."""
    text = raw_text.strip()
    if text.startswith("```"):
        # bỏ dòng ``` đầu và ``` cuối (có thể kèm "json")
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end < start:
        raise GenerationError(
            "Không tìm thấy mảng JSON hợp lệ trong phản hồi của model.\n"
            f"Nội dung nhận được:\n{raw_text[:2000]}"
        )
    candidate = text[start : end + 1]
    try:
        data = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise GenerationError(
            f"Lỗi parse JSON: {exc}\nNội dung:\n{candidate[:2000]}"
        ) from exc
    if not isinstance(data, list):
        raise GenerationError("JSON trả về không phải là một mảng (list).")
    return data


def generate_mcq_set(
    raw_scenario: str,
    blueprint: list[tuple[str, ThinkingLevel]] | None = None,
    model: str = DEFAULT_MODEL,
    max_tokens: int = 8000,
    api_key: str | None = None,
) -> list[dict]:
    """Sinh bộ câu hỏi MCQ từ 1 tình huống lâm sàng thô.

    Parameters
    ----------
    raw_scenario:
        Văn bản tình huống lâm sàng thô do người dùng cung cấp.
    blueprint:
        Danh sách (mã năng lực, mức độ tư duy) cho từng câu, theo đúng thứ
        tự mong muốn. Mặc định dùng DEFAULT_BLUEPRINT (10 câu, bao phủ
        chẩn đoán / cận lâm sàng / điều trị / tiên lượng / dự phòng...).
    model:
        Tên model Claude dùng để sinh câu hỏi.
    max_tokens:
        Giới hạn token đầu ra — 10 câu hỏi kèm bảng kiểm tự chấm thường
        cần khá nhiều token, tăng nếu bị cắt giữa chừng.
    api_key:
        Nếu không truyền, sẽ lấy từ biến môi trường ANTHROPIC_API_KEY.
    """
    try:
        import anthropic
    except ImportError as exc:
        raise GenerationError(
            "Thiếu thư viện 'anthropic'. Cài bằng: pip install anthropic"
        ) from exc

    if not raw_scenario or not raw_scenario.strip():
        raise ValueError("raw_scenario không được để trống.")

    blueprint = blueprint or DEFAULT_BLUEPRINT
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise GenerationError(
            "Chưa có ANTHROPIC_API_KEY. Đặt biến môi trường hoặc truyền "
            "api_key= khi gọi generate_mcq_set()."
        )

    client = anthropic.Anthropic(api_key=key)
    system_prompt = build_system_prompt(n_questions=len(blueprint))
    user_prompt = build_user_prompt(raw_scenario, blueprint)

    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw_text = "".join(
        block.text for block in response.content if block.type == "text"
    )
    questions = _extract_json_array(raw_text)

    # Đảm bảo question_number đúng thứ tự 1..n dù model có đánh số sai.
    for i, q in enumerate(questions, start=1):
        q["question_number"] = i

    return questions
