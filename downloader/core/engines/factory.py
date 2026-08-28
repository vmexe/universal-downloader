"""Engine factory: map a detected site to a concrete backend."""

from __future__ import annotations

from downloader.core.downloader import Downloader
from downloader.core.engines.gallery_engine import GalleryDlEngine
from downloader.core.engines.spotdl_engine import SpotdlEngine
from downloader.core.engines.ytdlp_engine import YtDlpEngine
from downloader.core.models import Site

_cache: dict = {}


def get_engine(
    site: Site,
    spotify_client_id: str | None = None,
    spotify_client_secret: str | None = None,
) -> Downloader:
    """Return a cached engine instance for the given site."""
    key = (site, spotify_client_id, spotify_client_secret)
    if key in _cache:
        return _cache[key]

    if site == Site.SPOTIFY:
        engine = SpotdlEngine(spotify_client_id, spotify_client_secret)
    elif site == Site.INSTAGRAM:
        engine = GalleryDlEngine()
    else:
        engine = YtDlpEngine()

    _cache[key] = engine
    return engine
