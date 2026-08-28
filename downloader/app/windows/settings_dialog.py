"""Settings dialog for the Universal Downloader."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from downloader.core.models import Settings


class SettingsDialog(QDialog):
    def __init__(self, settings: Settings, parent: Optional = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.settings = settings
        self.setMinimumWidth(460)

        root = QVBoxLayout(self)
        form = QFormLayout(root)

        self.template_edit = QLineEdit(settings.output_template)
        form.addRow("Output filename template:", self.template_edit)

        out_row = QHBoxLayout()
        self.out_edit = QLineEdit(str(settings.download_dir or ""))
        btn = QPushButton("Browse…")
        btn.clicked.connect(self._browse)
        out_row.addWidget(self.out_edit, 1)
        out_row.addWidget(btn)
        form.addRow("Download folder:", out_row)

        self.proxy_edit = QLineEdit(settings.proxy or "")
        form.addRow("Proxy URL (optional):", self.proxy_edit)

        self.rate_edit = QLineEdit(settings.rate_limit or "")
        form.addRow("Rate limit (optional, e.g. 5M):", self.rate_edit)

        self.cookies_edit = QLineEdit(str(settings.cookies_path or ""))
        ck_row = QHBoxLayout()
        ck_row.addWidget(self.cookies_edit, 1)
        ck_btn = QPushButton("Browse…")
        ck_btn.clicked.connect(self._browse_cookies)
        ck_row.addWidget(ck_btn)
        form.addRow("Cookies file (Netscape):", ck_row)

        self.spotify_id = QLineEdit(settings.spotify_client_id or "")
        form.addRow("Spotify Client ID:", self.spotify_id)

        self.spotify_secret = QLineEdit(settings.spotify_client_secret or "")
        self.spotify_secret.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("Spotify Client Secret:", self.spotify_secret)

        self.jobs_spin = QSpinBox()
        self.jobs_spin.setRange(1, 8)
        self.jobs_spin.setValue(settings.concurrent_jobs)
        form.addRow("Concurrent downloads:", self.jobs_spin)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _browse(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "Choose download folder", self.out_edit.text())
        if d:
            self.out_edit.setText(d)

    def _browse_cookies(self) -> None:
        f, _ = QFileDialog.getOpenFileName(self, "Choose cookies file")
        if f:
            self.cookies_edit.setText(f)

    def accept(self) -> None:
        self.settings.output_template = self.template_edit.text().strip() or "{title}.{ext}"
        if self.out_edit.text().strip():
            self.settings.download_dir = Path(self.out_edit.text().strip())
        self.settings.proxy = self.proxy_edit.text().strip() or None
        self.settings.rate_limit = self.rate_edit.text().strip() or None
        if self.cookies_edit.text().strip():
            self.settings.cookies_path = Path(self.cookies_edit.text().strip())
        self.settings.spotify_client_id = self.spotify_id.text().strip() or None
        self.settings.spotify_client_secret = self.spotify_secret.text().strip() or None
        self.settings.concurrent_jobs = self.jobs_spin.value()
        self.result = True
        super().accept()
