"""
generator.py
-------------
Gọi một LLM (mặc định Gemini, có thể đổi sang Anthropic) để sinh bộ câu
hỏi MCQ từ 1 tình huống lâm sàng thô, dựa trên prompts.py và
competency_framework.py. Việc gọi model thực tế nằm ở providers.py —
file này chỉ lo build prompt, gọi providers.call_llm(), rồi parse JSON.

Cách dùng cơ bản:

    from mcq_generator.generator import generate_mcq_set

    questions = generate_mcq_set(raw_scenario="....")  # dùng Gemini mặc định

Yêu cầu biến môi trường GEMINI_API_KEY (hoặc ANTHROPIC_API_KEY nếu dùng
provider="anthropic") — xem README.md / .env.example.
"""

from __future__ import annotations

import json
import os

from .competency_framework import DEFAULT_BLUEPRINT, ThinkingLevel
from .prompts import build_system_prompt, build_user_prompt
from .providers import ProviderError, call_llm

DEFAULT_PROVIDER = "gemini"


class GenerationError(RuntimeError):
    """Lỗi khi gọi model hoặc khi parse kết quả trả về."""


def _extract_json_array(raw_text: str) -> list[dict]:
    """Model được yêu cầu trả JSON thuần, nhưng vẫn phòng trường hợp
    model lỡ bọc thêm ```json ... ``` hoặc thêm vài dòng giải thích."""
    text = raw_text.strip()
    if text.startswith("```"):
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


def _resolve_api_key(provider: str, api_key: str | None) -> str:
    if api_key:
        return api_key

    env_var = "GEMINI_API_KEY" if provider == "gemini" else "ANTHROPIC_API_KEY"
    key = os.environ.get(env_var)
    if key:
        return key

    # fallback: key đã lưu cục bộ qua app giao diện (config.py)
    from .config import load_api_key
    key = load_api_key(provider)
    if key:
        return key

    raise GenerationError(
        f"Chưa có API key cho provider={provider!r}. Đặt biến môi trường "
        f"{env_var} hoặc truyền api_key= khi gọi generate_mcq_set()."
    )


def generate_mcq_set(
    raw_scenario: str,
    blueprint: list[tuple[str, ThinkingLevel]] | None = None,
    provider: str = DEFAULT_PROVIDER,
    model: str | None = None,
    max_tokens: int = 8000,
    api_key: str | None = None,
) -> list[dict]:
    """Sinh bộ câu hỏi MCQ từ 1 tình huống lâm sàng thô.

    Parameters
    ----------
    raw_scenario:
        Văn bản tình huống lâm sàng thô do người dùng cung cấp.
    blueprint:
        Danh sách (mã năng lực, mức độ tư duy) cho từng câu. Mặc định
        dùng DEFAULT_BLUEPRINT (10 câu).
    provider:
        "gemini" (mặc định) hoặc "anthropic".
    model:
        Tên model cụ thể. Nếu bỏ trống, dùng model mặc định của provider
        (xem providers.DEFAULT_MODEL_BY_PROVIDER).
    max_tokens:
        Giới hạn token đầu ra — tăng nếu bị cắt giữa chừng.
    api_key:
        Nếu không truyền, tự tìm theo thứ tự: biến môi trường
        (GEMINI_API_KEY / ANTHROPIC_API_KEY) → key đã lưu cục bộ qua app
        giao diện (config.py).
    """
    if not raw_scenario or not raw_scenario.strip():
        raise ValueError("raw_scenario không được để trống.")

    blueprint = blueprint or DEFAULT_BLUEPRINT
    key = _resolve_api_key(provider, api_key)

    system_prompt = build_system_prompt(n_questions=len(blueprint))
    user_prompt = build_user_prompt(raw_scenario, blueprint)

    try:
        raw_text = call_llm(
            provider=provider,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=model,
            api_key=key,
            max_tokens=max_tokens,
        )
    except ProviderError as exc:
        raise GenerationError(str(exc)) from exc

    questions = _extract_json_array(raw_text)

    # Đảm bảo question_number đúng thứ tự 1..n dù model có đánh số sai.
    for i, q in enumerate(questions, start=1):
        q["question_number"] = i

    return questions
