from app.tools.repository import list_files, read_file, search_code

workspace = r"C:\Users\soham\Devpilot-ai"

print("=" * 80)
print("LIST FILES")
print("=" * 80)

result = list_files.invoke({
    "workspace_path": workspace
})

print(result[:3000])

print()
print("=" * 80)
print("READ CONFIG")
print("=" * 80)

result = read_file.invoke({
    "file_path": "backend/internal/config/config.go",
    "workspace_path": workspace,
})

print(result)

print()
print("=" * 80)
print("SEARCH MONGO")
print("=" * 80)

result = search_code.invoke({
    "query": "Mongo",
    "workspace_path": workspace,
})

print(result)
