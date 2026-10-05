import subprocess
from types import SimpleNamespace

import hotspots.static_metrics as static_metrics


def test_process_pool_uses_spawn_context(monkeypatch):
    captured = {}
    sentinel = object()

    def fake_executor(**kwargs):
        captured.update(kwargs)
        return sentinel

    monkeypatch.setattr(static_metrics, "ProcessPoolExecutor", fake_executor)

    executor = static_metrics._create_executor(4)

    assert executor is sentinel
    assert captured["max_workers"] == 4
    assert captured["mp_context"].get_start_method() == "spawn"
    assert static_metrics._create_executor(1) is None


def test_cat_file_is_terminated_defensively_when_it_does_not_exit(monkeypatch):
    class FakeStream:
        def __init__(self):
            self.closed = False

        def close(self):
            self.closed = True

    class FakeProcess:
        def __init__(self):
            self.stdin = FakeStream()
            self.stdout = FakeStream()
            self.wait_calls = 0
            self.terminated = False
            self.killed = False

        def wait(self, timeout=None):
            self.wait_calls += 1
            if self.wait_calls == 1:
                raise subprocess.TimeoutExpired("git cat-file", timeout)
            return 0

        def terminate(self):
            self.terminated = True

        def kill(self):
            self.killed = True

    process = FakeProcess()
    monkeypatch.setattr(
        static_metrics.subprocess,
        "Popen",
        lambda *args, **kwargs: process,
    )

    assert list(static_metrics._cat_blobs(SimpleNamespace(), [])) == []
    assert process.stdin.closed
    assert process.stdout.closed
    assert process.terminated
    assert not process.killed
    assert process.wait_calls == 2
