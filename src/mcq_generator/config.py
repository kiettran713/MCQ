"""
config.py
----------
Lưu / đọc API key trên máy người dùng theo từng nhà cung cấp (provider:
"gemini" hoặc "anthropic"), để chỉ cần nhập 1 lần khi mở app lần đầu.

File cấu hình lưu tại thư mục home của người dùng:
  - Windows: C:\\Users\\<tên>\\.clinical_mcq_generator\\config.json
  - Mac/Linux: ~/.clinical_mcq_generator/config.json

LƯU Ý BẢO MẬT: file này lưu API key ở dạng văn bản thường (không mã hoá),
giống cách nhiều công cụ dòng lệnh khác vẫn làm (ví dụ AWS CLI, gcloud).
Không chia sẻ file này, ảnh chụp màn hình có key, hoặc máy tính của bạn
cho người khác. Nếu nghi ngờ key bị lộ, thu hồi (revoke/xoá khóa) và tạo
key mới:
  - Gemini:    https://aistudio.google.com/apikey
  - Anthropic: https://console.anthropic.com/settings/keys
"""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path

CONFIG_DIR = Path.home() / ".clinical_mcq_generator"
CONFIG_FILE = CONFIG_DIR / "config.json"

_ENV_VAR_BY_PROVIDER = {
    "gemini": "GEMINI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}
_CONFIG_KEY_BY_PROVIDER = {
    "gemini": "gemini_api_key",
    "anthropic": "anthropic_api_key",
}


def _read_config() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def load_api_key(provider: str = "gemini") -> str | None:
    """Ưu tiên biến môi trường tương ứng nếu có; nếu không, đọc từ file
    cấu hình cục bộ theo đúng provider."""
    env_var = _ENV_VAR_BY_PROVIDER.get(provider)
    if env_var:
        env_key = os.environ.get(env_var)
        if env_key:
            return env_key

    config_key = _CONFIG_KEY_BY_PROVIDER.get(provider)
    if not config_key:
        return None
    return _read_config().get(config_key)


def save_api_key(api_key: str, provider: str = "gemini") -> None:
    config_key = _CONFIG_KEY_BY_PROVIDER.get(provider)
    if not config_key:
        raise ValueError(f"Provider không hợp lệ: {provider!r}")

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    data = _read_config()
    data[config_key] = api_key.strip()
    CONFIG_FILE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    # Giới hạn quyền đọc file chỉ cho chủ sở hữu (best-effort; trên
    # Windows lệnh này không có hiệu lực đầy đủ nhưng không gây lỗi).
    try:
        os.chmod(CONFIG_FILE, stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass


def clear_api_key(provider: str | None = None) -> None:
    """Xoá key của 1 provider cụ thể, hoặc xoá toàn bộ file nếu
    provider=None."""
    if provider is None:
        if CONFIG_FILE.exists():
            CONFIG_FILE.unlink()
        return

    config_key = _CONFIG_KEY_BY_PROVIDER.get(provider)
    if not config_key:
        return
    data = _read_config()
    if config_key in data:
        del data[config_key]
        CONFIG_FILE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
