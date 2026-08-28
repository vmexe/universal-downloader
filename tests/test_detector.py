"""Tests for the URL site detector."""

from downloader.core.detector import detect_site
from downloader.core.models import Site


def test_youtube():
    assert detect_site("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == Site.YOUTUBE
    assert detect_site("https://youtu.be/dQw4w9WgXcQ") == Site.YOUTUBE


def test_youtube_music():
    assert detect_site("https://music.youtube.com/watch?v=abc") == Site.YOUTUBE_MUSIC


def test_spotify():
    assert detect_site("https://open.spotify.com/track/123") == Site.SPOTIFY


def test_reddit_x_tiktok_instagram():
    assert detect_site("https://www.reddit.com/r/pics/comments/abc") == Site.REDDIT
    assert detect_site("https://x.com/elonmusk/status/123") == Site.X
    assert detect_site("https://twitter.com/user/status/456") == Site.X
    assert detect_site("https://www.tiktok.com/@user/video/123") == Site.TIKTOK
    assert detect_site("https://www.instagram.com/p/abc/") == Site.INSTAGRAM


def test_generic():
    assert detect_site("https://vimeo.com/123") == Site.GENERIC
    assert detect_site("not a url") == Site.GENERIC
    assert detect_site("") == Site.GENERIC
