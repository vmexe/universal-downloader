"""Loading and saving user settings to a platform-appropriate location."""

from __future__ import annotations

import json
from pathlib import Path

from platformdirs import user_config_dir

from downloader.core.models import Settings

APP_NAME = "universal-downloader"


def config_dir() -> Path:
    """Return the per-OS config directory (created on demand)."""
    d = Path(user_config_dir(APP_NAME))
    d.mkdir(parents=True, exist_ok=True)
    return d


def _settings_path() -> Path:
    return config_dir() / "settings.json"


def default_download_dir() -> Path:
    """Sensible per-OS default download directory."""
    home = Path.home()
    return home / "Downloads" / "UniversalDownloader"


def load_settings() -> Settings:
    """Load settings from disk, merging defaults. Never raises."""
    path = _settings_path()
    s = Settings()
    s.download_dir = default_download_dir()
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}
        if data.get("output_template"):
            s.output_template = data["output_template"]
        if data.get("download_dir"):
            s.download_dir = Path(data["download_dir"])
        if data.get("proxy"):
            s.proxy = data["proxy"]
        if data.get("rate_limit"):
            s.rate_limit = data["rate_limit"]
        if data.get("cookies_path"):
            s.cookies_path = Path(data["cookies_path"])
        if data.get("spotify_client_id"):
            s.spotify_client_id = data["spotify_client_id"]
        if data.get("spotify_client_secret"):
            s.spotify_client_secret = data["spotify_client_secret"]
        if isinstance(data.get("concurrent_jobs"), int):
            s.concurrent_jobs = data["concurrent_jobs"]
    return s


def save_settings(s: Settings) -> None:
    """Persist settings to disk."""
    data = {
        "output_template": s.output_template,
        "download_dir": str(s.download_dir) if s.download_dir else None,
        "proxy": s.proxy,
        "rate_limit": s.rate_limit,
        "cookies_path": str(s.cookies_path) if s.cookies_path else None,
        "spotify_client_id": s.spotify_client_id,
        "spotify_client_secret": s.spotify_client_secret,
        "concurrent_jobs": s.concurrent_jobs,
    }
    _settings_path().write_text(json.dumps(data, indent=2), encoding="utf-8")
