"""Run validated Python tests in disposable Docker containers."""

from __future__ import annotations

import subprocess
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

from app.execution.runner import (
    ExecutionPolicy,
    validate_execution_request,
)


@dataclass(frozen=True)
class ExecutionResult:
    exit_code: int | None
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool
    output_truncated: bool


class DockerRunnerError(RuntimeError):
    """Raised when Docker cannot safely start or manage a run."""


class _BoundedCapture:
    """Capture at most a fixed number of bytes from a process stream."""

    def __init__(self, limit: int) -> None:
        if limit < 0:
            raise ValueError("limit cannot be negative.")
        self.limit = limit
        self.data = bytearray()
        self.truncated = False
        self._lock = threading.Lock()

    def read_from(self, stream) -> None:
        try:
            while True:
                chunk = stream.read(8192)
                if not chunk:
                    break

                with self._lock:
                    remaining = self.limit - len(self.data)
                    if remaining > 0:
                        self.data.extend(chunk[:remaining])
                    if len(chunk) > max(remaining, 0):
                        self.truncated = True
        finally:
            stream.close()

    def result(self) -> tuple[bytes, bool]:
        with self._lock:
            return bytes(self.data), self.truncated


class DockerTestRunner:
    def __init__(
        self,
        policy: ExecutionPolicy | None = None,
        image: str = "devpilot-sandbox:0.9",
    ) -> None:
        self.policy = policy or ExecutionPolicy()
        if image != "devpilot-sandbox:0.9":
            raise ValueError("Only the approved Python image is allowed.")
        if self.policy.max_output_bytes < 0:
            raise ValueError("max_output_bytes cannot be negative.")
        self.image = image

    def run_test(
        self,
        target: str,
        *,
        workspace: str,
    ) -> ExecutionResult:
        request = validate_execution_request(target, workspace=workspace)
        root = Path(workspace).resolve()
        started = time.monotonic()
        container_name = f"devpilot-test-{uuid.uuid4().hex[:16]}"
        created = False

        create_command = [
            "docker", "create",
            "--name", container_name,
            "--network=none",
            "--read-only",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            "--pids-limit", str(self.policy.pids_limit),
            "--memory", self.policy.memory_limit,
            "--cpus", str(self.policy.cpus),
            "--user", "65534:65534",
            "--tmpfs", "/tmp:rw,noexec,nosuid,size=16m,mode=1777",
            "--mount", f"type=bind,source={root},target=/workspace,readonly",
            "--workdir", "/workspace",
            self.image,
            "python", "-I", "-B", "-m", "pytest", "-q",
            "-p", "no:cacheprovider", request.target,
        ]

        try:
            creation = subprocess.run(
                create_command,
                shell=False,
                capture_output=True,
                timeout=15,
                check=False,
            )
            if creation.returncode != 0:
                raise DockerRunnerError(
                    "Docker could not create the test container: "
                    + _decode_bounded(creation.stderr, 4096)
                )

            created = True
            limit = self.policy.max_output_bytes
            stdout_capture = _BoundedCapture(limit // 2)
            stderr_capture = _BoundedCapture(limit - limit // 2)

            process = subprocess.Popen(
                ["docker", "start", "--attach", container_name],
                shell=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            assert process.stdout is not None
            assert process.stderr is not None

            stdout_thread = threading.Thread(
                target=stdout_capture.read_from,
                args=(process.stdout,),
                daemon=True,
            )
            stderr_thread = threading.Thread(
                target=stderr_capture.read_from,
                args=(process.stderr,),
                daemon=True,
            )
            stdout_thread.start()
            stderr_thread.start()

            try:
                exit_code = process.wait(
                    timeout=self.policy.timeout_seconds
                )
                timed_out = False
            except subprocess.TimeoutExpired:
                timed_out = True
                process.kill()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    pass

                # Explicitly stop the container after killing the Docker CLI.
                try:
                    subprocess.run(
                        ["docker", "stop", "--time", "1", container_name],
                        shell=False,
                        capture_output=True,
                        timeout=5,
                        check=False,
                    )
                except (OSError, subprocess.TimeoutExpired):
                    pass

                exit_code = None

            stdout_thread.join(timeout=5)
            stderr_thread.join(timeout=5)

            stdout, stdout_cut = stdout_capture.result()
            stderr, stderr_cut = stderr_capture.result()

            return ExecutionResult(
                exit_code=exit_code,
                stdout=stdout.decode("utf-8", errors="replace"),
                stderr=stderr.decode("utf-8", errors="replace"),
                duration_seconds=time.monotonic() - started,
                timed_out=timed_out,
                output_truncated=stdout_cut or stderr_cut,
            )

        except (OSError, subprocess.TimeoutExpired) as exc:
            if isinstance(exc, subprocess.TimeoutExpired):
                raise DockerRunnerError(
                    "Docker did not respond while creating the test container."
                ) from exc
            raise DockerRunnerError(
                "Could not start Docker. Check that Docker Desktop is running."
            ) from exc
        finally:
            if created:
                try:
                    subprocess.run(
                        ["docker", "rm", "--force", container_name],
                        shell=False,
                        capture_output=True,
                        timeout=10,
                        check=False,
                    )
                except (OSError, subprocess.TimeoutExpired):
                    pass


def _as_bounded_bytes(
    value: bytes | str | None,
    limit: int,
) -> tuple[bytes, bool]:
    if limit < 0:
        raise ValueError("limit cannot be negative.")

    if value is None:
        raw = b""
    elif isinstance(value, str):
        raw = value.encode("utf-8", errors="replace")
    else:
        raw = value

    if len(raw) <= limit:
        return raw, False

    return raw[:limit], True


def _decode_bounded(value: bytes | str | None, limit: int) -> str:
    output, _ = _as_bounded_bytes(value, limit)
    return output.decode("utf-8", errors="replace")
