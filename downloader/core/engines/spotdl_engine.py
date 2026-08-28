"""Downloader engine backed by spotdl.

Downloads from Spotify (and matches quality metadata). Requires Spotify
Client ID / Client Secret configured via settings — set them through the GUI
or by exporting ``SPOTIFY_CLIENT_ID`` / ``SPOTIFY_CLIENT_SECRET``.
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from downloader.core.downloader import Downloader
from downloader.core.models import (
    DownloadProgress,
    DownloadRequest,
    DownloadResult,
    MediaInfo,
    Site,
    Status,
)

log = logging.getLogger(__name__)


class SpotdlEngine(Downloader):
    """spotdl based downloader for Spotify tracks / playlists."""

    site = Site.SPOTIFY

    def __init__(self, client_id: str | None = None, client_secret: str | None = None) -> None:
        self._client_id = client_id
        self._client_secret = client_secret

    def _configure(self) -> None:
        # spotdl reads these env vars; fall back to any provided values.
        if self._client_id:
            os.environ.setdefault("SPOTIFY_CLIENT_ID", self._client_id)
        if self._client_secret:
            os.environ.setdefault("SPOTIFY_CLIENT_SECRET", self._client_secret)

    def probe(self, url: str, cookies: str | None = None) -> MediaInfo:
        self._configure()
        from spotdl import Spotdl
        from spotdl.utils.metadata import to_metadata

        spotdl = Spotdl(client_id=self._client_id, client_secret=self._client_secret)
        # spotdl resolves a song object from a URL.
        try:
            songs = spotdl.search([url])
        except Exception:  # noqa: BLE001 - probing must not crash
            songs = []
        title = ""
        if songs:
            meta = to_metadata(songs[0])
            parts = [p for p in (meta.artist or "", meta.name or "") if p]
            title = " - ".join(parts)
        return MediaInfo(url=url, title=title or "Spotify track", site=Site.SPOTIFY)

    def download(
        self,
        request: DownloadRequest,
        progress: Optional = None,
        cookies: str | None = None,
        proxy: str | None = None,
        rate_limit: str | None = None,
        quality: str | None = None,
    ) -> DownloadResult:
        self._configure()
        try:
            from spotdl import Spotdl

            spotdl = Spotdl(client_id=self._client_id, client_secret=self._client_secret)
            out = str(request.out_dir)
            # spotdl has no fine-grained progress callback hook; emit once.
            if progress:
                progress(DownloadProgress(request=request, percent=0.0))
            spotdl.download([request.url], output=out)
        except Exception as exc:
            log.exception("spotdl download failed")
            return DownloadResult(request=request, status=Status.FAILED, error=str(exc))
        return DownloadResult(request=request, status=Status.COMPLETED, path=request.out_dir)
