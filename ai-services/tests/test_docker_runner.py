from pathlib import Path
from subprocess import CompletedProcess, TimeoutExpired
from unittest.mock import patch

import pytest

from app.execution.docker_runner import (
    DockerRunnerError,
    DockerTestRunner,
    _as_bounded_bytes,
)


def test_output_is_truncated():
    output, truncated = _as_bounded_bytes(b"abcdefgh", 4)
    assert output == b"abcd"
    assert truncated is True


def test_small_output_is_not_truncated():
    output, truncated = _as_bounded_bytes(b"abc", 4)
    assert output == b"abc"
    assert truncated is False


def test_negative_output_limit_is_rejected():
    with pytest.raises(ValueError):
        _as_bounded_bytes(b"abc", -1)


def test_docker_creation_failure_is_reported(tmp_path: Path):
    test_file = tmp_path / "test_example.py"
    test_file.write_text("def test_ok(): assert True\n", encoding="utf-8")

    failure = CompletedProcess(
        args=["docker", "create"],
        returncode=1,
        stdout=b"",
        stderr=b"image not found",
    )

    with patch(
        "app.execution.docker_runner.subprocess.run",
        return_value=failure,
    ) as mocked_run:
        runner = DockerTestRunner()
        with pytest.raises(DockerRunnerError, match="could not create"):
            runner.run_test("test_example.py", workspace=str(tmp_path))

    # A container that was never created should not be removed.
    assert mocked_run.call_count == 1


def test_invalid_target_is_rejected_before_docker(tmp_path: Path):
    with patch(
        "app.execution.docker_runner.subprocess.run"
    ) as mocked_run:
        with pytest.raises(ValueError):
            DockerTestRunner().run_test(
                "../outside.py",
                workspace=str(tmp_path),
            )

    mocked_run.assert_not_called()
def test_timeout_attempts_container_cleanup(tmp_path: Path):
    import io

    test_file = tmp_path / "test_example.py"
    test_file.write_text("def test_ok(): assert True\n", encoding="utf-8")

    created = CompletedProcess(
        args=["docker", "create"],
        returncode=0,
        stdout=b"container-id",
        stderr=b"",
    )
    cleanup = CompletedProcess(
        args=["docker", "rm"],
        returncode=0,
        stdout=b"",
        stderr=b"",
    )

    class FakeProcess:
        def __init__(self, *args, **kwargs):
            self.stdout = io.BytesIO(b"partial output")
            self.stderr = io.BytesIO(b"")
            self.wait_calls = 0
            self.killed = False

        def wait(self, timeout=None):
            self.wait_calls += 1
            if self.wait_calls == 1:
                raise TimeoutExpired(cmd=["docker", "start"], timeout=timeout)
            return -9

        def kill(self):
            self.killed = True

    fake_process = FakeProcess()

    with (
        patch(
            "app.execution.docker_runner.subprocess.run",
            side_effect=[created, cleanup, cleanup],
        ) as mocked_run,
        patch(
            "app.execution.docker_runner.subprocess.Popen",
            return_value=fake_process,
        ),
    ):
        result = DockerTestRunner().run_test(
            "test_example.py",
            workspace=str(tmp_path),
        )

    assert result.timed_out is True
    assert result.exit_code is None
    assert fake_process.killed is True
    assert mocked_run.call_count == 3

    stop_command = mocked_run.call_args_list[1].args[0]
    assert stop_command[:3] == ["docker", "stop", "--time"]

    cleanup_command = mocked_run.call_args_list[2].args[0]
    assert cleanup_command[:3] == ["docker", "rm", "--force"]
