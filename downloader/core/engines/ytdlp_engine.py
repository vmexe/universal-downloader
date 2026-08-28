"""Downloader engine backed by yt-dlp.

Handles YouTube, YouTube Music, Reddit, X, TikTok, Instagram and many generic
video/audio sites through a single mature backend.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import yt_dlp

from downloader.core.downloader import Downloader
from downloader.core.models import (
    DownloadProgress,
    DownloadRequest,
    DownloadResult,
    Format,
    MediaInfo,
    Site,
    Status,
)

log = logging.getLogger(__name__)

#: filter to prefer progressive formats for direct playback on most players.
_FORMAT_MAP = {
    Format.BEST: "bestvideo*+bestaudio/best",
    Format.MP4: "bestvideo*[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
    Format.WEBM: "bestvideo*[ext=webm]+bestaudio[ext=webm]/best[ext=webm]",
    Format.MKV: "bestvideo*+bestaudio/best",
    Format.MP3: "bestaudio/best",
    Format.M4A: "bestaudio[ext=m4a]/bestaudio/best",
    Format.FLAC: "bestaudio/best",
    Format.OPUS: "bestaudio/best",
}

_AUDIO_CODEC = {
    Format.MP3: "libmp3lame",
    Format.M4A: "aac",
    Format.OPUS: "libopus",
    Format.FLAC: "flac",
}


class YtDlpEngine(Downloader):
    """yt-dlp based downloader for broad site coverage."""

    site = Site.GENERIC

    def __init__(self) -> None:
        self._opts_base: dict = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": False,
            "progress_hooks": [],
        }

    # -- yt-dlp option builders -------------------------------------------
    def _meta_opts(self, cookies: str | None) -> dict:
        opts = {"quiet": True, "no_warnings": True, "skip_download": True}
        if cookies:
            opts["cookiefile"] = cookies
        return opts

    def _download_opts(
        self,
        request: DownloadRequest,
        cookies: str | None,
        proxy: str | None,
        rate_limit: str | None,
        quality: str | None,
        on_progress: object | None,
    ) -> dict:
        opts: dict = {
            "outtmpl": self._default_outtmpl(request),
            "noplaylist": not (request.metadata.is_playlist if request.metadata else True),
            "progress_hooks": [on_progress] if on_progress else None,
            "format": _FORMAT_MAP[request.fmt],
        }

        audio_only = request.audio_only or request.fmt in (
            Format.MP3,
            Format.M4A,
            Format.FLAC,
            Format.OPUS,
        )
        if audio_only:
            codec = _AUDIO_CODEC.get(request.fmt, "best")
            opts["format"] = _FORMAT_MAP[request.fmt]
            opts["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": codec,
                    "preferredquality": quality or "0",
                }
            ]
            opts["final_ext"] = request.fmt.value

        if cookies:
            opts["cookiefile"] = cookies
        if proxy:
            opts["proxy"] = proxy
        if rate_limit:
            opts["ratelimit"] = rate_limit
        if request.quality:
            opts["format_sort"] = [request.quality]

        return opts

    def _default_outtmpl(self, request: DownloadRequest) -> str:
        return str(request.out_dir / "%(title).200B [%(id)s].%(ext)s")

    # -- public interface ------------------------------------------------
    def probe(self, url: str, cookies: str | None = None) -> MediaInfo:
        with yt_dlp.YoutubeDL(self._meta_opts(cookies)) as ydl:
            info = ydl.extract_info(url, download=False)
        return MediaInfo(
            url=url,
            title=info.get("title") or "",
            site=Site.GENERIC,
            thumbnail=info.get("thumbnail"),
            duration=info.get("duration"),
            is_playlist=bool(info.get("_type") in ("playlist", "multi_video")),
        )

    def download(
        self,
        request: DownloadRequest,
        progress: Optional = None,
        cookies: str | None = None,
        proxy: str | None = None,
        rate_limit: str | None = None,
        quality: str | None = None,
    ) -> DownloadResult:
        def _hook(d: dict) -> None:
            if d.get("status") == "downloading" and progress:
                raw = d.get("_percent_str", "0").strip("%")
                try:
                    percent = float(raw)
                except ValueError:
                    percent = 0.0
                p = DownloadProgress(
                    request=request,
                    percent=percent,
                    bytes_done=d.get("downloaded_bytes") or 0,
                    bytes_total=d.get("total_bytes") or d.get("total_bytes_estimate"),
                    speed=d.get("_speed_str"),
                    eta=d.get("_eta_str"),
                )
                progress(p)

        opts = self._download_opts(request, cookies, proxy, rate_limit, quality, _hook)
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(request.url, download=True)
            out_path: Path | None = None
            if info:
                out_path = Path(ydl.prepare_filename(info))
        except Exception as exc:  # yt-dlp raises various exception types
            log.exception("yt-dlp download failed")
            return DownloadResult(
                request=request,
                status=Status.FAILED,
                error=str(exc) or exc.__class__.__name__,
            )
        return DownloadResult(request=request, status=Status.COMPLETED, path=out_path)
