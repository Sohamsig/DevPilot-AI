from pathlib import Path

def test_workspace_is_read_only():
    target = Path("/workspace/sandbox-write-check.txt")
    try:
        target.write_text("unexpected", encoding="utf-8")
    except OSError:
        return
    raise AssertionError("Workspace unexpectedly allowed writes")
