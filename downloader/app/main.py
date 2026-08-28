"""PySide6 GUI for the Universal Downloader."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from downloader.config.settings import load_settings, save_settings
from downloader.core.detector import detect_site, detect_title_from_url
from downloader.core.models import DownloadRequest, DownloadTask, Format, Status
from downloader.core.queue import DownloadQueue


class QueueBridge(QObject):
    """Thread-safe bridge: forwards core queue updates to the Qt main thread."""

    task_updated = Signal(object)

    def on_update(self, task: DownloadTask) -> None:
        # Signal is auto-connected if the bridge lives in the GUI thread.
        self.task_updated.emit(task)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.settings = load_settings()
        self._bridge = QueueBridge()
        self._queue = DownloadQueue(
            on_task_update=self._bridge.on_update,
            concurrent_jobs=self.settings.concurrent_jobs,
        )
        # connect signal (cross-thread, queued automatically).
        self._bridge.task_updated.connect(self._on_task_updated)
        self._queue.start()

        self.setWindowTitle("Universal Downloader")
        self.resize(760, 540)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)

        self._build_url_bar(root)
        self._build_options(root)
        self._build_queue(root)

        self.status_label = QLabel("Ready")
        root.addWidget(self.status_label)

    # -- UI construction -------------------------------------------------
    def _build_url_bar(self, root: QVBoxLayout) -> None:
        row = QHBoxLayout()
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("Paste a YouTube / Spotify / Reddit / X / TikTok / Instagram link…")
        self.url_edit.returnPressed.connect(self.add_download)
        self.add_btn = QPushButton("Add to queue")
        self.add_btn.clicked.connect(self.add_download)
        row.addWidget(self.url_edit, 1)
        row.addWidget(self.add_btn)
        root.addLayout(row)

    def _build_options(self, root: QVBoxLayout) -> None:
        box = QGroupBox("Options")
        layout = QHBoxLayout(box)
        layout.addWidget(QLabel("Format:"))
        self.format_combo = None
        from PySide6.QtWidgets import QComboBox

        self.fmt_combo = QComboBox()
        self.fmt_combo.addItems([f.value for f in Format])
        layout.addWidget(self.fmt_combo)

        self.audio_check = None
        layout.addWidget(QLabel("Output:"))
        self.out_edit = QLineEdit(str(self.settings.download_dir or ""))
        self.out_btn = QPushButton("Browse…")
        self.out_btn.clicked.connect(self._browse_out)
        layout.addWidget(self.out_edit, 1)
        layout.addWidget(self.out_btn)
        root.addWidget(box)

    def _build_queue(self, root: QVBoxLayout) -> None:
        self.queue_list = QListWidget()
        root.addWidget(self.queue_list)
        btn_row = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancel selected")
        self.cancel_btn.clicked.connect(self._cancel_selected)
        self.settings_btn = QPushButton("Settings…")
        self.settings_btn.clicked.connect(self._open_settings)
        btn_row.addWidget(self.cancel_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.settings_btn)
        root.addLayout(btn_row)

    # -- actions ---------------------------------------------------------
    def _browse_out(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "Choose download folder", self.out_edit.text())
        if d:
            self.out_edit.setText(d)

    def add_download(self) -> None:
        url = self.url_edit.text().strip()
        if not url:
            self.status_label.setText("Please paste a URL")
            return
        out = Path(self.out_edit.text().strip()) or self.settings.download_dir
        out = out or self.settings.download_dir
        out.mkdir(parents=True, exist_ok=True)
        fmt = Format(self.fmt_combo.currentText())
        request = DownloadRequest(
            url=url,
            out_dir=out,
            fmt=fmt,
            audio_only=fmt in (Format.MP3, Format.M4A, Format.FLAC, Format.OPUS),
            site=detect_site(url),
        )
        task = DownloadTask(request=request)
        self._queue.add(task)
        self._render_item(task)
        self.url_edit.clear()
        site = task.request.site.value if task.request.site else "?"
        self.status_label.setText(f"Queued ({site}): {detect_title_from_url(url)}")

    def _cancel_selected(self) -> None:
        for item in self.queue_list.selectedItems():
            pass  # cancellation handled at engine level in a future release
        self.status_label.setText("Cancellation is not yet wired to in-flight engines")

    # -- queue rendering --------------------------------------------------
    def _render_item(self, task: DownloadTask) -> None:
        item = self.queue_list.findItems(task.request.url, Qt.MatchFlag.MatchExactly)
        if item:
            widget = item[0]
            widget.setText(self._task_text(task))
        else:
            li = QListWidgetItem(self._task_text(task))
            li.setData(256, task.request.url)  # store key in UserRole=256
            self.queue_list.addItem(li)

    def _task_text(self, task: DownloadTask) -> str:
        site = task.request.site.value if task.request.site else "?"
        state = task.status.value
        if task.result and task.result.error:
            return f"[{site}] {task.request.url}  ->  {state}: {task.result.error[:80]}"
        return f"[{site}] {task.request.url}  ->  {state}"

    def _on_task_updated(self, task: DownloadTask) -> None:
        if not isinstance(task, DownloadTask):
            return
        self._render_item(task)
        self.status_label.setText(f"{task.status.value}: {task.request.url}")

    def _open_settings(self) -> None:
        from downloader.app.windows.settings_dialog import SettingsDialog

        dlg = SettingsDialog(self.settings, self)
        if dlg.exec():
            self.settings = dlg.settings
            save_settings(self.settings)
            self.out_edit.setText(str(self.settings.download_dir or ""))
            self.status_label.setText("Settings saved")


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(prog="universal-downloader", description=__doc__)
    parser.add_argument("--cli", action="store_true", help="run headless download of URIs")
    parser.add_argument("--format", choices=[f.value for f in Format], default=None)
    parser.add_argument("--output", type=str, default=None, help="output directory")
    parser.add_argument("--audio-only", action="store_true")
    parser.add_argument("urls", nargs="*", help="media URLs to download (used with --cli)")

    args = parser.parse_args()

    if args.cli:
        return _run_cli(args)

    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    return app.exec()


def _run_cli(args) -> int:
    """Headless downloader for scripting / servers without a display."""
    from downloader.core.models import DownloadRequest
    from downloader.core.queue import DownloadQueue

    if not args.urls:
        print("No URLs provided. Pass URLs after --cli, e.g. --cli <url>")
        return 1

    settings = load_settings()
    out_dir = Path(args.output) if args.output else Path(settings.download_dir or "")
    out_dir.mkdir(parents=True, exist_ok=True)
    fmt = Format(args.format) if args.format else Format.BEST

    queue = DownloadQueue(
        on_task_update=lambda t: print(f"[{t.status.value}] {t.request.url}"),
        concurrent_jobs=settings.concurrent_jobs,
    )
    queue.start()

    for url in args.urls:
        request = DownloadRequest(
            url=url,
            out_dir=out_dir,
            fmt=fmt,
            audio_only=args.audio_only or fmt in (Format.MP3, Format.M4A, Format.FLAC, Format.OPUS),
            site=detect_site(url),
        )
        queue.add(DownloadTask(request=request))

    queue.wait()

    statuses = [t.status for t in queue.tasks]
    failed = sum(1 for s in statuses if s == Status.FAILED)
    done = sum(1 for s in statuses if s == Status.COMPLETED)
    print(f"Completed: {done}, Failed: {failed}, Total: {len(statuses)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
