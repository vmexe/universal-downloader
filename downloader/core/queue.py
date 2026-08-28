"""Threaded download queue.

This is a pure-Python queue usable headless. The GUI layer wraps its callbacks
(with signals/threads) but the scheduling logic stays here so it can be tested
without a display.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from queue import Empty, Queue

from downloader.config.settings import load_settings
from downloader.core.downloader import Downloader
from downloader.core.models import (
    DownloadResult,
    DownloadTask,
    Status,
)

log = logging.getLogger(__name__)


class DownloadQueue:
    """A simple worker-pool download queue.

    :param on_task_update: callback ``(task) -> None`` fired on any state change.
    :param concurrent_jobs: number of parallel workers.
    """

    def __init__(
        self,
        on_task_update: Callable[[DownloadTask], None] | None = None,
        concurrent_jobs: int = 2,
        engine_factory: Callable | None = None,
    ) -> None:
        self._on_update = on_task_update
        self._pool = Queue()
        self._tasks: dict[str, DownloadTask] = {}
        self._cancel_event = threading.Event()
        self._workers: list[threading.Thread] = []
        self._lock = threading.Lock()
        self._running = False
        self._concurrent_jobs = concurrent_jobs
        self._engine_factory = engine_factory or self._default_factory

    @staticmethod
    def _default_factory(site, client_id=None, client_secret=None):
        from downloader.core.engines.factory import get_engine

        return get_engine(site, client_id, client_secret)

    @property
    def tasks(self) -> list[DownloadTask]:
        with self._lock:
            return list(self._tasks.values())

    def add(self, task: DownloadTask) -> DownloadTask:
        with self._lock:
            self._tasks[task.request.url] = task
        self._pool.put(task)
        self._notify(task)
        return task

    def remove(self, key: str) -> DownloadTask | None:
        with self._lock:
            return self._tasks.pop(key, None)

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._cancel_event.clear()
        self._workers = [
            threading.Thread(target=self._worker, name=f"dl-worker-{i}", daemon=True)
            for i in range(self._concurrent_jobs)
        ]
        for w in self._workers:
            w.start()

    def stop(self) -> None:
        self._running = False
        self._cancel_event.set()
        # drain the pool so workers exit.
        while True:
            try:
                self._pool.get_nowait()
            except Empty:
                break
        for w in self._workers:
            w.join(timeout=2)
        self._workers.clear()

    def wait(self) -> None:
        """Block until all queued tasks have been processed."""
        self._pool.join()

    # -- internals --------------------------------------------------------
    def _worker(self) -> None:
        while self._running and not self._cancel_event.is_set():
            try:
                task = self._pool.get(timeout=0.2)
            except Empty:
                continue

            if self._cancel_event.is_set():
                task.status = Status.CANCELLED
                self._notify(task)
                continue

            self._execute(task)
            self._pool.task_done()

    def _execute(self, task: DownloadTask) -> None:
        task.status = Status.RUNNING
        self._notify(task)
        try:
            settings = load_settings()
            site = task.request.site
            engine: Downloader = self._engine_factory(
                site,
                settings.spotify_client_id,
                settings.spotify_client_secret,
            )
            result: DownloadResult = engine.download(
                task.request,
                progress=lambda p: self._notify(task),
                cookies=str(settings.cookies_path) if settings.cookies_path else None,
                proxy=settings.proxy,
                rate_limit=settings.rate_limit,
                quality=task.request.quality,
            )
            task.result = result
            task.status = result.status
        except Exception as exc:
            log.exception("worker failed")
            task.status = Status.FAILED
            task.result = DownloadResult(request=task.request, status=Status.FAILED, error=str(exc))
        finally:
            self._notify(task)

    def _notify(self, task: DownloadTask) -> None:
        if self._on_update:
            try:
                self._on_update(task)
            except Exception:
                log.exception("on_task_update callback failed")
