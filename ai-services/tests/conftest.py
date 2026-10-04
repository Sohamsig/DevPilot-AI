import pytest

from app.tools import repository


@pytest.fixture(autouse=True)
def isolated_workspace_root(tmp_path, monkeypatch):
    """Run repository-tool tests against an isolated temporary workspace."""
    monkeypatch.setattr(
        repository.settings,
        "workspace_root",
        str(tmp_path),
    )
    return tmp_path
