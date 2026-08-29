#!/usr/bin/env python3
"""
cli.py
-------
Công cụ dòng lệnh soạn bộ 10 câu hỏi MCQ theo năng lực từ 1 tình huống
lâm sàng thô. Có 2 cách dùng:

CÁCH 1 — KHÔNG CẦN API KEY (khuyên dùng nếu bạn đã có Claude.ai/Claude app):

    # Bước 1: tạo file prompt để dán thủ công vào Claude.ai
    python cli.py prepare --input examples/sample_scenario.txt --prompt-output prompt.txt

    # Bước 2: mở prompt.txt, copy toàn bộ, dán vào 1 cuộc trò chuyện mới
    #          trên Claude.ai (hoặc Claude app). Claude sẽ trả về JSON.
    #          Copy toàn bộ JSON đó, lưu vào 1 file, ví dụ answer.json

    # Bước 3: kiểm tra kỹ thuật + xuất file Word — KHÔNG cần API, chạy
    #          hoàn toàn bằng Python
    python cli.py build --json-input answer.json --output output/bo_cau_hoi.docx \
        --scenario-file examples/sample_scenario.txt

CÁCH 2 — TỰ ĐỘNG HOÀN TOÀN, CẦN ANTHROPIC_API_KEY:

    export ANTHROPIC_API_KEY=sk-ant-...
    python cli.py generate --input examples/sample_scenario.txt --output output/bo_cau_hoi.docx

Xem thêm: python cli.py --help / python cli.py <lệnh con> --help
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcq_generator import (  # noqa: E402
    DEFAULT_BLUEPRINT,
    build_manual_prompt,
    export_to_docx,
    validate_all,
)


def _read_text_arg_or_stdin(path, what):
    if path:
        return Path(path).read_text(encoding="utf-8")
    if not sys.stdin.isatty():
        return sys.stdin.read()
    raise SystemExit(
        f"Cần cung cấp {what}: dùng --input <file> hoặc pipe qua stdin."
    )


def cmd_prepare(args):
    """Tạo file prompt để dán thủ công vào Claude.ai — không gọi API."""
    raw_scenario = _read_text_arg_or_stdin(args.input, "tình huống lâm sàng thô")
    prompt_text = build_manual_prompt(raw_scenario)

    out_path = Path(args.prompt_output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(prompt_text, encoding="utf-8")

    print(f"Đã tạo prompt tại: {out_path}")
    print(
        "\nBước tiếp theo:\n"
        f"  1. Mở file {out_path}, copy TOÀN BỘ nội dung.\n"
        "  2. Dán vào một cuộc trò chuyện MỚI trên Claude.ai hoặc Claude app.\n"
        "  3. Claude sẽ trả lời bằng một khối JSON (mảng 10 phần tử). "
        "Copy toàn bộ JSON đó, lưu vào 1 file, ví dụ answer.json.\n"
        "  4. Chạy: python cli.py build --json-input answer.json "
        "--output output/bo_cau_hoi.docx"
    )


def cmd_build(args):
    """Đọc JSON câu hỏi (đã dán về từ Claude.ai), kiểm tra kỹ thuật và
    xuất file Word — hoàn toàn không cần API key."""
    json_text = Path(args.json_input).read_text(encoding="utf-8")
    try:
        questions = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"Không parse được JSON trong {args.json_input}: {exc}\n"
            "Kiểm tra lại: có thể Claude đã kèm thêm ```json ở đầu/cuối, "
            "hãy xoá phần đó rồi lưu lại file, chỉ giữ đúng mảng JSON."
        ) from exc

    if not isinstance(questions, list):
        raise SystemExit("File JSON phải là một mảng (list) các câu hỏi.")

    for i, q in enumerate(questions, start=1):
        q["question_number"] = i

    results = validate_all(questions)
    n_warnings = sum(len(r.warnings) for r in results)
    print(f"Đã nạp {len(questions)} câu. Kiểm tra kỹ thuật tự động: "
          f"{n_warnings} cảnh báo (xem chi tiết trong file .docx).")

    raw_scenario = None
    if args.scenario_file:
        raw_scenario = Path(args.scenario_file).read_text(encoding="utf-8")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    export_to_docx(
        questions,
        str(output_path),
        scenario_title=args.title,
        raw_scenario=raw_scenario,
        validation_results=results,
    )
    print(f"Đã lưu file Word: {output_path}")


def cmd_generate(args):
    """Chế độ tự động hoàn toàn — cần API key của provider đã chọn."""
    from mcq_generator import GenerationError, generate_mcq_set

    raw_scenario = _read_text_arg_or_stdin(args.input, "tình huống lâm sàng thô")

    print(f"Đang gọi {args.provider} để sinh {len(DEFAULT_BLUEPRINT)} câu hỏi...")
    try:
        questions = generate_mcq_set(
            raw_scenario, provider=args.provider, model=args.model
        )
    except GenerationError as exc:
        print(f"Lỗi: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    results = validate_all(questions)
    n_warnings = sum(len(r.warnings) for r in results)
    print(f"Đã sinh {len(questions)} câu. Kiểm tra kỹ thuật tự động: "
          f"{n_warnings} cảnh báo (xem chi tiết trong file .docx).")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    export_to_docx(
        questions,
        str(output_path),
        scenario_title=args.title,
        raw_scenario=raw_scenario,
        validation_results=results,
    )
    print(f"Đã lưu file Word: {output_path}")

    if args.json_output:
        json_path = Path(args.json_output)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(
            json.dumps(questions, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"Đã lưu file JSON: {json_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Soạn bộ câu hỏi MCQ lâm sàng theo năng lực từ 1 tình huống thô."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_prepare = sub.add_parser(
        "prepare",
        help="[Không cần API key] Tạo prompt để dán thủ công vào Claude.ai",
    )
    p_prepare.add_argument("--input", "-i", help="File .txt chứa tình huống thô. Bỏ qua để đọc từ stdin.")
    p_prepare.add_argument("--prompt-output", "-p", default="prompt.txt", help="Nơi lưu file prompt.")
    p_prepare.set_defaults(func=cmd_prepare)

    p_build = sub.add_parser(
        "build",
        help="[Không cần API key] Kiểm tra kỹ thuật + xuất .docx từ JSON đã có sẵn",
    )
    p_build.add_argument("--json-input", "-j", required=True, help="File JSON câu hỏi (dán về từ Claude.ai).")
    p_build.add_argument("--output", "-o", default="output/bo_cau_hoi.docx", help="File .docx đầu ra.")
    p_build.add_argument("--scenario-file", help="File tình huống thô gốc, để in kèm trong docx (tuỳ chọn).")
    p_build.add_argument("--title", default="Tình huống lâm sàng", help="Tiêu đề phụ trong file Word.")
    p_build.set_defaults(func=cmd_build)

    p_generate = sub.add_parser(
        "generate",
        help="[Cần API key] Sinh + kiểm tra + xuất .docx tự động, chỉ 1 lệnh",
    )
    p_generate.add_argument("--input", "-i", help="File .txt chứa tình huống thô. Bỏ qua để đọc từ stdin.")
    p_generate.add_argument("--output", "-o", default="output/bo_cau_hoi.docx", help="File .docx đầu ra.")
    p_generate.add_argument("--json-output", help="Lưu thêm bản JSON thô tại đây (tuỳ chọn).")
    p_generate.add_argument("--title", default="Tình huống lâm sàng", help="Tiêu đề phụ trong file Word.")
    p_generate.add_argument("--provider", default="gemini", choices=["gemini", "anthropic"], help="Nhà cung cấp AI (mặc định: gemini).")
    p_generate.add_argument("--model", default=None, help="Tên model cụ thể (mặc định theo provider).")
    p_generate.set_defaults(func=cmd_generate)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
