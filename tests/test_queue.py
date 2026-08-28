"""Tests for the threaded download queue (pure core, no network / GUI)."""


from downloader.core.models import DownloadRequest, DownloadTask, Format, Status
from downloader.core.queue import DownloadQueue


class _FakeEngine:
    def __init__(self, fail: bool = False):
        self.fail = fail

    def download(self, request, **kwargs):
        from downloader.core.models import DownloadResult

        if self.fail:
            return DownloadResult(request=request, status=Status.FAILED, error="boom")
        return DownloadResult(request=request, status=Status.COMPLETED, path=request.out_dir / "x.mp4")


def test_queue_completes(tmp_path):
    updates = []
    q = DownloadQueue(
        on_task_update=lambda t: updates.append(t.status),
        concurrent_jobs=1,
        engine_factory=lambda site, *a, **kw: _FakeEngine(),
    )
    q.start()

    task = DownloadTask(
        request=DownloadRequest(url="https://example.com/v", out_dir=tmp_path, fmt=Format.MP4)
    )
    q.add(task)
    q.wait()
    q.stop()

    assert task.status == Status.COMPLETED
    assert task.result is not None
    assert task.result.path is not None
    assert Status.FAILED not in updates


def test_queue_failure(tmp_path):
    q = DownloadQueue(
        concurrent_jobs=1,
        engine_factory=lambda site, *a, **kw: _FakeEngine(fail=True),
    )
    q.start()

    task = DownloadTask(
        request=DownloadRequest(url="https://example.com/v", out_dir=tmp_path, fmt=Format.BEST)
    )
    q.add(task)
    q.wait()
    q.stop()

    assert task.status == Status.FAILED
    assert task.result.error == "boom"
