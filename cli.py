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
    QUESTION_CATEGORIES,
    build_blueprint,
    build_manual_prompt,
    build_manual_refine_scenario_prompt,
    build_manual_scenario_prompt,
    export_to_docx,
    extract_json_array,
    validate_all,
)
from mcq_generator.json_utils import JsonExtractionError
from mcq_generator.reference_loader import ReferenceLoadError, load_reference_text

CATEGORY_KEYS = [c.key for c in QUESTION_CATEGORIES]
CATEGORY_HELP = "; ".join(f"{c.key}={c.label}" for c in QUESTION_CATEGORIES)


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
    if args.topic:
        # Bước khi dùng chế độ "AI tự tạo tình huống" thủ công: tạo
        # prompt để lấy tình huống trước, chưa tạo câu hỏi vội.
        prompt_text = build_manual_scenario_prompt(args.topic)
        out_path = Path(args.prompt_output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(prompt_text, encoding="utf-8")
        print(f"Đã tạo prompt (bước 1/3 — tạo tình huống) tại: {out_path}")
        print(
            "\nBước tiếp theo:\n"
            f"  1. Mở file {out_path}, copy TOÀN BỘ, dán vào Claude.ai/Gemini/ChatGPT.\n"
            "  2. Copy đoạn tình huống trả về, lưu vào 1 file .txt, ví dụ scenario.txt.\n"
            "  3. Chạy lại: python cli.py prepare --refine --input scenario.txt "
            "--prompt-output prompt_refine.txt để lấy prompt bước 2 (chuẩn hoá tình huống)."
        )
        return

    raw_scenario = _read_text_arg_or_stdin(args.input, "tình huống lâm sàng thô")

    if args.refine:
        # Bước riêng: chỉ tạo prompt CHUẨN HOÁ tình huống (không phải
        # prompt tạo câu hỏi) — dùng khi tình huống chưa qua bước biên
        # soạn lại (ví dụ vừa lấy từ bước --topic, hoặc do người dùng tự
        # dán tình huống thô, viết tắt/chưa chuẩn).
        prompt_text = build_manual_refine_scenario_prompt(raw_scenario)
        out_path = Path(args.prompt_output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(prompt_text, encoding="utf-8")
        print(f"Đã tạo prompt (bước chuẩn hoá tình huống) tại: {out_path}")
        print(
            "\nBước tiếp theo:\n"
            f"  1. Mở file {out_path}, copy TOÀN BỘ, dán vào Claude.ai/Gemini/ChatGPT.\n"
            "  2. Copy đoạn tình huống ĐÃ CHUẨN HOÁ trả về, lưu đè vào lại file tình "
            "huống (ví dụ scenario.txt).\n"
            "  3. Chạy lại: python cli.py prepare --input scenario.txt "
            "--prompt-output prompt.txt (bỏ --refine) để lấy prompt tạo câu hỏi."
        )
        return

    blueprint = build_blueprint(args.n_questions, args.categories)
    reference_knowledge = None
    if args.reference_file:
        try:
            reference_knowledge = load_reference_text(args.reference_file)
        except ReferenceLoadError as exc:
            raise SystemExit(f"Lỗi đọc tài liệu tham chiếu: {exc}") from exc
    prompt_text = build_manual_prompt(
        raw_scenario, blueprint=blueprint, reference_knowledge=reference_knowledge
    )

    out_path = Path(args.prompt_output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(prompt_text, encoding="utf-8")

    print(f"Đã tạo prompt tại: {out_path}")
    print(
        "\nBước tiếp theo:\n"
        f"  1. Mở file {out_path}, copy TOÀN BỘ nội dung.\n"
        "  2. Dán vào một cuộc trò chuyện MỚI trên Claude.ai hoặc Claude app.\n"
        "  3. Claude sẽ trả lời bằng một khối JSON (mảng "
        f"{args.n_questions} phần tử). Copy toàn bộ JSON đó, lưu vào 1 "
        "file, ví dụ answer.json.\n"
        "  4. Chạy: python cli.py build --json-input answer.json "
        "--output output/bo_cau_hoi.docx"
    )


def cmd_build(args):
    """Đọc JSON câu hỏi (đã dán về từ Claude.ai), kiểm tra kỹ thuật và
    xuất file Word — hoàn toàn không cần API key."""
    json_text = Path(args.json_input).read_text(encoding="utf-8")
    try:
        questions = extract_json_array(json_text)
    except JsonExtractionError as exc:
        raise SystemExit(f"Lỗi đọc JSON trong {args.json_input}:\n\n{exc}") from exc

    raw_scenario = None
    if args.scenario_file:
        raw_scenario = Path(args.scenario_file).read_text(encoding="utf-8")

    missing_stem_count = 0
    for i, q in enumerate(questions, start=1):
        q["question_number"] = i
        # "Phần thân" do AI tự soạn (đã lọc từ tình huống thô theo đúng
        # hướng dẫn trong prompt) — chỉ dùng --scenario-file làm phương
        # án dự phòng khi AI lỡ không trả về field "stem".
        if not (q.get("stem") or "").strip():
            missing_stem_count += 1
            if raw_scenario:
                q["stem"] = raw_scenario
    if missing_stem_count and not raw_scenario:
        print(
            f"Cảnh báo: {missing_stem_count} câu thiếu \"Phần thân\" (AI "
            "không trả về field \"stem\") và không có --scenario-file để "
            "dùng dự phòng. Nên chạy lại kèm --scenario-file "
            "duong_dan_tinh_huong.txt.",
            file=sys.stderr,
        )

    results = validate_all(questions)
    n_warnings = sum(len(r.warnings) for r in results)
    print(f"Đã nạp {len(questions)} câu. Kiểm tra kỹ thuật tự động: "
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


def cmd_generate(args):
    """Chế độ tự động hoàn toàn — cần API key của provider đã chọn."""
    from mcq_generator import GenerationError, generate_mcq_set
    from mcq_generator.generator import (
        generate_mcq_set_per_question,
        generate_scenario_from_topic,
        refine_raw_scenario,
    )

    reference_knowledge = None
    if args.reference_file:
        try:
            reference_knowledge = load_reference_text(args.reference_file)
        except ReferenceLoadError as exc:
            raise SystemExit(f"Lỗi đọc tài liệu tham chiếu: {exc}") from exc
        print(f"Đã nạp tài liệu tham chiếu: {args.reference_file}")

    if args.per_question_scenario:
        if not args.topic:
            raise SystemExit(
                "--per-question-scenario chỉ dùng được kèm --topic "
                "(mỗi câu cần 1 tình huống riêng do AI tự tạo)."
            )
        blueprint = build_blueprint(args.n_questions, args.categories)
        print(
            f"Đang sinh {len(blueprint)} câu hỏi, MỖI CÂU 1 tình huống riêng "
            f"(chủ đề: {args.topic!r})..."
        )
        try:
            questions, scenarios = generate_mcq_set_per_question(
                args.topic, blueprint=blueprint, provider=args.provider,
                model=args.model, reference_knowledge=reference_knowledge,
                progress_callback=lambda i, t, s: print(f"  [{i}/{t}] {s}"),
            )
        except GenerationError as exc:
            print(f"Lỗi: {exc}", file=sys.stderr)
            raise SystemExit(1) from exc
        raw_scenario = None  # không có 1 tình huống chung — mỗi câu đã tự mang theo trong "stem"
    else:
        if args.topic:
            print(f"Đang nhờ {args.provider} soạn tình huống từ tên bài: {args.topic!r}...")
            try:
                raw_scenario = generate_scenario_from_topic(
                    args.topic, provider=args.provider, model=args.model
                )
            except GenerationError as exc:
                print(f"Lỗi: {exc}", file=sys.stderr)
                raise SystemExit(1) from exc
            print("Tình huống do AI tạo:\n" + raw_scenario + "\n")
        else:
            raw_scenario = _read_text_arg_or_stdin(args.input, "tình huống lâm sàng thô")

        if not args.no_refine:
            print(f"Đang nhờ {args.provider} biên soạn/chuẩn hoá tình huống...")
            try:
                raw_scenario = refine_raw_scenario(
                    raw_scenario, provider=args.provider, model=args.model
                )
            except GenerationError as exc:
                print(f"Lỗi: {exc}", file=sys.stderr)
                raise SystemExit(1) from exc
            print("Tình huống đã chuẩn hoá:\n" + raw_scenario + "\n")

        blueprint = build_blueprint(args.n_questions, args.categories)

        print(f"Đang gọi {args.provider} để sinh {len(blueprint)} câu hỏi...")
        try:
            questions = generate_mcq_set(
                raw_scenario, blueprint=blueprint, provider=args.provider,
                model=args.model, reference_knowledge=reference_knowledge,
            )
        except GenerationError as exc:
            print(f"Lỗi: {exc}", file=sys.stderr)
            raise SystemExit(1) from exc

        # Tự động kiểm tra + tạo bù 1 lượt cho các câu không đạt bảng kiểm.
        results = validate_all(questions)
        missing_blueprint = [blueprint[i] for i, r in enumerate(results) if not r.ok]
        if missing_blueprint:
            print(f"Đang tạo bù {len(missing_blueprint)} câu không đạt bảng kiểm...")
            try:
                extra = generate_mcq_set(
                    raw_scenario, blueprint=missing_blueprint, provider=args.provider,
                    model=args.model, reference_knowledge=reference_knowledge,
                )
                questions = questions + extra
            except GenerationError:
                print("Lượt tạo bù thất bại, dùng số câu đã có.", file=sys.stderr)

    # Tự động loại các câu vẫn không đạt bảng kiểm sau khi đã thử tạo bù.
    results = validate_all(questions)
    passing = [q for q, r in zip(questions, results) if r.ok]
    n_dropped = len(questions) - len(passing)
    for i, q in enumerate(passing, start=1):
        q["question_number"] = i
    questions = passing
    results = validate_all(questions)

    if n_dropped:
        print(f"Đã tự động loại {n_dropped} câu không đạt bảng kiểm 12 tiêu chí.")
    print(f"Còn lại {len(questions)} câu đạt (xem chi tiết trong file .docx).")
    if not questions:
        raise SystemExit("Không còn câu nào đạt sau khi lọc — không có gì để lưu.")

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
    p_prepare.add_argument("--topic", help="Tên bài/chủ đề — nếu có, tạo prompt bước 1 (AI tự soạn tình huống) thay vì đọc --input.")
    p_prepare.add_argument("--n-questions", "-n", type=int, default=10, help="Số lượng câu hỏi muốn tạo (mặc định 10).")
    p_prepare.add_argument("--categories", nargs="+", choices=CATEGORY_KEYS, default=None, help=f"Miền năng lực muốn hỏi, cách nhau bởi khoảng trắng. Mặc định = tất cả. Các mã: {CATEGORY_HELP}")
    p_prepare.add_argument("--reference-file", help="File .txt hoặc .pdf chứa tài liệu tham chiếu chuẩn (ví dụ Hướng dẫn chẩn đoán & điều trị của Bộ Y tế) — model sẽ bám sát tài liệu này khi soạn câu hỏi.")
    p_prepare.add_argument("--refine", action="store_true", help="Chỉ tạo prompt bước CHUẨN HOÁ tình huống (không phải prompt tạo câu hỏi) — dùng --input để chỉ tình huống cần chuẩn hoá.")
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
    p_generate.add_argument("--input", "-i", help="File .txt chứa tình huống thô. Bỏ qua để đọc từ stdin (bỏ qua luôn nếu dùng --topic).")
    p_generate.add_argument("--topic", help="Tên bài/chủ đề — nếu có, AI tự soạn tình huống thay vì đọc --input.")
    p_generate.add_argument("--output", "-o", default="output/bo_cau_hoi.docx", help="File .docx đầu ra.")
    p_generate.add_argument("--json-output", help="Lưu thêm bản JSON thô tại đây (tuỳ chọn).")
    p_generate.add_argument("--title", default="Tình huống lâm sàng", help="Tiêu đề phụ trong file Word.")
    p_generate.add_argument("--provider", default="gemini", choices=["gemini", "anthropic", "openai", "openrouter", "cerebras", "groq", "mistral", "github"], help="Nhà cung cấp AI (mặc định: gemini).")
    p_generate.add_argument("--model", default=None, help="Tên model cụ thể (mặc định theo provider).")
    p_generate.add_argument("--n-questions", "-n", type=int, default=10, help="Số lượng câu hỏi muốn tạo (mặc định 10).")
    p_generate.add_argument("--categories", nargs="+", choices=CATEGORY_KEYS, default=None, help=f"Miền năng lực muốn hỏi, cách nhau bởi khoảng trắng. Mặc định = tất cả. Các mã: {CATEGORY_HELP}")
    p_generate.add_argument("--per-question-scenario", action="store_true", help="Mỗi câu hỏi dùng 1 tình huống riêng do AI tự tạo (chỉ dùng kèm --topic).")
    p_generate.add_argument("--no-refine", action="store_true", help="Bỏ qua bước AI tự biên soạn/chuẩn hoá tình huống trước khi tạo câu hỏi (mặc định có bật bước này).")
    p_generate.add_argument("--reference-file", help="File .txt hoặc .pdf chứa tài liệu tham chiếu chuẩn (ví dụ Hướng dẫn chẩn đoán & điều trị của Bộ Y tế) — model sẽ bám sát tài liệu này khi soạn câu hỏi.")
    p_generate.set_defaults(func=cmd_generate)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
