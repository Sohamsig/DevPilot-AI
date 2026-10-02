from pathlib import Path

from langchain_core.tools import tool

from app.config import settings


IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
}

IGNORED_FILES = {
    ".env",
    ".env.local",
    ".env.development",
    ".env.production",
}


def resolve_workspace(workspace_path: str | None) -> Path:
    root = Path(settings.workspace_root).resolve()

    if workspace_path:
        workspace = Path(workspace_path).resolve()
    else:
        workspace = root

    try:
        workspace.relative_to(root)
    except ValueError:
        raise ValueError(
            "Workspace is outside the configured workspace root."
        )

    if not workspace.exists():
        raise ValueError("Workspace does not exist.")

    if not workspace.is_dir():
        raise ValueError("Workspace is not a directory.")

    return workspace


def is_ignored(path: Path, workspace: Path) -> bool:
    relative = path.relative_to(workspace)

    if any(part in IGNORED_DIRECTORIES for part in relative.parts):
        return True

    if path.name in IGNORED_FILES:
        return True

    return False


@tool
def list_files(workspace_path: str | None = None) -> str:
    """List source files while excluding secrets and generated directories."""

    workspace = resolve_workspace(workspace_path)

    files = []

    for path in workspace.rglob("*"):
        if not path.is_file():
            continue

        if is_ignored(path, workspace):
            continue

        files.append(path.relative_to(workspace).as_posix())

    return "\n".join(sorted(files))


@tool
def read_file(
    file_path: str,
    workspace_path: str | None = None,
) -> str:
    """Read a repository file safely."""

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

    return target.read_text(encoding="utf-8")


@tool
def search_code(
    query: str,
    workspace_path: str | None = None,
) -> str:
    """Search repository source files while excluding secrets and generated directories."""

    workspace = resolve_workspace(workspace_path)

    results = []

    for path in workspace.rglob("*"):
        if not path.is_file():
            continue

        if is_ignored(path, workspace):
            continue

        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        for line_number, line in enumerate(content.splitlines(), start=1):
            if query.lower() in line.lower():
                relative = path.relative_to(workspace).as_posix()
                results.append(
                    f"{relative}:{line_number}: {line}"
                )

    if not results:
        return "No matches found"

    return "\n".join(results)
