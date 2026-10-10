import difflib
from pathlib import Path

from langchain_core.tools import tool

from app.tools.change_approval import create_proposal
from app.tools.repository import is_ignored, resolve_workspace


def build_file_diff(
    file_path: str,
    proposed_content: str,
    workspace_path: str | None = None,
) -> str:
    """Preview a proposed change without modifying the repository."""

    workspace = resolve_workspace(workspace_path)
    target = (workspace / file_path).resolve()

    try:
        target.relative_to(workspace)
    except ValueError:
        raise ValueError(
            "File is outside the configured workspace."
        )

    if is_ignored(target, workspace):
        raise ValueError("Access to this file is not allowed.")

    if not target.exists():
        return f"File not found: {file_path}"

    if not target.is_file():
        return f"Not a file: {file_path}"

    try:
        original_content = target.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as exc:
        raise ValueError(
            "Unable to read the target file as UTF-8 text."
        ) from exc

    diff = difflib.unified_diff(
        original_content.splitlines(keepends=True),
        proposed_content.splitlines(keepends=True),
        fromfile=f"a/{target.relative_to(workspace).as_posix()}",
        tofile=f"b/{target.relative_to(workspace).as_posix()}",
    )

    result = "".join(diff)

    if not result:
        return "No changes proposed."

    return result


@tool
def preview_file_change(
    file_path: str,
    proposed_content: str,
    workspace_path: str | None = None,
) -> str:
    """Preview a proposed repository file change without writing to disk."""

    return build_file_diff(
        file_path=file_path,
        proposed_content=proposed_content,
        workspace_path=workspace_path,
    )



@tool
def propose_file_change(
    file_path: str,
    proposed_content: str,
    workspace_path: str | None = None,
) -> str:
    """Create a pending code-change proposal for human review. Does not modify the file."""
    proposal = create_proposal(
        file_path=file_path,
        proposed_content=proposed_content,
        workspace_path=workspace_path,
    )

    return (
        f"Proposal created: {proposal['proposal_id']}\n"
        f"File: {proposal['file_path']}\n"
        f"Status: {proposal['status']}\n\n"
        f"Review this diff before approval:\n{proposal['diff']}"
    )
