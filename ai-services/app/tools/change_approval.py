import difflib
import hashlib
import os
import secrets
import tempfile
from pathlib import Path
from threading import Lock

from app.tools.repository import is_ignored, resolve_workspace


class ChangeProposal:
    def __init__(
        self,
        proposal_id: str,
        workspace: Path,
        target: Path,
        original_content: str,
        proposed_content: str,
        diff: str,
    ):
        self.proposal_id = proposal_id
        self.workspace = workspace
        self.target = target
        self.original_hash = hashlib.sha256(
            original_content.encode("utf-8")
        ).hexdigest()
        self.proposed_content = proposed_content
        self.diff = diff
        self.status = "pending"


_proposals: dict[str, ChangeProposal] = {}
_lock = Lock()


def _validate_target(
    file_path: str,
    workspace_path: str | None,
) -> tuple[Path, Path]:
    workspace = resolve_workspace(workspace_path)
    target = (workspace / file_path).resolve()

    try:
        target.relative_to(workspace)
    except ValueError as exc:
        raise ValueError(
            "File is outside the configured workspace."
        ) from exc

    if is_ignored(target, workspace):
        raise ValueError("Access to this file is not allowed.")

    if not target.is_file():
        raise ValueError("Target must be an existing file.")

    return workspace, target


def create_proposal(
    file_path: str,
    proposed_content: str,
    workspace_path: str | None = None,
) -> dict[str, str]:
    workspace, target = _validate_target(
        file_path,
        workspace_path,
    )

    try:
        original = target.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as exc:
        raise ValueError(
            "Unable to read target as UTF-8 text."
        ) from exc

    diff = "".join(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            proposed_content.splitlines(keepends=True),
            fromfile=f"a/{target.relative_to(workspace).as_posix()}",
            tofile=f"b/{target.relative_to(workspace).as_posix()}",
        )
    )

    if not diff:
        raise ValueError("No changes proposed.")

    proposal_id = secrets.token_urlsafe(24)

    proposal = ChangeProposal(
        proposal_id=proposal_id,
        workspace=workspace,
        target=target,
        original_content=original,
        proposed_content=proposed_content,
        diff=diff,
    )

    with _lock:
        _proposals[proposal_id] = proposal

    return {
        "proposal_id": proposal_id,
        "file_path": target.relative_to(workspace).as_posix(),
        "diff": diff,
        "status": "pending",
    }


def approve_proposal(proposal_id: str) -> dict[str, str]:
    with _lock:
        proposal = _proposals.get(proposal_id)

        if proposal is None:
            raise ValueError("Proposal not found.")

        if proposal.status != "pending":
            raise ValueError("Proposal is no longer pending.")

        # Revalidate the target immediately before writing.
        workspace, target = _validate_target(
            str(proposal.target.relative_to(proposal.workspace)),
            str(proposal.workspace),
        )

        if workspace != proposal.workspace or target != proposal.target:
            raise ValueError("Proposal target validation failed.")

        try:
            current_content = target.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError) as exc:
            raise ValueError(
                "Unable to re-read target file."
            ) from exc

        current_hash = hashlib.sha256(
            current_content.encode("utf-8")
        ).hexdigest()

        if current_hash != proposal.original_hash:
            raise ValueError(
                "File changed since proposal creation. Create a new proposal."
            )

        # Mark as consumed before writing to prevent a second approval.
        proposal.status = "applying"

        # Write to a temporary file, then atomically replace the target.
        temp_path = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="",
                dir=target.parent,
                prefix=f".{target.name}.",
                suffix=".tmp",
                delete=False,
            ) as temp_file:
                temp_path = Path(temp_file.name)
                temp_file.write(proposal.proposed_content)
                temp_file.flush()
                os.fsync(temp_file.fileno())

            os.replace(temp_path, target)
            temp_path = None
        except OSError as exc:
            proposal.status = "failed"
            raise ValueError("Unable to apply approved change.") from exc
        finally:
            if temp_path is not None:
                try:
                    temp_path.unlink(missing_ok=True)
                except OSError:
                    pass

        proposal.status = "applied"

        return {
            "proposal_id": proposal_id,
            "file_path": target.relative_to(workspace).as_posix(),
            "status": "applied",
        }


def reject_proposal(proposal_id: str) -> dict[str, str]:
    with _lock:
        proposal = _proposals.get(proposal_id)

        if proposal is None:
            raise ValueError("Proposal not found.")

        if proposal.status != "pending":
            raise ValueError("Proposal is no longer pending.")

        proposal.status = "rejected"

        return {
            "proposal_id": proposal_id,
            "status": "rejected",
        }
