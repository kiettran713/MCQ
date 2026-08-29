"""
manual_mode.py
---------------
Chế độ THỦ CÔNG — dùng khi bạn KHÔNG có (hoặc không muốn dùng) API key.

Ý tưởng: tách rời 2 việc:
  1. "Soạn câu hỏi" — việc này cần một LLM. Nếu không gọi API, bạn có thể
     dùng chính Claude.ai / Claude app bạn đang có sẵn: dán prompt do hàm
     build_manual_prompt() tạo ra vào cửa sổ chat, Claude sẽ trả về JSON.
  2. "Kiểm tra kỹ thuật + xuất file Word" — việc này KHÔNG cần AI, chạy
     hoàn toàn bằng validator.py + docx_export.py (Python thuần).

Vì vậy bạn chỉ cần: prepare (tạo prompt) → dán vào Claude.ai → copy JSON
Claude trả về → build (kiểm tra + xuất docx). Không tốn API key nào cả.
"""

from __future__ import annotations

from .competency_framework import DEFAULT_BLUEPRINT, ThinkingLevel
from .prompts import build_system_prompt, build_user_prompt


def build_manual_prompt(
    raw_scenario: str,
    blueprint: list[tuple[str, ThinkingLevel]] | None = None,
) -> str:
    """Ghép system prompt + user prompt thành 1 khối văn bản duy nhất,
    kèm hướng dẫn ngắn ở đầu và cuối — sẵn sàng để dán thẳng vào ô chat
    của Claude.ai / Claude app (không có khái niệm "system prompt" riêng
    khi chat thủ công, nên gộp chung vào 1 tin nhắn)."""
    blueprint = blueprint or DEFAULT_BLUEPRINT
    system_part = build_system_prompt(n_questions=len(blueprint))
    user_part = build_user_prompt(raw_scenario, blueprint)

    return (
        "Bạn hãy đóng vai trò và làm đúng theo hướng dẫn dưới đây.\n\n"
        f"{system_part}\n\n"
        f"{user_part}\n\n"
        "NHẮC LẠI: chỉ trả về JSON thuần (một mảng), không kèm lời dẫn, "
        "không kèm ```json, không kèm giải thích nào khác ngoài JSON."
    )
