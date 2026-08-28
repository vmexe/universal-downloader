"""Abstract downloader interface.

Every backend engine implements this interface so the queue and GUI can treat
all sites uniformly. Engines run long operations and push progress via callbacks.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable

from downloader.core.models import (
    DownloadProgress,
    DownloadRequest,
    DownloadResult,
    MediaInfo,
    Site,
)

ProgressCallback = Callable[[DownloadProgress], None]


class Downloader(ABC):
    """Base class for a backend download engine."""

    #: sites this engine can handle
    site: Site = Site.GENERIC

    @abstractmethod
    def probe(self, url: str, cookies: str | None = None) -> MediaInfo:
        """Fetch metadata about the URL without downloading anything."""

    @abstractmethod
    def download(
        self,
        request: DownloadRequest,
        progress: ProgressCallback | None = None,
        cookies: str | None = None,
        proxy: str | None = None,
        rate_limit: str | None = None,
        quality: str | None = None,
    ) -> DownloadResult:
        """Download the media described by ``request``.

        :param progress: callback invoked repeatedly with progress updates.
        :param cookies: path to a Netscape cookies file, if needed.
        :param proxy: proxy URL to route requests through.
        :param rate_limit: e.g. ``"1M"``, ``"5M"`` to throttle bandwidth.
        :param quality: optional quality hint (engine specific).
        :return: a :class:`DownloadResult`.
        """
