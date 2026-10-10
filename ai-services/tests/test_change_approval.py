import pytest

from app.tools.change_approval import (
    approve_proposal,
    create_proposal,
    reject_proposal,
)


def test_approval_applies_proposed_change(tmp_path):
    source = tmp_path / "main.py"
    source.write_text("old = True\n", encoding="utf-8")

    proposal = create_proposal(
        "main.py",
        "new = True\n",
        str(tmp_path),
    )

    assert source.read_text(encoding="utf-8") == "old = True\n"

    result = approve_proposal(proposal["proposal_id"])

    assert result["status"] == "applied"
    assert source.read_text(encoding="utf-8") == "new = True\n"


def test_rejection_does_not_modify_file(tmp_path):
    source = tmp_path / "main.py"
    source.write_text("old = True\n", encoding="utf-8")

    proposal = create_proposal(
        "main.py",
        "new = True\n",
        str(tmp_path),
    )

    result = reject_proposal(proposal["proposal_id"])

    assert result["status"] == "rejected"
    assert source.read_text(encoding="utf-8") == "old = True\n"


def test_stale_proposal_cannot_overwrite_changed_file(tmp_path):
    source = tmp_path / "main.py"
    source.write_text("old = True\n", encoding="utf-8")

    proposal = create_proposal(
        "main.py",
        "new = True\n",
        str(tmp_path),
    )

    source.write_text("changed elsewhere = True\n", encoding="utf-8")

    with pytest.raises(ValueError, match="File changed"):
        approve_proposal(proposal["proposal_id"])

    assert source.read_text(encoding="utf-8") == "changed elsewhere = True\n"


def test_proposal_cannot_be_applied_twice(tmp_path):
    source = tmp_path / "main.py"
    source.write_text("old = True\n", encoding="utf-8")

    proposal = create_proposal(
        "main.py",
        "new = True\n",
        str(tmp_path),
    )

    approve_proposal(proposal["proposal_id"])

    with pytest.raises(ValueError, match="no longer pending"):
        approve_proposal(proposal["proposal_id"])


def test_proposal_rejects_path_traversal(tmp_path):
    with pytest.raises(ValueError, match="outside"):
        create_proposal(
            "../outside.py",
            "new = True\n",
            str(tmp_path),
        )