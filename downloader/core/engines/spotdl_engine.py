"""Downloader engine backed by spotdl.

Downloads from Spotify. Optionally uses a Spotify Client ID / Client Secret for
higher quality / reliability; without them spotdl runs in anonymous mode.
Credentials can be set via settings (GUI) so no env vars are needed.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

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

_PROGRESS_CB = Callable[[DownloadProgress], None]

#: map our format enum to spotdl output format strings.
_FORMAT_TO_SPOTDL = {
    Format.MP3: "mp3",
    Format.M4A: "m4a",
    Format.FLAC: "flac",
    Format.OPUS: "opus",
    Format.WEBM: "opus",
    Format.MKV: "mp3",
    Format.BEST: "mp3",
}


class SpotdlEngine(Downloader):
    """spotdl based downloader for Spotify tracks / playlists."""

    site = Site.SPOTIFY

    def __init__(self, client_id: str | None = None, client_secret: str | None = None) -> None:
        self._client_id = client_id
        self._client_secret = client_secret

    def _make_spotdl(self, out_dir: str, out_format: str, proxy: str | None = None):
        from spotdl import Spotdl

        settings: dict = {
            "output": out_dir,
            "format": out_format,
            "threads": 1,
        }
        if proxy:
            settings["proxy"] = proxy
        # client_id/client_secret are positional; None => anonymous fallback.
        return Spotdl(self._client_id, self._client_secret, downloader_settings=settings)

    @staticmethod
    def _title_for(song) -> str:
        parts = [p for p in (getattr(song, "artist", None) or "", getattr(song, "name", None) or "") if p]
        return " - ".join(parts) or "Spotify track"

    def probe(self, url: str, cookies: str | None = None) -> MediaInfo:
        from spotdl import Spotdl

        # Probe with a throwaway instance (no output needed).
        spotdl = Spotdl(self._client_id, self._client_secret)
        try:
            songs = spotdl.search([url])
        except Exception:  # noqa: BLE001 - probing must not crash
            songs = []
        title = self._title_for(songs[0]) if songs else "Spotify track"
        return MediaInfo(url=url, title=title, site=Site.SPOTIFY)

    def download(
        self,
        request: DownloadRequest,
        progress: _PROGRESS_CB | None = None,
        cookies: str | None = None,
        proxy: str | None = None,
        rate_limit: str | None = None,
        quality: str | None = None,
    ) -> DownloadResult:
        out_format = _FORMAT_TO_SPOTDL.get(request.fmt, "mp3")
        try:
            out_dir = str(request.out_dir)
            spotdl = self._make_spotdl(out_dir, out_format, proxy)
            if progress:
                progress(DownloadProgress(request=request, percent=0.0))
            songs = spotdl.search([request.url])
            if not songs:
                return DownloadResult(
                    request=request,
                    status=Status.FAILED,
                    error="No matching track found for the given Spotify URL",
                )
            results = spotdl.download_songs(songs[:1])
        except Exception as exc:
            log.exception("spotdl download failed")
            return DownloadResult(request=request, status=Status.FAILED, error=str(exc))

        path = None
        if results:
            _, first_path = results[0]
            path = first_path
        if progress:
            progress(DownloadProgress(request=request, percent=100.0))
        return DownloadResult(request=request, status=Status.COMPLETED, path=path)
