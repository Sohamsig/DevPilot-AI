from pathlib import Path

import pytest

from app.tools import repository
from app.tools.repository import (
    list_files,
    list_top_level_folders,
    read_file,
    search_code,
)

@pytest.fixture
def workspace(tmp_path: Path, monkeypatch) -> Path:
    """Create an isolated fake repository for the test."""

    workspace = tmp_path

    monkeypatch.setattr(
        repository.settings,
        "workspace_root",
        str(workspace),
    )

    (workspace / "src").mkdir()
    (workspace / ".venv").mkdir()
    (workspace / "node_modules").mkdir()
    (workspace / ".git").mkdir()

    (workspace / "src" / "main.py").write_text(
        "def hello():\n"
        "    return 'hello'\n",
        encoding="utf-8",
    )

    (workspace / "src" / "config.py").write_text(
        "DATABASE = 'mongodb://localhost:27017'\n",
        encoding="utf-8",
    )

    (workspace / ".env").write_text(
        "SECRET_KEY=super-secret\n"
        "MONGO_URI=mongodb://secret-user:secret-password@host\n",
        encoding="utf-8",
    )

    (workspace / ".venv" / "ignored.py").write_text(
        "should not appear",
        encoding="utf-8",
    )

    (workspace / "node_modules" / "ignored.js").write_text(
        "should not appear",
        encoding="utf-8",
    )

    (workspace / ".git" / "config").write_text(
        "should not appear",
        encoding="utf-8",
    )

    return workspace

def test_list_files_returns_source_files(workspace):
    result = list_files.invoke(
        {"workspace_path": str(workspace)}
    )

    assert "src/main.py" in result
    assert "src/config.py" in result


def test_list_files_excludes_env(workspace):
    result = list_files.invoke(
        {"workspace_path": str(workspace)}
    )

    assert ".env" not in result


def test_list_files_excludes_venv(workspace):
    result = list_files.invoke(
        {"workspace_path": str(workspace)}
    )

    assert ".venv" not in result


def test_list_files_excludes_node_modules(workspace):
    result = list_files.invoke(
        {"workspace_path": str(workspace)}
    )

    assert "node_modules" not in result


def test_list_files_excludes_git(workspace):
    result = list_files.invoke(
        {"workspace_path": str(workspace)}
    )

    assert ".git" not in result


def test_read_file_reads_source_file(workspace):
    result = read_file.invoke(
        {
            "file_path": "src/main.py",
            "workspace_path": str(workspace),
        }
    )

    assert "def hello()" in result
    assert "return 'hello'" in result


def test_read_file_handles_missing_file(workspace):
    result = read_file.invoke(
        {
            "file_path": "src/missing.py",
            "workspace_path": str(workspace),
        }
    )

    assert "File not found" in result


def test_read_file_rejects_path_traversal(workspace):
    with pytest.raises(ValueError, match="outside"):
        read_file.invoke(
            {
                "file_path": "../secret.txt",
                "workspace_path": str(workspace),
            }
        )


def test_search_code_finds_matching_source(workspace):
    result = search_code.invoke(
        {
            "query": "mongodb",
            "workspace_path": str(workspace),
        }
    )

    assert "src/config.py" in result
    assert "mongodb" in result.lower()


def test_search_code_handles_no_match(workspace):
    result = search_code.invoke(
        {
            "query": "something_that_does_not_exist",
            "workspace_path": str(workspace),
        }
    )

    assert "No matches found" in result


def test_search_code_does_not_return_env_content(workspace):
    result = search_code.invoke(
        {
            "query": "SECRET_KEY",
            "workspace_path": str(workspace),
        }
    )

    assert "super-secret" not in result
def test_list_files_skips_external_symlink(workspace, tmp_path):
    outside_file = workspace.parent / "outside_repository_secret.py"
    outside_file.write_text(
        "OUTSIDE_REPOSITORY_MARKER",
        encoding="utf-8",
    )

    link = workspace / "src" / "external_link.py"

    try:
        link.symlink_to(outside_file)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"Symlink creation is unavailable: {exc}")

    result = list_files.invoke(
        {"workspace_path": str(workspace)}
    )

    assert "src/external_link.py" not in result
    assert "outside_repository_secret.py" not in result


def test_search_code_skips_external_symlink(workspace):
    outside_file = workspace.parent / "outside_search_secret.py"
    outside_file.write_text(
        "UNIQUE_OUTSIDE_SEARCH_MARKER",
        encoding="utf-8",
    )

    link = workspace / "src" / "external_search.py"

    try:
        link.symlink_to(outside_file)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"Symlink creation is unavailable: {exc}")

    result = search_code.invoke(
        {
            "query": "UNIQUE_OUTSIDE_SEARCH_MARKER",
            "workspace_path": str(workspace),
        }
    )

    assert "UNIQUE_OUTSIDE_SEARCH_MARKER" not in result
    assert "external_search.py" not in result


def test_list_top_level_folders_skips_external_symlink(workspace):
    outside_dir = workspace.parent / "outside_repository_folder"
    outside_dir.mkdir()
    (outside_dir / "external.py").write_text(
        "print('outside')",
        encoding="utf-8",
    )

    link = workspace / "external_folder_link"

    try:
        link.symlink_to(outside_dir, target_is_directory=True)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"Directory symlink creation is unavailable: {exc}")

    result = list_top_level_folders.invoke(
        {"workspace_path": str(workspace)}
    )

    assert "src" in result.splitlines()
    assert "external_folder_link" not in result.splitlines()


def test_read_file_rejects_external_symlink(workspace):
    outside_file = workspace.parent / "outside_read_secret.py"
    outside_file.write_text(
        "OUTSIDE_READ_MARKER",
        encoding="utf-8",
    )

    link = workspace / "src" / "external_read.py"

    try:
        link.symlink_to(outside_file)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"Symlink creation is unavailable: {exc}")

    with pytest.raises(ValueError, match="outside"):
        read_file.invoke(
            {
                "file_path": "src/external_read.py",
                "workspace_path": str(workspace),
            }
        )

def test_search_code_excludes_backup_files(workspace):
    from app.tools.repository import search_code

    (workspace / "main.py").write_text(
        '@app.get("/health")' + "\n",
        encoding="utf-8",
    )
    (workspace / "main.py.bak").write_text(
        '@app.get("/health")' + "\n",
        encoding="utf-8",
    )
    (workspace / "main.py.bak-20261023-083901").write_text(
        '@app.get("/health")' + "\n",
        encoding="utf-8",
    )
    (workspace / "main.py.orig").write_text(
        '@app.get("/health")' + "\n",
        encoding="utf-8",
    )

    result = search_code.invoke({
        "query": '@app.get("/health")',
        "workspace_path": str(workspace),
    })

    assert "main.py:" in result
    assert "main.py.bak:" not in result
    assert "main.py.bak-" not in result
    assert "main.py.orig:" not in result


def test_list_files_excludes_backup_files(workspace):
    from app.tools.repository import list_files

    (workspace / "main.py").write_text(
        "print('current')\n",
        encoding="utf-8",
    )
    (workspace / "main.py.bak").write_text(
        "print('backup')\n",
        encoding="utf-8",
    )
    (workspace / "main.py.old").write_text(
        "print('old')\n",
        encoding="utf-8",
    )

    result = list_files.invoke({
        "workspace_path": str(workspace),
    })

    assert "main.py" in result.splitlines()
    assert "main.py.bak" not in result.splitlines()
    assert "main.py.old" not in result.splitlines()



