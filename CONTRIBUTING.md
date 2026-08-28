# Contributing

Thanks for wanting to contribute! Here's how to get started.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate         # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Running checks

Always run these before submitting a pull request:

```bash
ruff check downloader tests   # lint
pytest                        # tests
```

The CI pipeline runs the same checks on Linux, Windows and macOS.

## Project layout

```
downloader/
├── app/          # PySide6 GUI (everything Qt lives here)
├── config/       # per-OS settings persistence
└── core/         # pure logic, no GUI: models, queue, engines
    └── engines/  # one module per backend (yt-dlp, spotdl, gallery-dl)
```

Guidelines:

- Keep **GUI in `app/`**, **logic in `core/`**. The `core/` package must stay
  usable and testable without a display.
- Add a new site by (1) adding a `Site` enum member + detector rule, then
  (2) routing it to an engine in `engines/factory.py`.
- Write tests in `tests/` — pure-`core` code is tested headless.
- Open an issue first for non-trivial features so work isn't duplicated.

## Reporting issues

Include the URL you tried, the format options, and the full error output (use
`universal-downloader --cli <url>` to get console output).
