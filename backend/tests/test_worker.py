import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

from hellofedge import worker
from hellofedge.config import Settings


def make_settings(heartbeat_file: Path, max_age: int = 120) -> Settings:
    return Settings(
        _env_file=None,
        database_url="postgresql://u:p@h/db",
        worker_heartbeat_file=heartbeat_file,
        worker_heartbeat_max_age_seconds=max_age,
    )


class TestHealthCheck:
    """`hellofedge-worker --check` : le contrôle de santé utilisé par Docker."""

    NOW = 1_000_000.0

    @pytest.fixture(autouse=True)
    def frozen_clock(self, monkeypatch):
        monkeypatch.setattr(worker.time, "time", lambda: self.NOW)

    def test_healthy_when_the_heartbeat_is_recent(self, tmp_path):
        hb = tmp_path / "hb"
        hb.write_text(str(self.NOW - 10))

        assert worker.check(make_settings(hb)) == 0

    def test_still_healthy_exactly_at_the_maximum_age(self, tmp_path):
        hb = tmp_path / "hb"
        hb.write_text(str(self.NOW - 120))

        assert worker.check(make_settings(hb)) == 0

    def test_unhealthy_once_the_heartbeat_is_older_than_the_maximum_age(self, tmp_path):
        hb = tmp_path / "hb"
        hb.write_text(str(self.NOW - 121))

        assert worker.check(make_settings(hb)) == 1

    def test_unhealthy_when_the_worker_never_wrote_a_heartbeat(self, tmp_path):
        assert worker.check(make_settings(tmp_path / "absent")) == 1

    @pytest.mark.parametrize("content", ["", "pas un nombre", "12:30"])
    def test_unhealthy_when_the_heartbeat_file_is_unreadable(self, tmp_path, content):
        hb = tmp_path / "hb"
        hb.write_text(content)

        assert worker.check(make_settings(hb)) == 1

    def test_a_heartbeat_written_by_the_worker_is_read_back_as_healthy(self, tmp_path):
        settings = make_settings(tmp_path / "hb")

        worker.touch_heartbeat(settings)

        assert worker.check(settings) == 0

    def test_check_flag_exits_with_the_health_code(self, tmp_path, monkeypatch):
        hb = tmp_path / "hb"
        hb.write_text(str(self.NOW - 500))
        monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@h/db")
        monkeypatch.setenv("WORKER_HEARTBEAT_FILE", str(hb))
        monkeypatch.setattr(sys, "argv", ["hellofedge-worker", "--check"])

        with pytest.raises(SystemExit) as exit_info:
            worker.main()

        assert exit_info.value.code == 1


# Le worker réel, lancé comme sur le serveur, contre une vraie base.


def worker_env(db_url: str, heartbeat_file: Path) -> dict[str, str]:
    return {
        **os.environ,
        "DATABASE_URL": db_url,
        "WORKER_HEARTBEAT_FILE": str(heartbeat_file),
        "WORKER_HEARTBEAT_SECONDS": "1",
    }


def start_worker(db_url: str, heartbeat_file: Path) -> subprocess.Popen[str]:
    return subprocess.Popen(
        [sys.executable, "-m", "hellofedge.worker"],
        env=worker_env(db_url, heartbeat_file),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def wait_for(path: Path, timeout: float = 15.0) -> None:
    deadline = time.monotonic() + timeout
    while not path.exists():
        if time.monotonic() > deadline:
            raise AssertionError(f"{path} jamais écrit en {timeout} s")
        time.sleep(0.1)


def stop(proc: subprocess.Popen[str]) -> tuple[int, list[dict]]:
    proc.send_signal(signal.SIGTERM)
    out, _ = proc.communicate(timeout=15)
    return proc.returncode, [
        json.loads(line) for line in out.splitlines() if line.strip()
    ]


@pytest.fixture
def running_worker(db_url, tmp_path):
    hb = tmp_path / "first-hb"
    proc = start_worker(db_url, hb)
    try:
        wait_for(hb)
        yield proc, hb
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.communicate()


class TestSingleWorker:
    def test_the_first_worker_takes_the_lock_and_writes_its_heartbeat(
        self, running_worker
    ):
        proc, hb = running_worker

        assert proc.poll() is None
        assert float(hb.read_text()) <= time.time()

    def test_the_heartbeat_keeps_moving_while_the_worker_runs(self, running_worker):
        _, hb = running_worker
        first = float(hb.read_text())

        time.sleep(2.5)

        assert float(hb.read_text()) > first

    def test_a_second_copy_refuses_to_run_and_exits_with_code_1(
        self, running_worker, db_url, tmp_path
    ):
        second_hb = tmp_path / "second-hb"

        result = subprocess.run(
            [sys.executable, "-m", "hellofedge.worker"],
            env=worker_env(db_url, second_hb),
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 1
        entry = json.loads(result.stdout.strip().splitlines()[-1])
        assert entry["level"] == "ERROR"
        assert entry["msg"] == "arrêt : un autre worker tient déjà le verrou"
        assert not second_hb.exists()

    def test_stops_cleanly_on_sigterm_with_json_logs(self, running_worker):
        proc, _ = running_worker

        code, entries = stop(proc)

        assert code == 0
        assert [e["msg"] for e in entries] == [
            "worker démarré, verrou obtenu",
            "worker arrêté proprement",
        ]

    def test_the_lock_is_released_after_a_clean_stop(
        self, running_worker, db_url, tmp_path
    ):
        proc, _ = running_worker
        stop(proc)
        next_hb = tmp_path / "next-hb"

        successor = start_worker(db_url, next_hb)
        try:
            wait_for(next_hb)
            assert successor.poll() is None
        finally:
            code, _ = stop(successor)

        assert code == 0

    def test_a_dead_worker_releases_the_lock(self, running_worker, db_url, tmp_path):
        # Un plantage brutal ferme la connexion : PostgreSQL libère le verrou de lui même.
        proc, _ = running_worker
        proc.kill()
        proc.communicate()
        next_hb = tmp_path / "next-hb"

        successor = start_worker(db_url, next_hb)
        try:
            wait_for(next_hb)
            assert successor.poll() is None
        finally:
            stop(successor)


def test_the_worker_fails_loudly_when_the_database_is_unreachable(tmp_path):
    hb = tmp_path / "hb"

    result = subprocess.run(
        [sys.executable, "-m", "hellofedge.worker"],
        env=worker_env("postgresql://u:p@127.0.0.1:1/db", hb),
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode != 0
    assert not hb.exists()
