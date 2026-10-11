
"""Strict execution policy for DevPilot's sandboxed test runner."""

from dataclasses import dataclass
from pathlib import PurePosixPath
import re


@dataclass(frozen=True)
class ExecutionPolicy:
    """Limits for an approved test execution."""

    timeout_seconds: int = 30
    max_output_bytes: int = 64 * 1024
    memory_limit: str = "256m"
    cpus: float = 1.0
    pids_limit: int = 64


@dataclass(frozen=True)
class ExecutionRequest:
    """A validated request to run a specific test target."""

    target: str


_ALLOWED_TARGET = re.compile(r"^[A-Za-z0-9_./-]+\.py$")


def validate_execution_request(
    target: str,
    *,
    workspace: str,
) -> ExecutionRequest:
    """Accept only Python test files inside the configured workspace."""

    if not isinstance(target, str) or not target.strip():
        raise ValueError("Target must be a non-empty relative path.")

    if "\x00" in target or "\\" in target:
        raise ValueError("Target contains unsupported path characters.")

    path = PurePosixPath(target)

    if path.is_absolute() or ".." in path.parts:
        raise ValueError("Target must stay inside the workspace.")

    if not _ALLOWED_TARGET.fullmatch(target):
        raise ValueError("Only simple Python file paths are allowed.")

    if not path.name.startswith("test_"):
        raise ValueError("Only test_*.py files may be executed.")

    # Resolve paths to prevent symlink-based workspace escapes.
    from pathlib import Path

    root = Path(workspace).resolve()
    candidate = (root / Path(*path.parts)).resolve()

    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError("Target escapes the workspace.") from exc

    if not candidate.is_file():
        raise ValueError("Test target does not exist.")

    return ExecutionRequest(target=path.as_posix())


def truncate_output(output: bytes, max_bytes: int) -> tuple[bytes, bool]:
    """Limit captured output and report whether it was truncated."""

    if max_bytes < 0:
        raise ValueError("max_bytes cannot be negative.")

    if len(output) <= max_bytes:
        return output, False

    return output[:max_bytes], True
