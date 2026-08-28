"""Core data models used across the application."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class Site(str, Enum):
    """Supported sites / content sources."""

    YOUTUBE = "youtube"
    YOUTUBE_MUSIC = "youtube_music"
    SPOTIFY = "spotify"
    REDDIT = "reddit"
    X = "x"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    GENERIC = "generic"


class Format(str, Enum):
    """User facing output formats mapped to engine-specific format ids."""

    BEST = "best"
    MP4 = "mp4"
    WEBM = "webm"
    MKV = "mkv"
    MP3 = "mp3"
    M4A = "m4a"
    FLAC = "flac"
    OPUS = "opus"


@dataclass
class Settings:
    """Persisted user settings."""

    output_template: str = "{title}.{ext}"
    download_dir: Path | None = None
    proxy: str | None = None
    rate_limit: str | None = None
    cookies_path: Path | None = None
    spotify_client_id: str | None = None
    spotify_client_secret: str | None = None
    concurrent_jobs: int = 2


@dataclass
class MediaInfo:
    """Metadata about a discovered media item."""

    url: str
    title: str = ""
    site: Site = Site.GENERIC
    thumbnail: str | None = None
    duration: int | None = None
    is_playlist: bool = False


@dataclass
class DownloadRequest:
    """A single unit of work submitted to the queue."""

    url: str
    out_dir: Path
    fmt: Format = Format.BEST
    audio_only: bool = False
    metadata: MediaInfo | None = None
    site: Site | None = None
    quality: str | None = None


class Status(str, Enum):
    """Lifecycle state of a download."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class DownloadResult:
    """Outcome of a finished download."""

    request: DownloadRequest
    status: Status
    path: Path | None = None
    error: str | None = None
    info: MediaInfo | None = None


@dataclass
class DownloadProgress:
    """Streamed progress during a running download."""

    request: DownloadRequest
    percent: float = 0.0
    bytes_done: int = 0
    bytes_total: int | None = None
    speed: str | None = None
    eta: str | None = None
    status: Status = Status.RUNNING


@dataclass
class DownloadTask:
    """Bookkeeping for a queued task."""

    request: DownloadRequest
    status: Status = Status.QUEUED
    result: DownloadResult | None = None
    progress: DownloadProgress = field(init=False)

    def __post_init__(self) -> None:
        self.progress = DownloadProgress(request=self.request, status=self.status)
