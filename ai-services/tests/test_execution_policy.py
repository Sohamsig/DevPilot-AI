
import pytest

from app.execution.runner import (
    ExecutionPolicy,
    truncate_output,
    validate_execution_request,
)


def test_accepts_test_file_inside_workspace(tmp_path):
    test_file = tmp_path / "tests" / "test_example.py"
    test_file.parent.mkdir()
    test_file.write_text("def test_example():\n    assert True\n")

    request = validate_execution_request(
        "tests/test_example.py",
        workspace=str(tmp_path),
    )

    assert request.target == "tests/test_example.py"


@pytest.mark.parametrize(
    "target",
    [
        "",
        "../test_escape.py",
        "/tmp/test_escape.py",
        "tests\\test_example.py",
        "tests/run.py",
        "tests/test_example.py;whoami",
        "tests/test_example.py\x00",
    ],
)
def test_rejects_unsafe_targets(tmp_path, target):
    with pytest.raises(ValueError):
        validate_execution_request(target, workspace=str(tmp_path))


def test_rejects_missing_test_file(tmp_path):
    with pytest.raises(ValueError, match="does not exist"):
        validate_execution_request(
            "tests/test_missing.py",
            workspace=str(tmp_path),
        )


def test_rejects_symlink_escape(tmp_path):
    outside = tmp_path.parent / "outside_test.py"
    outside.write_text("def test_escape():\n    assert True\n")

    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    link = tests_dir / "test_escape.py"

    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("Symlink creation is unavailable on this system.")

    with pytest.raises(ValueError, match="escapes the workspace"):
        validate_execution_request(
            "tests/test_escape.py",
            workspace=str(tmp_path),
        )


def test_truncates_oversized_output():
    output, truncated = truncate_output(b"abcdefgh", 4)

    assert output == b"abcd"
    assert truncated is True


def test_preserves_small_output():
    output, truncated = truncate_output(b"hello", 10)

    assert output == b"hello"
    assert truncated is False


def test_policy_has_conservative_defaults():
    policy = ExecutionPolicy()

    assert policy.timeout_seconds == 30
    assert policy.max_output_bytes == 64 * 1024
    assert policy.pids_limit == 64
