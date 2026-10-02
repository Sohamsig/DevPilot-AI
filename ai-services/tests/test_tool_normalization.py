from langchain_core.messages import AIMessage

from app.agent.graph import normalize_tool_call


def test_normalize_list_files_tool_call():
    message = AIMessage(
        content='{"name": "list_files", "arguments": {}}'
    )

    normalized = normalize_tool_call(message)

    assert normalized.content == ""

    assert len(normalized.tool_calls) == 1

    tool_call = normalized.tool_calls[0]

    assert tool_call["name"] == "list_files"
    assert tool_call["args"] == {}


def test_normalize_search_code_tool_call():
    message = AIMessage(
        content=(
            '{"name": "search_code", '
            '"arguments": {"query": "mongodb"}}'
        )
    )

    normalized = normalize_tool_call(message)

    assert len(normalized.tool_calls) == 1

    tool_call = normalized.tool_calls[0]

    assert tool_call["name"] == "search_code"
    assert tool_call["args"]["query"] == "mongodb"


def test_normalize_read_file_tool_call():
    message = AIMessage(
        content=(
            '{"name": "read_file", '
            '"arguments": {"file_path": "backend/main.go"}}'
        )
    )

    normalized = normalize_tool_call(message)

    assert len(normalized.tool_calls) == 1

    tool_call = normalized.tool_calls[0]

    assert tool_call["name"] == "read_file"
    assert tool_call["args"]["file_path"] == "backend/main.go"


def test_normalize_regular_message():
    message = AIMessage(
        content="The repository contains a Go backend."
    )

    normalized = normalize_tool_call(message)

    assert normalized.content == (
        "The repository contains a Go backend."
    )

    assert normalized.tool_calls == []