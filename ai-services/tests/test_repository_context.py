from pathlib import Path

import pytest

from app.repository.context import build_repository_context


def test_empty_repository(tmp_path: Path):
    context = build_repository_context(tmp_path)

    assert context.file_count == 0
    assert context.directory_count == 0
    assert context.files == []
    assert context.languages == []
    assert context.truncated is False


def test_discovers_repository_structure(tmp_path: Path):
    (tmp_path / "backend").mkdir()
    (tmp_path / "backend" / "main.go").write_text("package main")
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "main.py").write_text("print('hello')")
    (tmp_path / "README.md").write_text("# DevPilot")

    context = build_repository_context(tmp_path)

    assert "backend/main.go" in context.files
    assert "app/main.py" in context.files
    assert "README.md" in context.files

    assert "backend" in context.directories
    assert "app" in context.directories


def test_ignores_generated_and_environment_directories(tmp_path: Path):
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "main.py").write_text("print('hello')")

    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("git")

    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / "test.py").write_text("test")

    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "foo.pyc").write_bytes(b"test")

    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "index.js").write_text("test")

    context = build_repository_context(tmp_path)

    assert context.files == ["app/main.py"]
    assert ".git/config" not in context.files
    assert ".venv/test.py" not in context.files
    assert "__pycache__/foo.pyc" not in context.files
    assert "node_modules/index.js" not in context.files


def test_ignores_environment_files(tmp_path: Path):
    (tmp_path / "main.py").write_text("print('hello')")
    (tmp_path / ".env").write_text("SECRET=value")
    (tmp_path / ".env.local").write_text("SECRET=value")

    context = build_repository_context(tmp_path)

    assert "main.py" in context.files
    assert ".env" not in context.files
    assert ".env.local" not in context.files


def test_detects_languages(tmp_path: Path):
    (tmp_path / "main.py").write_text("print('hello')")
    (tmp_path / "server.go").write_text("package main")
    (tmp_path / "app.ts").write_text("const app = true")

    context = build_repository_context(tmp_path)

    assert context.languages == ["Go", "Python", "TypeScript"]


def test_file_limit_sets_truncated(tmp_path: Path):
    for index in range(5):
        (tmp_path / f"file_{index}.py").write_text("print('test')")

    context = build_repository_context(
        tmp_path,
        max_files=3,
    )

    assert context.file_count <= 3
    assert context.truncated is True


def test_directory_limit_sets_truncated(tmp_path: Path):
    for index in range(5):
        (tmp_path / f"dir_{index}").mkdir()

    context = build_repository_context(
        tmp_path,
        max_directories=3,
    )

    assert context.directory_count <= 3
    assert context.truncated is True


def test_missing_workspace_raises_value_error(tmp_path: Path):
    missing = tmp_path / "does-not-exist"

    with pytest.raises(ValueError, match="Workspace does not exist"):
        build_repository_context(missing)


def test_file_as_workspace_raises_value_error(tmp_path: Path):
    file_path = tmp_path / "file.txt"
    file_path.write_text("test")

    with pytest.raises(ValueError, match="Workspace is not a directory"):
        build_repository_context(file_path)
def test_context_skips_external_symlinks(tmp_path: Path):
    outside_file = tmp_path.parent / "outside_context_secret.py"
    outside_file.write_text(
        "OUTSIDE_CONTEXT_MARKER",
        encoding="utf-8",
    )

    outside_dir = tmp_path.parent / "outside_context_folder"
    outside_dir.mkdir()
    (outside_dir / "external.py").write_text(
        "print('outside')",
        encoding="utf-8",
    )

    file_link = tmp_path / "external_file_link.py"
    dir_link = tmp_path / "external_directory_link"

    try:
        file_link.symlink_to(outside_file)
        dir_link.symlink_to(outside_dir, target_is_directory=True)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"Symlink creation is unavailable: {exc}")

    context = build_repository_context(tmp_path)

    assert "external_file_link.py" not in context.files
    assert "external_directory_link/external.py" not in context.files
    assert "external_directory_link" not in context.directories
