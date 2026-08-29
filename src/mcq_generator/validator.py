"""
validator.py
-------------
Các kiểm tra kỹ thuật TỰ ĐỘNG, độc lập với việc model tự chấm bảng kiểm.
Đây là lớp phòng vệ thứ hai — model có thể tự chấm "Đạt" nhầm, nên ta
kiểm tra lại bằng heuristic đơn giản, khách quan, không cần gọi model.

Không thay thế việc giảng viên đọc và duyệt lại câu hỏi — chỉ giúp lọc
nhanh các lỗi kỹ thuật phổ biến trước khi con người xem.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .competency_framework import ABSOLUTE_WORDS, CONVERGENCE_TRAP_PATTERNS


@dataclass
class ValidationResult:
    question_number: int
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.warnings


def _length_balance_warning(options: dict[str, str]) -> str | None:
    lengths = {k: len(v) for k, v in options.items()}
    longest = max(lengths.values())
    shortest = min(lengths.values())
    if shortest == 0:
        return None
    # Nếu lựa chọn dài nhất gấp hơn 1.8 lần lựa chọn ngắn nhất, khả năng
    # cao thí sinh sẽ đoán được nhờ "đáp án dài nhất thường đúng".
    if longest / shortest > 1.8:
        return (
            f"Độ dài lựa chọn chênh lệch lớn (ngắn nhất {shortest} ký tự, "
            f"dài nhất {longest} ký tự) — nên viết lại cho cân đối."
        )
    return None


def _absolute_word_warnings(options: dict[str, str]) -> list[str]:
    warnings = []
    for key, text in options.items():
        lowered = text.lower()
        for word in ABSOLUTE_WORDS:
            if word in lowered:
                warnings.append(
                    f"Lựa chọn {key} chứa từ tuyệt đối \"{word}\" — cân "
                    "nhắc viết lại để tránh mồi nhử/đáp án quá dễ loại trừ."
                )
    return warnings


def _convergence_trap_warnings(options: dict[str, str]) -> list[str]:
    warnings = []
    for key, text in options.items():
        lowered = text.lower()
        for pattern in CONVERGENCE_TRAP_PATTERNS:
            if pattern in lowered:
                warnings.append(
                    f"Lựa chọn {key} dùng mẫu câu bẫy hội tụ (\"{pattern}\") "
                    "— loại mẫu câu này thường bị cấm trong NHCH năng lực."
                )
    return warnings


def _duplicate_option_warning(options: dict[str, str]) -> str | None:
    seen = {}
    for key, text in options.items():
        norm = " ".join(text.lower().split())
        if norm in seen:
            return f"Lựa chọn {key} và {seen[norm]} trùng nội dung."
        seen[norm] = key
    return None


def _missing_field_warnings(q: dict) -> list[str]:
    warnings = []
    required = ["stem", "lead_in", "options", "correct_answer", "rationale"]
    for field_name in required:
        if not q.get(field_name):
            warnings.append(f"Thiếu trường bắt buộc: {field_name}")
    options = q.get("options") or {}
    for letter in ["A", "B", "C", "D"]:
        if letter not in options or not str(options[letter]).strip():
            warnings.append(f"Thiếu lựa chọn {letter}.")
    if q.get("correct_answer") not in {"A", "B", "C", "D"}:
        warnings.append(
            f"correct_answer không hợp lệ: {q.get('correct_answer')!r}"
        )
    if not q.get("lead_in", "").strip().endswith("?"):
        warnings.append("Câu hỏi dẫn nên kết thúc bằng dấu chấm hỏi.")
    return warnings


def validate_question(q: dict) -> ValidationResult:
    result = ValidationResult(question_number=q.get("question_number", -1))
    result.warnings.extend(_missing_field_warnings(q))

    options = q.get("options") or {}
    if len(options) == 4 and all(options.values()):
        balance_warning = _length_balance_warning(options)
        if balance_warning:
            result.warnings.append(balance_warning)
        result.warnings.extend(_absolute_word_warnings(options))
        result.warnings.extend(_convergence_trap_warnings(options))
        dup_warning = _duplicate_option_warning(options)
        if dup_warning:
            result.warnings.append(dup_warning)

    self_check = q.get("checklist_self_check") or {}
    failed_criteria = [
        crit for crit, verdict in self_check.items()
        if isinstance(verdict, str) and not verdict.strip().lower().startswith("đạt")
    ]
    for crit in failed_criteria:
        result.warnings.append(f"Bảng kiểm tự chấm 'Chưa đạt': {crit}")

    return result


def validate_all(questions: list[dict]) -> list[ValidationResult]:
    return [validate_question(q) for q in questions]
