from app.tools.repository import list_files, read_file, search_code

workspace = r"C:\Users\soham\Devpilot-ai"

tests = [
    (
        "LIST",
        list_files.invoke({
            "workspace_path": workspace,
        }),
    ),
    (
        "MONGO",
        search_code.invoke({
            "query": "Mongo",
            "workspace_path": workspace,
        }),
    ),
    (
        "READ",
        read_file.invoke({
            "file_path": "backend/internal/config/config.go",
            "workspace_path": workspace,
        }),
    ),
    (
        "MISSING",
        read_file.invoke({
            "file_path": "backend/does-not-exist.go",
            "workspace_path": workspace,
        }),
    ),
]

for name, result in tests:
    print()
    print("=" * 100)
    print(name)
    print("=" * 100)
    print(result)
