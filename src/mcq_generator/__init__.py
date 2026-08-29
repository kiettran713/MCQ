from .validator import validate_all, validate_question, ValidationResult
from .docx_export import export_to_docx
from .competency_framework import DEFAULT_BLUEPRINT, ThinkingLevel, COMPETENCIES
from .manual_mode import build_manual_prompt

__all__ = [
    "validate_all",
    "validate_question",
    "ValidationResult",
    "export_to_docx",
    "DEFAULT_BLUEPRINT",
    "ThinkingLevel",
    "COMPETENCIES",
    "build_manual_prompt",
]

# generate_mcq_set / GenerationError cần thư viện `anthropic` + API key —
# chỉ import khi thực sự dùng, để chế độ thủ công (manual_mode) không bị
# bắt buộc cài "anthropic" hay có API key mới chạy được.
def __getattr__(name):
    if name in ("generate_mcq_set", "GenerationError"):
        from . import generator as _generator
        value = getattr(_generator, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
