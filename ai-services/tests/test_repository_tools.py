from pathlib import Path

import pytest

from app.tools import repository
from app.tools.repository import (
    list_files,
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