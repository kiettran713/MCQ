"""
test_pipeline_offline.py
--------------------------
Test KHÔNG gọi API thật — dùng dữ liệu MCQ giả lập (giống định dạng model
sẽ trả về) để kiểm tra validator.py và docx_export.py hoạt động đúng.
Chạy: python -m pytest tests/ -v   (hoặc python tests/test_pipeline_offline.py)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcq_generator import export_to_docx, validate_all  # noqa: E402

FAKE_QUESTIONS = [
    {
        "question_number": 1,
        "competency_code": "B.3",
        "competency_name": "Bệnh sử/tiền sử/thăm khám thực thể",
        "thinking_level": "Vận dụng",
        "stem": "Bệnh nhân nữ 40 tuổi, PARA 1021, đến khám vì test thai "
                "dương tính kèm đau vùng hạ vị...",
        "lead_in": "Dữ kiện nào trong tiền sử có giá trị nhất khi đánh giá "
                   "nguy cơ bất thường của thai kỳ hiện tại?",
        "options": {
            "A": "Có hai lần thai kỳ trước kết thúc bất thường, đều cần "
                 "can thiệp lấy thai sau đó.",
            "B": "Đã từng mổ lấy thai vì chuyển dạ ngưng tiến triển từ trước.",
            "C": "Có triệu chứng nghén rõ trong thai kỳ hiện tại đang có.",
            "D": "Có đau vùng hạ vị trong thai kỳ hiện tại đang theo dõi.",
        },
        "correct_answer": "A",
        "rationale": "Tiền sử hai lần thai bất thường liên tiếp là yếu tố "
                     "nguy cơ trực tiếp nhất cho thai kỳ hiện tại.",
        "checklist_self_check": {
            "Câu hỏi lượng giá 1 khái niệm quan trọng": "Đạt",
            "Đáp án đủ thuyết phục, không gây tranh cãi": "Đạt",
        },
    },
    {
        # Câu này cố tình có lỗi kỹ thuật để kiểm tra validator bắt được.
        "question_number": 2,
        "competency_code": "B.4",
        "competency_name": "Cận lâm sàng/xét nghiệm chẩn đoán",
        "thinking_level": "Phân tích",
        "stem": "Siêu âm ghi nhận túi thai GS 7mm, chưa thấy phôi.",
        "lead_in": "Nhận định nào sau đây phù hợp nhất",  # thiếu dấu ?
        "options": {
            "A": "Đã xác định túi thai trong tử cung nhưng chưa đủ dữ "
                 "kiện để kết luận khả năng sống của thai ở thời điểm này.",
            "B": "Sai.",
            "C": "Tất cả các đáp án trên đều đúng.",
            "D": "Thai chắc chắn không thể sống được trong mọi trường hợp.",
        },
        "correct_answer": "A",
        "rationale": "Kích thước túi thai 7mm chưa đủ để kết luận.",
        "checklist_self_check": {
            "Không có lỗi kỹ thuật": "Chưa đạt: lựa chọn C và D có vấn đề",
        },
    },
]


def test_validator_flags_known_issues():
    results = validate_all(FAKE_QUESTIONS)
    assert results[0].ok, f"Câu 1 lẽ ra không có cảnh báo, nhưng có: {results[0].warnings}"

    q2 = results[1]
    assert not q2.ok
    joined = " ".join(q2.warnings)
    assert "chấm hỏi" in joined
    assert "bẫy hội tụ" in joined or "tất cả các đáp án trên" in joined.lower()
    assert "tuyệt đối" in joined or "mọi trường hợp" in joined.lower()
    print("OK: validator phát hiện đúng các lỗi kỹ thuật đã cài trong câu 2.")


def test_docx_export_runs(tmp_path=None):
    out_dir = Path(__file__).parent / "_tmp_output"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "test_output.docx"
    results = validate_all(FAKE_QUESTIONS)
    export_to_docx(
        FAKE_QUESTIONS,
        str(out_path),
        scenario_title="Ca test offline",
        raw_scenario="Đây là tình huống thô giả lập để test.",
        validation_results=results,
    )
    assert out_path.exists() and out_path.stat().st_size > 0
    print(f"OK: đã xuất file docx test tại {out_path}")


if __name__ == "__main__":
    test_validator_flags_known_issues()
    test_docx_export_runs()
    print("\nTất cả test offline PASS.")
