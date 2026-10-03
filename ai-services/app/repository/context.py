from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class RepositoryContext:
    """Structured context describing a repository."""

    root: str
    files: list[str] = field(default_factory=list)
    directories: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    file_count: int = 0
    directory_count: int = 0
    truncated: bool = False


IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".pytest-workspaces",
    "node_modules",
    "dist",
    "build",
    "vendor",
    "coverage",
}

IGNORED_FILES = {
    ".env",
}

IGNORED_FILE_PREFIXES = {
    ".env.",
}

LANGUAGE_BY_EXTENSION = {
    ".py": "Python",
    ".go": "Go",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".c": "C",
    ".h": "C",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".php": "PHP",
    ".cs": "C#",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
}


def _is_ignored_file(path: Path) -> bool:
    name = path.name

    if name in IGNORED_FILES:
        return True

    return any(name.startswith(prefix) for prefix in IGNORED_FILE_PREFIXES)


def _is_ignored_path(path: Path) -> bool:
    return any(part in IGNORED_DIRECTORIES for part in path.parts)


def build_repository_context(
    workspace_path: str | Path,
    *,
    max_files: int = 500,
    max_directories: int = 200,
) -> RepositoryContext:
    """Build a bounded structural representation of a repository."""

    workspace = Path(workspace_path).resolve()

    if not workspace.exists():
        raise ValueError(f"Workspace does not exist: {workspace}")

    if not workspace.is_dir():
        raise ValueError(f"Workspace is not a directory: {workspace}")

    if max_files < 0:
        raise ValueError("max_files must be non-negative")

    if max_directories < 0:
        raise ValueError("max_directories must be non-negative")

    files: list[str] = []
    directories: list[str] = []
    languages: set[str] = set()
    truncated = False

    for path in workspace.rglob("*"):
        try:
            relative = path.relative_to(workspace)
        except ValueError:
            continue

        if _is_ignored_path(relative):
            continue

        if path.is_dir():
            if len(directories) >= max_directories:
                truncated = True
                continue

            directories.append(relative.as_posix())
            continue

        if not path.is_file():
            continue

        if _is_ignored_file(path):
            continue

        if len(files) >= max_files:
            truncated = True
            continue

        relative_path = relative.as_posix()
        files.append(relative_path)

        language = LANGUAGE_BY_EXTENSION.get(path.suffix.lower())
        if language:
            languages.add(language)

    files.sort()
    directories.sort()

    return RepositoryContext(
        root=str(workspace),
        files=files,
        directories=directories,
        languages=sorted(languages),
        file_count=len(files),
        directory_count=len(directories),
        truncated=truncated,
    )