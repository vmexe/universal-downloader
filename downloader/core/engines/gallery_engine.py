"""Downloader engine backed by gallery-dl.

Handles image galleries, stands in as a fallback for Reddit / Instagram when
yt-dlp cannot match every attachment.
"""

from __future__ import annotations

import logging
from typing import Optional

import gallery_dl

from downloader.core.downloader import Downloader
from downloader.core.models import (
    DownloadRequest,
    DownloadResult,
    MediaInfo,
    Site,
    Status,
)

log = logging.getLogger(__name__)


class GalleryDlEngine(Downloader):
    """gallery-dl based downloader for image / gallery sites."""

    site = Site.GENERIC

    def probe(self, url: str, cookies: str | None = None) -> MediaInfo:
        return MediaInfo(url=url, title="Image gallery", site=Site.GENERIC)

    def download(
        self,
        request: DownloadRequest,
        progress: Optional = None,
        cookies: str | None = None,
        proxy: str | None = None,
        rate_limit: str | None = None,
        quality: str | None = None,
    ) -> DownloadResult:
        try:
            opts = gallery_dl.config.load([])
            opts["directory"] = [str(request.out_dir)]
            if proxy:
                opts["proxy"] = proxy
            from gallery_dl import job

            job.DownloadJob(request.url).run()
        except Exception as exc:
            log.exception("gallery-dl download failed")
            return DownloadResult(request=request, status=Status.FAILED, error=str(exc))
        return DownloadResult(request=request, status=Status.COMPLETED, path=request.out_dir)
