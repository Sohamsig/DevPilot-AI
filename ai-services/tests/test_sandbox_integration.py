from pathlib import Path

import pytest

from app.execution.docker_runner import DockerTestRunner
from app.execution.runner import ExecutionPolicy


pytestmark = pytest.mark.docker_integration


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    return tmp_path


def run_sandbox_test(
    workspace: Path,
    source: str,
    *,
    timeout_seconds: int = 10,
):
    (workspace / "test_sandbox_case.py").write_text(
        source,
        encoding="utf-8",
    )

    runner = DockerTestRunner(
        policy=ExecutionPolicy(timeout_seconds=timeout_seconds)
    )

    return runner.run_test(
        "test_sandbox_case.py",
        workspace=str(workspace),
    )


def test_network_is_blocked(workspace: Path):
    result = run_sandbox_test(
        workspace,
        """
import socket

def test_no_network():
    sock = socket.socket()
    try:
        sock.settimeout(2)
        with __import__('pytest').raises(OSError):
            sock.connect(("1.1.1.1", 80))
    finally:
        sock.close()
""",
    )

    assert not result.timed_out
    assert result.exit_code == 0, result.stdout + result.stderr
    assert "1 passed" in result.stdout


def test_workspace_is_read_only(workspace: Path):
    result = run_sandbox_test(
        workspace,
        """
from pathlib import Path

def test_cannot_write_workspace():
    target = Path("/workspace/sandbox-write-check.txt")
    try:
        target.write_text("unexpected write")
    except OSError:
        return
    raise AssertionError("Sandbox unexpectedly allowed workspace writes")
""",
    )

    assert not result.timed_out
    assert result.exit_code == 0, result.stdout + result.stderr
    assert "1 passed" in result.stdout
    assert not (workspace / "sandbox-write-check.txt").exists()


def test_execution_timeout(workspace: Path):
    result = run_sandbox_test(
        workspace,
        """
import time

def test_slow():
    time.sleep(10)
""",
        timeout_seconds=2,
    )

    assert result.timed_out is True
    assert result.exit_code is None
