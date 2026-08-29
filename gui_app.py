#!/usr/bin/env python3
"""
gui_app.py
-----------
Ứng dụng giao diện cửa sổ (desktop app) — không cần dòng lệnh.
Mặc định dùng Gemini API (Google); có thể đổi sang Anthropic trong app.

Cách chạy:
    python gui_app.py
(Trên Windows có thể double-click file run_windows.bat;
 trên Mac double-click file run_mac.command — xem README.md)

Luồng sử dụng:
    1. Lần đầu mở app sẽ hỏi API key của nhà cung cấp đang chọn (mặc định
       Gemini). Chỉ hỏi 1 lần, lưu cục bộ tại
       ~/.clinical_mcq_generator/config.json — xem config.py.
    2. Dán tình huống lâm sàng thô vào ô văn bản.
    3. Bấm "Tạo bộ 10 câu hỏi".
    4. Chờ vài chục giây (app gọi API ở luồng nền, không đơ giao diện) —
       xong sẽ hiện hộp thoại chọn nơi lưu file Word (.docx).
    5. Xem lại danh sách cảnh báo kỹ thuật (nếu có) ngay trong app.
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

from mcq_generator import export_to_docx, validate_all
from mcq_generator.config import clear_api_key, load_api_key, save_api_key
from mcq_generator.generator import GenerationError, generate_mcq_set

APP_TITLE = "Công cụ soạn câu hỏi MCQ lâm sàng theo năng lực"

PROVIDER_LABELS = {"gemini": "Google Gemini", "anthropic": "Anthropic Claude"}
API_KEY_URL = {
    "gemini": "https://aistudio.google.com/apikey",
    "anthropic": "https://console.anthropic.com/settings/keys",
}


class MCQApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("900x720")
        self.minsize(700, 520)

        self.provider_var = tk.StringVar(value="gemini")
        self._last_questions: list[dict] | None = None
        self._last_scenario: str = ""

        self._build_menu()
        self._build_widgets()

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
        self.config(menu=menubar)

    def _build_widgets(self):
        pad = {"padx": 10, "pady": 6}

        provider_frame = ttk.Frame(self)
        provider_frame.pack(fill="x", **pad)
        ttk.Label(provider_frame, text="Nhà cung cấp AI:").pack(side="left")
        for value, label in PROVIDER_LABELS.items():
            ttk.Radiobutton(
                provider_frame,
                text=label,
                value=value,
                variable=self.provider_var,
            ).pack(side="left", padx=(10, 0))

        top_label = ttk.Label(
            self,
            text="Dán tình huống lâm sàng thô vào ô bên dưới "
            "(tiền sử, bệnh sử, khám lâm sàng, cận lâm sàng...):",
        )
        top_label.pack(anchor="w", **pad)

        self.scenario_box = scrolledtext.ScrolledText(self, height=13, wrap="word")
        self.scenario_box.pack(fill="both", expand=True, padx=10)

        title_frame = ttk.Frame(self)
        title_frame.pack(fill="x", **pad)
        ttk.Label(title_frame, text="Tiêu đề ca bệnh (hiện trong file Word):").pack(
            side="left"
        )
        self.title_entry = ttk.Entry(title_frame)
        self.title_entry.insert(0, "Tình huống lâm sàng")
        self.title_entry.pack(side="left", fill="x", expand=True, padx=(8, 0))

        button_frame = ttk.Frame(self)
        button_frame.pack(fill="x", **pad)
        self.generate_btn = ttk.Button(
            button_frame, text="Tạo bộ 10 câu hỏi", command=self._on_generate_click
        )
        self.generate_btn.pack(side="left")

        self.progress = ttk.Progressbar(button_frame, mode="indeterminate")
        self.progress.pack(side="left", fill="x", expand=True, padx=10)

        self.status_label = ttk.Label(self, text="Sẵn sàng.", foreground="gray")
        self.status_label.pack(anchor="w", padx=10)

        result_label = ttk.Label(self, text="Kết quả / cảnh báo kỹ thuật:")
        result_label.pack(anchor="w", **pad)

        self.result_box = scrolledtext.ScrolledText(
            self, height=10, wrap="word", state="disabled", background="#f4f4f4"
        )
        self.result_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))

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

    def _on_generate_click(self):
        scenario = self.scenario_box.get("1.0", tk.END).strip()
        if not scenario:
            messagebox.showwarning(APP_TITLE, "Vui lòng dán tình huống lâm sàng trước.")
            return

        provider = self._current_provider()
        api_key = self._ensure_api_key(prompt_if_missing=True)
        if not api_key:
            messagebox.showwarning(
                APP_TITLE, "Cần có API key để tạo câu hỏi tự động."
            )
            return

        self.generate_btn.config(state="disabled")
        self.progress.start(12)
        self._set_status(
            f"Đang gọi {PROVIDER_LABELS[provider]} để soạn 10 câu hỏi... "
            "(vài chục giây)",
            "blue",
        )
        self._set_result_text("")

        thread = threading.Thread(
            target=self._generate_worker,
            args=(scenario, provider, api_key),
            daemon=True,
        )
        thread.start()

    def _generate_worker(self, scenario: str, provider: str, api_key: str):
        try:
            questions = generate_mcq_set(scenario, provider=provider, api_key=api_key)
            results = validate_all(questions)
            self.after(0, self._on_generate_success, scenario, questions, results)
        except GenerationError as exc:
            self.after(0, self._on_generate_error, str(exc))
        except Exception:  # noqa: BLE001 - hiện lỗi đầy đủ cho người dùng debug
            self.after(0, self._on_generate_error, traceback.format_exc())

    def _on_generate_error(self, message: str):
        self.progress.stop()
        self.generate_btn.config(state="normal")
        self._set_status("Có lỗi xảy ra.", "red")
        self._set_result_text(message)
        messagebox.showerror(APP_TITLE, f"Không tạo được câu hỏi:\n\n{message[:500]}")

    def _on_generate_success(self, scenario: str, questions: list[dict], results):
        self.progress.stop()
        self.generate_btn.config(state="normal")
        self._last_questions = questions
        self._last_scenario = scenario

        n_warnings = sum(len(r.warnings) for r in results)
        self._set_status(
            f"Đã tạo {len(questions)} câu hỏi. {n_warnings} cảnh báo kỹ thuật.",
            "green" if n_warnings == 0 else "orange",
        )

        lines = []
        for r in results:
            if r.warnings:
                lines.append(f"Câu {r.question_number}:")
                for w in r.warnings:
                    lines.append(f"   - {w}")
        if not lines:
            lines.append(
                "Không phát hiện lỗi kỹ thuật tự động nào. "
                "Vẫn nên đọc lại nội dung y khoa trước khi dùng chính thức."
            )
        self._set_result_text("\n".join(lines))

        self._save_docx_dialog()

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
                "Đã tạo xong câu hỏi nhưng chưa lưu file. Bấm nút bên dưới để lưu.",
                "orange",
            )
            self._add_save_again_button()
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

    def _add_save_again_button(self):
        if getattr(self, "_save_btn", None):
            return
        self._save_btn = ttk.Button(
            self, text="Lưu file Word...", command=self._save_docx_dialog
        )
        self._save_btn.pack(pady=(0, 10))


def main():
    app = MCQApp()
    app.mainloop()


if __name__ == "__main__":
    main()
