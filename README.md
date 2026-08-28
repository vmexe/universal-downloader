# Universal Downloader

A cross-platform (Linux / Windows / macOS), open-source universal downloader for
**YouTube, Spotify, YouTube Music, Reddit, X (Twitter), TikTok, Instagram** and more.

It wraps the best open-source downloader engines behind a single, friendly GUI
and a clean Python API.

## Features

- 🎯 **Auto-detection** — paste any link and the right engine is chosen automatically.
- 📥 **Backend engines**, aggregated behind one interface:
  - [yt-dlp](https://github.com/yt-dlp/yt-dlp) — YouTube, YouTube Music, Reddit, X,
    TikTok, Instagram, and hundreds of generic sites.
  - [spotdl](https://github.com/spotDL/spotify-downloader) — Spotify.
  - [gallery-dl](https://github.com/mikf/gallery-dl) — galleries / Reddit / Instagram fallback.
- 🎬 **Format selection** — video (MP4/WebM/MKV) or audio-only (MP3/M4A/FLAC/OPUS), plus quality.
- ⏱️ **Threaded queue** — download many items, pause / cancel / retry.
- 💾 **Metadata & thumbnails** — tags and embedded cover art.
- 🍪 **Cookies / authentication** for private or age-gated content.
- 🧲 **Proxy & rate-limit settings** to avoid IP bans.

## Installation (development)

Requires **Python 3.11+**.

```bash
# use a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -e ".[dev]"
```

### Spotify extra step

To download Spotify you need a [Spotify Developer](https://developer.spotify.com/)
Client ID / Client Secret. Set them in the app Settings (or add them to
`spotdl`'s config) — [see spotdl docs](https://spotdl.readthedocs.io/).

## Running the GUI

```bash
universal-downloader
# or
python -m downloader.app.main
```

## Using the core API (headless)

```python
from downloader.core.detector import detect_engine
from downloader.core.engines.factory import get_engine
from downloader.config.settings import Settings

settings = Settings()
engine = get_engine(detect_engine("https://www.youtube.com/watch?v=dQw4w9WgXcQ"))
download = engine.download(url="...", out_dir=str(settings.download_dir), format_id="mp4")
print(download.path)
```

## Building standalone binaries

Uses [PyInstaller](https://pyinstaller.org/) to produce a native binary for
each platform. On each OS run:

```bash
pip install -e . pyinstaller
pyinstaller --clean --noconfirm packaging/universal-downloader.spec
```

You also need **ffmpeg** installed (used by yt-dlp/spotdl for post-processing).

- Linux → `dist/universal-downloader/`
- macOS → `dist/universal-downloader/UniversalDownloader.app`
- Windows → `dist/universal-downloader/UniversalDownloader.exe`

CI (`.github/workflows/build.yml`) builds all three automatically when you push
a version tag (`v*`) and attaches them to a GitHub Release.

## Roadmap

- [x] Core engines (yt-dlp, spotdl, gallery-dl) + detection
- [x] Threaded download queue
- [x] PySide6 GUI (main window, queue, settings)
- [x] Headless CLI mode (`--cli`)
- [x] GitHub Actions CI (lint + test on Linux/Windows/macOS)
- [x] PyInstaller packaging for all 3 OS
- [ ] Playlist support in the GUI
- [ ] Subtitle / transcript download
- [ ] More site-specific engines / fallback strategies

## Contributing

Contributions are welcome! Please open an issue or a pull request. See
[CONTRIBUTING.md](CONTRIBUTING.md) and the GitHub Issues tab for good-first-issue
ideas.

## License

MIT — see [LICENSE](LICENSE).
