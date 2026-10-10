import pytest

from app.tools.code_changes import build_file_diff


def test_preview_shows_diff_without_modifying_file(tmp_path):
    source = tmp_path / "main.py"
    source.write_text("print('old')\n", encoding="utf-8")

    diff = build_file_diff(
        file_path="main.py",
        proposed_content="print('new')\n",
        workspace_path=str(tmp_path),
    )

    assert "--- a/main.py" in diff
    assert "+++ b/main.py" in diff
    assert "-print('old')" in diff
    assert "+print('new')" in diff
    assert source.read_text(encoding="utf-8") == "print('old')\n"


def test_preview_rejects_path_traversal(tmp_path):
    with pytest.raises(ValueError, match="outside"):
        build_file_diff(
            file_path="../outside.py",
            proposed_content="changed = True\n",
            workspace_path=str(tmp_path),
        )


def test_preview_rejects_env_file(tmp_path):
    (tmp_path / ".env").write_text(
        "API_KEY=example\n", encoding="utf-8"
    )

    with pytest.raises(ValueError, match="not allowed"):
        build_file_diff(
            file_path=".env",
            proposed_content="API_KEY=changed\n",
            workspace_path=str(tmp_path),
        )


def test_preview_handles_missing_file(tmp_path):
    result = build_file_diff(
        file_path="missing.py",
        proposed_content="print('hello')\n",
        workspace_path=str(tmp_path),
    )

    assert result == "File not found: missing.py"


def test_preview_handles_identical_content(tmp_path):
    source = tmp_path / "main.py"
    source.write_text("print('hello')\n", encoding="utf-8")

    result = build_file_diff(
        file_path="main.py",
        proposed_content="print('hello')\n",
        workspace_path=str(tmp_path),
    )

    assert result == "No changes proposed."
