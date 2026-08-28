"""Detect which site / engine a URL belongs to."""

from __future__ import annotations

from urllib.parse import urlparse

from downloader.core.models import Site

# (host patterns, Site) ordered from most to least specific.
_HOST_RULES: list[tuple[tuple[str, ...], Site]] = [
    (("music.youtube.com", "youtube-music.com"), Site.YOUTUBE_MUSIC),
    (("youtube.com", "youtu.be", "youtube-nocookie.com"), Site.YOUTUBE),
    (("open.spotify.com", "spotify.com", "spotify.link"), Site.SPOTIFY),
    (("reddit.com", "redd.it"), Site.REDDIT),
    (("x.com", "twitter.com", "t.co", "tweetdeck.twitter.com"), Site.X),
    (("tiktok.com", "vm.tiktok.com"), Site.TIKTOK),
    (("instagram.com", "instagr.am"), Site.INSTAGRAM),
]

# Generic host patterns handled by yt-dlp for sites not explicitly listed.
_GENERIC_HOST_PREFIXES = (
    "vimeo.com",
    "soundcloud.com",
    "dailymotion.com",
    "twitch.tv",
    "archive.org",
)


def _hostname(url: str) -> str:
    host = urlparse(url).hostname or ""
    return host.lower().removeprefix("www.")


def detect_site(url: str) -> Site:
    """Return the :class:`Site` for a URL.

    Falls back to :attr:`Site.GENERIC` when no specific rule matches. Generic
    URLs are usually still downloadable via yt-dlp.
    """
    host = _hostname(url)
    if not host:
        return Site.GENERIC

    for patterns, site in _HOST_RULES:
        for pattern in patterns:
            if host == pattern or host.endswith("." + pattern.lstrip(".")):
                return site

    if host.startswith(_GENERIC_HOST_PREFIXES):
        return Site.GENERIC

    return Site.GENERIC


def detect_title_from_url(url: str, hostname: str | None = None) -> str:
    """Best-effort readable title from a URL (used before probing)."""
    host = hostname or _hostname(url)
    v = urlparse(url)
    path = v.path.strip("/")
    label = host.replace("-", " ").title()
    if not path:
        return label
    last = path.rsplit("/", 1)[-1]
    if not last or last.lower() in ("watch", "shorts", "reel", "status", "post"):
        return label
    return f"{label} — {last[:60]}"
