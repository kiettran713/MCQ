"""
providers.py
-------------
Lớp trừu tượng gọi model — tách riêng "gọi LLM nào, bằng SDK nào" ra khỏi
phần logic build prompt / parse JSON trong generator.py. Nhờ vậy đổi nhà
cung cấp (Gemini/Anthropic...) chỉ cần sửa file này.

Mỗi hàm call_* nhận (system_prompt, user_prompt, model, api_key, max_tokens)
và trả về CHUỖI VĂN BẢN thô model trả lời — việc parse JSON nằm ở
generator.py, dùng chung cho mọi provider.
"""

from __future__ import annotations

DEFAULT_MODEL_BY_PROVIDER = {
    "gemini": "gemini-2.5-pro",
    "anthropic": "claude-sonnet-4-6",
}


class ProviderError(RuntimeError):
    """Lỗi khi gọi nhà cung cấp LLM (thiếu SDK, sai key, lỗi mạng...)."""


def call_gemini(
    system_prompt: str,
    user_prompt: str,
    model: str,
    api_key: str,
    max_tokens: int,
) -> str:
    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise ProviderError(
            "Thiếu thư viện 'google-genai'. Cài bằng: pip install google-genai"
        ) from exc

    client = genai.Client(api_key=api_key)
    try:
        response = client.models.generate_content(
            model=model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=max_tokens,
                temperature=0.4,
            ),
        )
    except Exception as exc:  # noqa: BLE001 - bọc lại lỗi SDK cho thống nhất
        raise ProviderError(f"Lỗi gọi Gemini API: {exc}") from exc

    text = getattr(response, "text", None)
    if not text:
        raise ProviderError(
            "Gemini không trả về nội dung văn bản. Có thể do bị chặn bởi "
            "bộ lọc an toàn hoặc hết max_tokens — thử tăng max_tokens hoặc "
            "kiểm tra response.prompt_feedback."
        )
    return text


def call_anthropic(
    system_prompt: str,
    user_prompt: str,
    model: str,
    api_key: str,
    max_tokens: int,
) -> str:
    try:
        import anthropic
    except ImportError as exc:
        raise ProviderError(
            "Thiếu thư viện 'anthropic'. Cài bằng: pip install anthropic"
        ) from exc

    client = anthropic.Anthropic(api_key=api_key)
    try:
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
    except Exception as exc:  # noqa: BLE001
        raise ProviderError(f"Lỗi gọi Anthropic API: {exc}") from exc

    return "".join(block.text for block in response.content if block.type == "text")


CALL_FUNCTIONS = {
    "gemini": call_gemini,
    "anthropic": call_anthropic,
}


def call_llm(
    provider: str,
    system_prompt: str,
    user_prompt: str,
    model: str | None,
    api_key: str,
    max_tokens: int,
) -> str:
    provider = provider.lower().strip()
    if provider not in CALL_FUNCTIONS:
        raise ProviderError(
            f"Nhà cung cấp không hỗ trợ: {provider!r}. "
            f"Chọn một trong: {list(CALL_FUNCTIONS)}"
        )
    resolved_model = model or DEFAULT_MODEL_BY_PROVIDER[provider]
    return CALL_FUNCTIONS[provider](
        system_prompt, user_prompt, resolved_model, api_key, max_tokens
    )
