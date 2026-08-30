#!/usr/bin/env python3
"""
gui_app.py
-----------
Ứng dụng giao diện cửa sổ (desktop app) — không cần dòng lệnh.

Có 2 cách lấy câu hỏi:
  1. "Tự động qua API" — app tự gọi Gemini/Anthropic/OpenAI/OpenRouter/
     Cerebras/Groq bằng API key bạn cung cấp.
  2. "Thủ công (dán vào Claude.ai/Gemini/ChatGPT)" — KHÔNG cần API key.
     App tạo sẵn prompt, bạn tự dán vào cửa sổ chat bạn đang có (tài
     khoản thường, không phải API), rồi dán kết quả AI trả về ngược lại
     vào app để app tự kiểm tra kỹ thuật + xuất file Word.

     Lưu ý: đây LÀ cách hợp lệ duy nhất để "dùng tài khoản Claude/Gemini
     thường thay vì API" — app không thể tự động đăng nhập hộ bạn vào
     Claude.ai/Gemini để gửi tin nhắn thay bạn, vì các trang đó không hỗ
     trợ việc này cho ứng dụng bên ngoài (và làm chui qua phiên đăng
     nhập web sẽ vi phạm điều khoản dịch vụ của họ).

Cách chạy:
    python gui_app.py
(Trên Windows có thể double-click file run_windows.bat;
 trên Mac double-click file run_mac.command — xem README.md)
"""

from __future__ import annotations

import sys
import threading
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, scrolledtext, simpledialog, ttk
except ImportError:
    print(
        "Thiếu tkinter (thư viện giao diện đi kèm Python).\n"
        "- Windows/Mac: cài lại Python từ python.org, tkinter có sẵn.\n"
        "- Ubuntu/Debian: chạy 'sudo apt install python3-tk' rồi thử lại."
    )
    sys.exit(1)

from mcq_generator import (
    QUESTION_CATEGORIES,
    build_blueprint,
    build_manual_prompt,
    build_manual_refine_scenario_prompt,
    build_manual_scenario_prompt,
    export_to_docx,
    extract_json_array,
    validate_all,
    validate_question,
)
from mcq_generator.json_utils import JsonExtractionError
from mcq_generator.reference_loader import ReferenceLoadError, load_reference_text
from mcq_generator.config import clear_api_key, load_api_key, save_api_key
from mcq_generator.generator import (
    GenerationError,
    generate_mcq_set,
    generate_mcq_set_per_question,
    generate_scenario_from_topic,
    refine_raw_scenario,
)

APP_TITLE = "Công cụ soạn câu hỏi MCQ lâm sàng theo năng lực"

PROVIDER_LABELS = {
    "gemini": "Google Gemini",
    "anthropic": "Anthropic Claude",
    "openai": "OpenAI (ChatGPT)",
    "openrouter": "OpenRouter (miễn phí)",
    "cerebras": "Cerebras (siêu nhanh)",
    "groq": "Groq (siêu nhanh, miễn phí)",
    "mistral": "Mistral AI",
    "github": "GitHub Models",
}
API_KEY_URL = {
    "gemini": "https://aistudio.google.com/apikey",
    "anthropic": "https://console.anthropic.com/settings/keys",
    "openai": "https://platform.openai.com/api-keys",
    "openrouter": "https://openrouter.ai/keys",
    "cerebras": "https://cloud.cerebras.ai/",
    "groq": "https://console.groq.com/keys",
    "mistral": "https://console.mistral.ai/api-keys",
    "github": "https://github.com/settings/tokens",
}

MIN_QUESTIONS = 1
MAX_QUESTIONS = 20
DEFAULT_QUESTIONS = 10


class ResultsReviewWindow(tk.Toplevel):
    """Cửa sổ xem trước toàn bộ bộ câu hỏi trong app — người dùng đọc/
    duyệt tại đây; xuất ra file Word là hành động RIÊNG, chỉ xảy ra khi
    bấm nút, không tự động xuất ngay sau khi tạo xong."""

    def __init__(self, parent, title_text, questions, results, on_export):
        super().__init__(parent)
        self.title("Xem trước bộ câu hỏi")
        self.geometry("880x760")
        self._on_export = on_export

        pad = {"padx": 10, "pady": 6}

        header = ttk.Label(self, text=title_text, font=("", 11, "bold"))
        header.pack(anchor="w", **pad)

        self.preview_box = scrolledtext.ScrolledText(self, wrap="word")
        self.preview_box.pack(fill="both", expand=True, padx=10)
        self.preview_box.insert(tk.END, self._format_all(questions, results))
        self.preview_box.config(state="disabled")

        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", padx=10, pady=10)
        ttk.Button(button_frame, text="Đóng", command=self.destroy).pack(side="right")
        ttk.Button(
            button_frame, text="Xuất ra file Word...", command=self._handle_export
        ).pack(side="right", padx=(0, 8))

    @staticmethod
    def _format_all(questions, results):
        results_by_number = {r.question_number: r for r in results}
        blocks = []
        for q in questions:
            n = q.get("question_number", "?")
            r = results_by_number.get(n)
            lines = [
                f"Câu {n}. {q.get('competency_code', '')} -- {q.get('competency_name', '')}",
                f"Mức độ tư duy: {q.get('thinking_level', '')}",
                "",
                "Phần thân:",
                q.get("stem", ""),
                "",
                q.get("lead_in", ""),
            ]
            options = q.get("options", {})
            for letter in ["A", "B", "C", "D"]:
                lines.append(f"{letter}. {options.get(letter, '')}")
            lines.append(f"Đáp án: {q.get('correct_answer', '')}")
            if q.get("rationale"):
                lines.append(f"Giải thích: {q['rationale']}")
            if r and r.warnings:
                lines.append("Cảnh báo kỹ thuật:")
                for w in r.warnings:
                    lines.append(f"  - {w}")
            blocks.append("\n".join(lines))
        return "\n\n" + ("\n\n" + "-" * 70 + "\n\n").join(blocks)

    def _handle_export(self):
        self._on_export()


class CopyPasteDialog(tk.Toplevel):
    """Cửa sổ dùng chung cho chế độ thủ công: hiện prompt để copy, có ô
    để dán kết quả AI trả về, rồi gọi on_submit(pasted_text) khi bấm nút."""

    def __init__(self, parent, title, instructions, prompt_text, submit_label, on_submit, on_cancel):
        super().__init__(parent)
        self.title(title)
        self.geometry("760x620")
        self._on_submit = on_submit
        self._on_cancel = on_cancel
        self.protocol("WM_DELETE_WINDOW", self._handle_cancel)

        pad = {"padx": 10, "pady": 6}

        ttk.Label(self, text=instructions, wraplength=720, justify="left").pack(
            anchor="w", **pad
        )

        ttk.Label(self, text="1. Copy nội dung dưới đây:").pack(anchor="w", padx=10)
        prompt_box = scrolledtext.ScrolledText(self, height=14, wrap="word")
        prompt_box.pack(fill="both", expand=True, padx=10)
        prompt_box.insert(tk.END, prompt_text)
        prompt_box.config(state="disabled")

        copy_btn = ttk.Button(
            self, text="Copy vào clipboard",
            command=lambda: self._copy_to_clipboard(prompt_text),
        )
        copy_btn.pack(anchor="w", padx=10, pady=(4, 10))

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=10, pady=4)

        ttk.Label(
            self, text="2. Dán nội dung AI trả về vào ô bên dưới, rồi bấm nút:"
        ).pack(anchor="w", padx=10)
        self.result_box = scrolledtext.ScrolledText(self, height=10, wrap="word")
        self.result_box.pack(fill="both", expand=True, padx=10, pady=(0, 6))

        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(button_frame, text="Huỷ", command=self._handle_cancel).pack(side="right")
        ttk.Button(button_frame, text=submit_label, command=self._handle_submit).pack(
            side="right", padx=(0, 8)
        )

    def _copy_to_clipboard(self, text):
        self.clipboard_clear()
        self.clipboard_append(text)

    def _handle_submit(self):
        text = self.result_box.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning(APP_TITLE, "Vui lòng dán nội dung AI trả về trước.", parent=self)
            return
        self.destroy()
        self._on_submit(text)

    def _handle_cancel(self):
        self.destroy()
        if self._on_cancel:
            self._on_cancel()


class MCQApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("940x860")
        self.minsize(760, 640)

        self.input_source_var = tk.StringVar(value="api")  # api | manual
        self.provider_var = tk.StringVar(value="gemini")
        self.input_mode_var = tk.StringVar(value="existing")  # existing | topic
        self.n_questions_var = tk.StringVar(value=str(DEFAULT_QUESTIONS))
        self.category_vars: dict[str, tk.BooleanVar] = {
            c.key: tk.BooleanVar(value=True) for c in QUESTION_CATEGORIES
        }
        self.per_question_scenario_var = tk.BooleanVar(value=False)

        self._last_questions: list[dict] | None = None
        self._last_scenario: str = ""
        self._reference_knowledge: str | None = None
        self._reference_knowledge_filename: str | None = None

        self._build_menu()
        self._build_widgets()
        self._on_input_mode_change()
        self._on_input_source_change()

    # ---------- Giao diện ----------

    def _build_menu(self):
        menubar = tk.Menu(self)
        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(
            label="Cài đặt / đổi API Key...", command=self._prompt_api_key
        )
        settings_menu.add_command(
            label="Xoá API Key đã lưu (nhà cung cấp đang chọn)",
            command=self._clear_api_key,
        )
        menubar.add_cascade(label="Cài đặt", menu=settings_menu)

        reference_menu = tk.Menu(menubar, tearoff=0)
        reference_menu.add_command(
            label="Nạp tài liệu tham chiếu chuẩn (.txt)...",
            command=self._load_reference_knowledge,
        )
        reference_menu.add_command(
            label="Xoá tài liệu tham chiếu đã nạp",
            command=self._clear_reference_knowledge,
        )
        menubar.add_cascade(label="Tài liệu tham chiếu", menu=reference_menu)

        self.config(menu=menubar)

    def _build_widgets(self):
        pad = {"padx": 10, "pady": 6}

        # --- Cách lấy câu hỏi ---
        source_frame = ttk.Frame(self)
        source_frame.pack(fill="x", **pad)
        ttk.Label(source_frame, text="Cách lấy câu hỏi:").pack(side="left")
        ttk.Radiobutton(
            source_frame, text="Tự động qua API", value="api",
            variable=self.input_source_var, command=self._on_input_source_change,
        ).pack(side="left", padx=(10, 0))
        ttk.Radiobutton(
            source_frame,
            text="Thủ công (dán vào Claude.ai / Gemini / ChatGPT — không cần API key)",
            value="manual", variable=self.input_source_var,
            command=self._on_input_source_change,
        ).pack(side="left", padx=(10, 0))

        # --- Nhà cung cấp AI (chỉ dùng khi chọn "Tự động qua API") ---
        self.provider_frame = ttk.Frame(self)
        self.provider_frame.pack(fill="x", **pad)
        ttk.Label(self.provider_frame, text="Nhà cung cấp AI:").pack(side="left")
        self.provider_radios = []
        for value, label in PROVIDER_LABELS.items():
            rb = ttk.Radiobutton(
                self.provider_frame, text=label, value=value, variable=self.provider_var,
            )
            rb.pack(side="left", padx=(10, 0))
            self.provider_radios.append(rb)

        self.model_frame = ttk.Frame(self)
        self.model_frame.pack(fill="x", **pad)
        ttk.Label(self.model_frame, text="Model (để trống = dùng mặc định):").pack(side="left")
        self.model_entry = ttk.Entry(self.model_frame)
        self.model_entry.pack(side="left", fill="x", expand=True, padx=(8, 0))

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=10, pady=4)

        # --- Nguồn tình huống ---
        mode_frame = ttk.Frame(self)
        mode_frame.pack(fill="x", **pad)
        ttk.Label(mode_frame, text="Nguồn tình huống:").pack(side="left")
        ttk.Radiobutton(
            mode_frame, text="Dán tình huống có sẵn", value="existing",
            variable=self.input_mode_var, command=self._on_input_mode_change,
        ).pack(side="left", padx=(10, 0))
        ttk.Radiobutton(
            mode_frame, text="Nhập tên bài — AI tự tạo tình huống", value="topic",
            variable=self.input_mode_var, command=self._on_input_mode_change,
        ).pack(side="left", padx=(10, 0))

        self.topic_frame = ttk.Frame(self)
        ttk.Label(self.topic_frame, text="Tên bài / chủ đề:").pack(side="left")
        self.topic_entry = ttk.Entry(self.topic_frame)
        self.topic_entry.pack(side="left", fill="x", expand=True, padx=(8, 0))
        self.topic_frame.pack(fill="x", padx=10, pady=(0, 6))

        self.per_question_frame = ttk.Frame(self)
        self.per_question_check = ttk.Checkbutton(
            self.per_question_frame,
            text=(
                "Mỗi câu hỏi dùng 1 tình huống lâm sàng RIÊNG (không dùng chung "
                "1 tình huống cho cả bộ) — chỉ áp dụng với 'AI tự tạo tình "
                "huống' + 'Tự động qua API'"
            ),
            variable=self.per_question_scenario_var,
        )
        self.per_question_check.pack(side="left")
        self.per_question_frame.pack(fill="x", padx=10, pady=(0, 6))

        self.reference_label = ttk.Label(
            self, text="Tài liệu tham chiếu: (chưa nạp — xem menu \"Tài liệu tham chiếu\")",
            foreground="gray",
        )
        self.reference_label.pack(anchor="w", padx=10, pady=(0, 6))

        self.scenario_label = ttk.Label(
            self, text="Dán tình huống lâm sàng thô vào ô bên dưới:"
        )
        self.scenario_label.pack(anchor="w", **pad)

        self.scenario_box = scrolledtext.ScrolledText(self, height=11, wrap="word")
        self.scenario_box.pack(fill="both", expand=True, padx=10)

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=10, pady=4)

        # --- Số lượng câu hỏi + miền năng lực ---
        n_frame = ttk.Frame(self)
        n_frame.pack(fill="x", **pad)
        ttk.Label(n_frame, text="Số lượng câu hỏi:").pack(side="left")
        self.n_questions_spin = ttk.Spinbox(
            n_frame, from_=MIN_QUESTIONS, to=MAX_QUESTIONS, width=5,
            textvariable=self.n_questions_var,
        )
        self.n_questions_spin.pack(side="left", padx=(8, 0))

        cat_label = ttk.Label(self, text="Miền năng lực muốn hỏi (chọn ít nhất 1):")
        cat_label.pack(anchor="w", padx=10)
        cat_frame = ttk.Frame(self)
        cat_frame.pack(fill="x", padx=10, pady=(0, 6))
        for c in QUESTION_CATEGORIES:
            ttk.Checkbutton(
                cat_frame, text=c.label, variable=self.category_vars[c.key],
            ).pack(side="left", padx=(0, 14))

        title_frame = ttk.Frame(self)
        title_frame.pack(fill="x", **pad)
        ttk.Label(title_frame, text="Tiêu đề ca bệnh (hiện trong file Word):").pack(side="left")
        self.title_entry = ttk.Entry(title_frame)
        self.title_entry.insert(0, "Tình huống lâm sàng")
        self.title_entry.pack(side="left", fill="x", expand=True, padx=(8, 0))

        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", **pad)
        self.generate_btn = ttk.Button(
            button_frame, text="Tạo bộ câu hỏi", command=self._on_generate_click
        )
        self.generate_btn.pack(side="left")

        self.progress = ttk.Progressbar(button_frame, mode="indeterminate")
        self.progress.pack(side="left", fill="x", expand=True, padx=10)

        self.status_label = ttk.Label(self, text="Sẵn sàng.", foreground="gray")
        self.status_label.pack(anchor="w", padx=10)

        result_label = ttk.Label(self, text="Kết quả / cảnh báo kỹ thuật:")
        result_label.pack(anchor="w", **pad)

        self.result_box = scrolledtext.ScrolledText(
            self, height=8, wrap="word", state="disabled", background="#f4f4f4"
        )
        self.result_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _on_input_mode_change(self):
        if self.input_mode_var.get() == "topic":
            self.scenario_label.config(
                text="Tình huống sẽ được AI tạo ra ở đây (có thể sửa lại trước khi lưu):"
            )
            self.scenario_box.delete("1.0", tk.END)
            self.scenario_box.config(state="disabled", background="#eeeeee")
        else:
            self.topic_entry.delete(0, tk.END)
            self.scenario_label.config(
                text="Dán tình huống lâm sàng thô vào ô bên dưới:"
            )
            self.scenario_box.config(state="normal", background="white")
        self._update_per_question_availability()

    def _on_input_source_change(self):
        is_manual = self.input_source_var.get() == "manual"
        state = "disabled" if is_manual else "normal"
        for rb in self.provider_radios:
            rb.config(state=state)
        self.model_entry.config(state=state)
        if is_manual:
            self.generate_btn.config(text="Bắt đầu (chế độ thủ công)")
        else:
            self.generate_btn.config(text="Tạo bộ câu hỏi")
        self._update_per_question_availability()

    def _update_per_question_availability(self):
        """Tính năng 'mỗi câu 1 tình huống riêng' chỉ hợp lý khi nguồn
        tình huống là 'AI tự tạo' VÀ đang dùng API tự động (chế độ thủ
        công không tự động hoá được vòng lặp gọi API nhiều lần)."""
        available = (
            self.input_mode_var.get() == "topic"
            and self.input_source_var.get() == "api"
        )
        if available:
            self.per_question_check.config(state="normal")
        else:
            self.per_question_scenario_var.set(False)
            self.per_question_check.config(state="disabled")

    # ---------- Tài liệu tham chiếu chuẩn ----------

    def _load_reference_knowledge(self):
        path = filedialog.askopenfilename(
            title="Chọn file tài liệu tham chiếu (.txt hoặc .pdf)",
            filetypes=[
                ("Text hoặc PDF", "*.txt *.pdf"),
                ("Text file", "*.txt"),
                ("PDF file", "*.pdf"),
                ("Tất cả file", "*.*"),
            ],
        )
        if not path:
            return
        try:
            content = load_reference_text(path)
        except ReferenceLoadError as exc:
            messagebox.showerror(APP_TITLE, f"Không đọc được file:\n{exc}")
            return
        if not content.strip():
            messagebox.showwarning(APP_TITLE, "File rỗng, không có gì để nạp.")
            return
        self._reference_knowledge = content
        self._reference_knowledge_filename = Path(path).name
        self.reference_label.config(
            text=f"Tài liệu tham chiếu: đã nạp \"{self._reference_knowledge_filename}\" "
            f"({len(content):,} ký tự)",
            foreground="green",
        )

    def _clear_reference_knowledge(self):
        self._reference_knowledge = None
        self._reference_knowledge_filename = None
        self.reference_label.config(
            text="Tài liệu tham chiếu: (chưa nạp — xem menu \"Tài liệu tham chiếu\")",
            foreground="gray",
        )

    # ---------- API key ----------

    def _current_provider(self) -> str:
        return self.provider_var.get()

    def _ensure_api_key(self, prompt_if_missing: bool = True) -> str | None:
        provider = self._current_provider()
        key = load_api_key(provider)
        if key or not prompt_if_missing:
            return key
        return self._prompt_api_key()

    def _prompt_api_key(self) -> str | None:
        provider = self._current_provider()
        label = PROVIDER_LABELS[provider]
        url = API_KEY_URL[provider]
        key = simpledialog.askstring(
            f"Nhập API Key cho {label}",
            f"Dán API key {label} của bạn vào đây.\n"
            f"Lấy key tại: {url}\n"
            "Key sẽ được lưu trên máy này để dùng cho các lần sau.",
            show="*",
            parent=self,
        )
        if key and key.strip():
            save_api_key(key.strip(), provider=provider)
            self._set_status(f"Đã lưu API key cho {label}.", "green")
            return key.strip()
        return None

    def _clear_api_key(self):
        provider = self._current_provider()
        clear_api_key(provider=provider)
        messagebox.showinfo(
            APP_TITLE,
            f"Đã xoá API key đã lưu cho {PROVIDER_LABELS[provider]} trên máy này.",
        )

    # ---------- Hành động chính ----------

    def _set_status(self, text: str, color: str = "gray"):
        self.status_label.config(text=text, foreground=color)

    def _set_result_text(self, text: str):
        self.result_box.config(state="normal")
        self.result_box.delete("1.0", tk.END)
        self.result_box.insert(tk.END, text)
        self.result_box.config(state="disabled")

    def _fill_scenario_box(self, scenario: str):
        was_disabled = str(self.scenario_box.cget("state")) == "disabled"
        self.scenario_box.config(state="normal")
        self.scenario_box.delete("1.0", tk.END)
        self.scenario_box.insert(tk.END, scenario)
        if was_disabled:
            self.scenario_box.config(state="disabled", background="#eeeeee")

    def _selected_categories(self) -> list[str]:
        return [key for key, var in self.category_vars.items() if var.get()]

    def _read_common_inputs(self):
        """Đọc + validate các input dùng chung cho cả 2 chế độ (API/thủ
        công). Trả về None nếu có lỗi (đã hiện cảnh báo)."""
        mode = self.input_mode_var.get()
        if mode == "existing":
            scenario_text = self.scenario_box.get("1.0", tk.END).strip()
            if not scenario_text:
                messagebox.showwarning(APP_TITLE, "Vui lòng dán tình huống lâm sàng trước.")
                return None
            topic = None
        else:
            topic = self.topic_entry.get().strip()
            if not topic:
                messagebox.showwarning(APP_TITLE, "Vui lòng nhập tên bài / chủ đề trước.")
                return None
            scenario_text = None

        try:
            n_questions = int(self.n_questions_var.get())
            if not (MIN_QUESTIONS <= n_questions <= MAX_QUESTIONS):
                raise ValueError
        except ValueError:
            messagebox.showwarning(
                APP_TITLE,
                f"Số lượng câu hỏi phải là số nguyên từ {MIN_QUESTIONS} đến {MAX_QUESTIONS}.",
            )
            return None

        categories = self._selected_categories()
        if not categories:
            messagebox.showwarning(APP_TITLE, "Vui lòng chọn ít nhất 1 miền năng lực.")
            return None

        return mode, scenario_text, topic, n_questions, categories

    def _on_generate_click(self):
        parsed = self._read_common_inputs()
        if parsed is None:
            return
        mode, scenario_text, topic, n_questions, categories = parsed

        if self.input_source_var.get() == "manual":
            self._set_result_text("")
            self._start_manual_flow(mode, scenario_text, topic, n_questions, categories)
            return

        provider = self._current_provider()
        api_key = self._ensure_api_key(prompt_if_missing=True)
        if not api_key:
            messagebox.showwarning(APP_TITLE, "Cần có API key để tạo câu hỏi tự động.")
            return

        model = self.model_entry.get().strip() or None
        per_question = self.per_question_scenario_var.get() and mode == "topic"

        self.generate_btn.config(state="disabled")
        self.progress.start(12)
        self._set_result_text("")

        if per_question:
            thread = threading.Thread(
                target=self._generate_worker_per_question,
                args=(topic, n_questions, categories, provider, api_key, model),
                daemon=True,
            )
        else:
            thread = threading.Thread(
                target=self._generate_worker,
                args=(mode, scenario_text, topic, n_questions, categories, provider, api_key, model),
                daemon=True,
            )
        thread.start()

    def _generate_worker(
        self, mode, scenario_text, topic, n_questions, categories, provider, api_key, model,
    ):
        try:
            if mode == "topic":
                self.after(
                    0, self._set_status,
                    f"Đang nhờ {PROVIDER_LABELS[provider]} soạn tình huống từ tên bài...",
                    "blue",
                )
                scenario_text = generate_scenario_from_topic(
                    topic, provider=provider, api_key=api_key, model=model
                )
                self.after(0, self._fill_scenario_box, scenario_text)

            # Bước riêng: BIÊN SOẠN LẠI (chuẩn hoá hình thức/cấu trúc,
            # gộp bớt trùng lặp) tình huống trước khi dùng làm nguồn tạo
            # câu hỏi — khác với bước LỌC dữ kiện cho từng câu (nằm
            # trong generate_mcq_set). Không bỏ sót dữ kiện lâm sàng.
            self.after(
                0, self._set_status,
                f"Đang nhờ {PROVIDER_LABELS[provider]} biên soạn/chuẩn hoá tình huống...",
                "blue",
            )
            scenario_text = refine_raw_scenario(
                scenario_text, provider=provider, api_key=api_key, model=model
            )
            self.after(0, self._fill_scenario_box, scenario_text)

            blueprint = build_blueprint(n_questions, categories)

            self.after(
                0, self._set_status,
                f"Đang gọi {PROVIDER_LABELS[provider]} để soạn {n_questions} câu hỏi... "
                "(vài chục giây)",
                "blue",
            )
            questions = generate_mcq_set(
                scenario_text, blueprint=blueprint, provider=provider,
                api_key=api_key, model=model,
                reference_knowledge=self._reference_knowledge,
            )

            # Tự động kiểm tra bảng kiểm 12 tiêu chí; nếu có câu không
            # đạt, thử tạo bù thêm 1 lượt (dùng lại đúng các mã năng
            # lực/mức độ tư duy của những câu không đạt) trước khi giao
            # cho _on_generate_success lọc và chốt danh sách cuối cùng.
            results = validate_all(questions)
            missing_blueprint = [
                blueprint[i] for i, r in enumerate(results) if not r.ok
            ]
            if missing_blueprint:
                self.after(
                    0, self._set_status,
                    f"Đang tạo bù {len(missing_blueprint)} câu không đạt bảng kiểm...",
                    "blue",
                )
                try:
                    extra_questions = generate_mcq_set(
                        scenario_text, blueprint=missing_blueprint, provider=provider,
                        api_key=api_key, model=model,
                        reference_knowledge=self._reference_knowledge,
                    )
                    questions = questions + extra_questions
                except GenerationError:
                    pass  # bỏ qua lượt tạo bù nếu lỗi, vẫn dùng số câu đã có

            results = validate_all(questions)
            self.after(0, self._on_generate_success, scenario_text, questions, results)
        except (GenerationError, ValueError) as exc:
            self.after(0, self._on_generate_error, str(exc))
        except Exception:  # noqa: BLE001 - hiện lỗi đầy đủ cho người dùng debug
            self.after(0, self._on_generate_error, traceback.format_exc())

    def _generate_worker_per_question(
        self, topic, n_questions, categories, provider, api_key, model,
    ):
        try:
            blueprint = build_blueprint(n_questions, categories)

            def progress_callback(idx, total, status_text):
                self.after(0, self._set_status, status_text, "blue")

            questions, scenarios = generate_mcq_set_per_question(
                topic, blueprint=blueprint, provider=provider, api_key=api_key,
                model=model, reference_knowledge=self._reference_knowledge,
                progress_callback=progress_callback,
            )
            # Không có 1 tình huống chung để hiện trong docx (mỗi câu có
            # tình huống riêng, đã nằm sẵn trong "stem" của câu đó) —
            # để trống scenario tổng, docx_export sẽ tự bỏ qua khối
            # "Nguồn tình huống thô" chung.
            self.after(0, self._fill_scenario_box, "\n\n---\n\n".join(scenarios))
            results = validate_all(questions)
            self.after(0, self._on_generate_success, None, questions, results)
        except (GenerationError, ValueError) as exc:
            self.after(0, self._on_generate_error, str(exc))
        except Exception:  # noqa: BLE001
            self.after(0, self._on_generate_error, traceback.format_exc())

    # ---------- Chế độ thủ công (không cần API key) ----------

    def _start_manual_flow(self, mode, scenario_text, topic, n_questions, categories):
        self.generate_btn.config(state="disabled")
        blueprint = build_blueprint(n_questions, categories)
        total_steps = 3 if mode == "topic" else 2

        def reset_ui():
            self.generate_btn.config(state="normal")
            self._set_status("Đã huỷ chế độ thủ công.", "gray")

        if mode == "topic":
            scenario_prompt = build_manual_scenario_prompt(topic)
            self._set_status("Chờ bạn dán tình huống từ Claude.ai/Gemini/ChatGPT...", "blue")
            CopyPasteDialog(
                self,
                title=f"Bước 1/{total_steps} — Tạo tình huống",
                instructions=(
                    "Copy nội dung bên dưới và dán vào MỘT CUỘC TRÒ CHUYỆN MỚI trên "
                    "Claude.ai, Gemini hoặc ChatGPT (dùng tài khoản thường của bạn, "
                    "không cần API key). Sau khi AI trả lời bằng 1 đoạn tình huống, "
                    "copy đoạn đó và dán vào ô bên dưới."
                ),
                prompt_text=scenario_prompt,
                submit_label=f"Tiếp tục → Bước 2/{total_steps}",
                on_submit=lambda scenario_result: self._on_manual_scenario_obtained(
                    scenario_result, blueprint, total_steps
                ),
                on_cancel=reset_ui,
            )
        else:
            self._on_manual_scenario_obtained(scenario_text, blueprint, total_steps)

    def _on_manual_scenario_obtained(self, scenario_text: str, blueprint, total_steps: int):
        """Bước RIÊNG: biên soạn lại (chuẩn hoá hình thức/cấu trúc, gộp
        bớt trùng lặp) tình huống trước khi dùng làm nguồn tạo câu hỏi
        — khác với bước lọc dữ kiện cho từng câu (nằm trong prompt tạo
        câu hỏi ở bước tiếp theo)."""
        refine_prompt = build_manual_refine_scenario_prompt(scenario_text)
        step_num = total_steps - 1  # bước áp chót, ngay trước "Tạo câu hỏi"

        def reset_ui():
            self.generate_btn.config(state="normal")
            self._set_status("Đã huỷ chế độ thủ công.", "gray")

        self._set_status("Chờ bạn dán tình huống đã chuẩn hoá...", "blue")
        CopyPasteDialog(
            self,
            title=f"Bước {step_num}/{total_steps} — Chuẩn hoá tình huống",
            instructions=(
                "Copy nội dung bên dưới và dán vào MỘT CUỘC TRÒ CHUYỆN MỚI trên "
                "Claude.ai, Gemini hoặc ChatGPT. AI sẽ biên soạn lại tình huống cho "
                "chuẩn (sắp xếp đúng trình tự, viết rõ ràng hơn) mà không bỏ sót dữ "
                "kiện nào. Copy đoạn tình huống đã biên soạn lại và dán vào ô bên dưới."
            ),
            prompt_text=refine_prompt,
            submit_label=f"Tiếp tục → Bước {total_steps}/{total_steps}",
            on_submit=lambda refined: self._on_manual_scenario_ready(
                refined, blueprint, total_steps
            ),
            on_cancel=reset_ui,
        )

    def _on_manual_scenario_ready(self, scenario_text: str, blueprint, total_steps: int = 2):
        self._fill_scenario_box(scenario_text)
        self._last_scenario = scenario_text
        prompt_text = build_manual_prompt(
            scenario_text, blueprint=blueprint, reference_knowledge=self._reference_knowledge
        )

        def reset_ui():
            self.generate_btn.config(state="normal")
            self._set_status("Đã huỷ chế độ thủ công.", "gray")

        self._set_status("Chờ bạn dán JSON câu hỏi từ Claude.ai/Gemini/ChatGPT...", "blue")
        CopyPasteDialog(
            self,
            title=f"Bước {total_steps}/{total_steps} — Tạo câu hỏi",
            instructions=(
                "Copy nội dung bên dưới và dán vào MỘT CUỘC TRÒ CHUYỆN MỚI trên "
                "Claude.ai, Gemini hoặc ChatGPT. AI sẽ trả lời bằng một khối JSON "
                "— copy TOÀN BỘ JSON đó (bỏ phần ```json ở đầu/cuối nếu có) và dán "
                "vào ô bên dưới."
            ),
            prompt_text=prompt_text,
            submit_label="Xử lý JSON này",
            on_submit=self._on_manual_json_ready,
            on_cancel=reset_ui,
        )

    def _on_manual_json_ready(self, json_text: str):
        try:
            questions = extract_json_array(json_text)
        except JsonExtractionError as exc:
            self.generate_btn.config(state="normal")
            self._on_generate_error(str(exc))
            return

        # "Phần thân" do AI tự soạn (đã lọc từ tình huống thô theo đúng
        # hướng dẫn trong prompt) — chỉ dùng nguyên văn tình huống làm
        # phương án dự phòng khi AI lỡ không trả về field "stem".
        for i, q in enumerate(questions, start=1):
            q["question_number"] = i
            if not (q.get("stem") or "").strip():
                q["stem"] = self._last_scenario

        results = validate_all(questions)
        self._on_generate_success(self._last_scenario, questions, results)

    # ---------- Xử lý kết quả chung cho cả 2 chế độ ----------

    def _on_generate_error(self, message: str):
        self.progress.stop()
        self.generate_btn.config(state="normal")
        self._set_status("Có lỗi xảy ra.", "red")
        self._set_result_text(message)
        messagebox.showerror(APP_TITLE, f"Không tạo được câu hỏi:\n\n{message[:500]}")

    def _on_generate_success(self, scenario: str | None, questions: list[dict], results):
        self.progress.stop()
        self.generate_btn.config(state="normal")

        # Tự động loại các câu không đạt bảng kiểm 12 tiêu chí (heuristic
        # + tự chấm của model) — chỉ giữ lại câu đạt (result.ok).
        passing_questions = [q for q, r in zip(questions, results) if r.ok]
        n_dropped = len(questions) - len(passing_questions)

        for i, q in enumerate(passing_questions, start=1):
            q["question_number"] = i
        final_results = validate_all(passing_questions)  # nên toàn "Đạt"

        self._last_questions = passing_questions
        self._last_scenario = scenario or ""

        if n_dropped:
            status_text = (
                f"Đã tạo {len(questions)} câu, tự động loại {n_dropped} câu "
                f"không đạt bảng kiểm — còn lại {len(passing_questions)} câu."
            )
            status_color = "orange" if passing_questions else "red"
        else:
            status_text = f"Đã tạo {len(passing_questions)} câu, tất cả đều đạt bảng kiểm."
            status_color = "green"
        self._set_status(status_text, status_color)

        lines = [status_text, ""]
        if n_dropped:
            lines.append("Chi tiết các câu đã bị loại (trước khi đánh lại số thứ tự):")
            for q, r in zip(questions, results):
                if not r.ok:
                    lines.append(f"Câu gốc #{q.get('question_number', '?')}:")
                    for w in r.warnings:
                        lines.append(f"   - {w}")
        else:
            lines.append(
                "Không phát hiện lỗi kỹ thuật tự động nào ở bất kỳ câu nào. "
                "Vẫn nên đọc lại nội dung y khoa trước khi dùng chính thức."
            )
        self._set_result_text("\n".join(lines))

        if not passing_questions:
            messagebox.showwarning(
                APP_TITLE,
                "Tất cả câu hỏi đều không đạt bảng kiểm 12 tiêu chí sau khi "
                "tự động lọc — không có gì để lưu. Thử lại, hoặc nới lỏng "
                "miền năng lực/số lượng câu hỏi.",
            )
            return

        # Hiện kết quả NGAY TRONG APP để xem/duyệt trước — xuất ra file
        # Word là hành động riêng, chỉ xảy ra khi bấm nút trong cửa sổ
        # xem trước, không tự động lưu file ngay sau khi tạo xong.
        ResultsReviewWindow(
            self,
            title_text=status_text,
            questions=passing_questions,
            results=final_results,
            on_export=self._save_docx_dialog,
        )

    def _save_docx_dialog(self):
        if not self._last_questions:
            return
        path = filedialog.asksaveasfilename(
            title="Lưu bộ câu hỏi",
            defaultextension=".docx",
            filetypes=[("Word Document", "*.docx")],
            initialfile="bo_cau_hoi.docx",
        )
        if not path:
            self._set_status(
                "Chưa lưu file — bấm lại \"Xuất ra file Word...\" trong cửa sổ xem trước khi sẵn sàng.",
                "orange",
            )
            return

        results = validate_all(self._last_questions)
        export_to_docx(
            self._last_questions,
            path,
            scenario_title=self.title_entry.get() or "Tình huống lâm sàng",
            raw_scenario=self._last_scenario,
            validation_results=results,
        )
        self._set_status(f"Đã lưu: {path}", "green")
        messagebox.showinfo(APP_TITLE, f"Đã lưu file Word tại:\n{path}")


def main():
    app = MCQApp()
    app.mainloop()


if __name__ == "__main__":
    main()
