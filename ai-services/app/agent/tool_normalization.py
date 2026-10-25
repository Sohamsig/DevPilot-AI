import json
import re
import uuid

from langchain_core.messages import AIMessage


VALID_TOOL_NAMES = {
    "list_files",
    "list_top_level_folders",
    "read_file",
    "search_code",
    "preview_file_change",
    "propose_file_change",
}


def normalize_tool_call(
    response: AIMessage,
    workspace_path: str | None = None,
) -> AIMessage:
    """Normalize native and JSON-in-content tool calls."""

    if response.tool_calls:
        normalized_calls = []

        for call in response.tool_calls:
            name = call.get("name")
            args = dict(call.get("args") or {})

            if name in VALID_TOOL_NAMES and workspace_path:
                args["workspace_path"] = workspace_path

            normalized_calls.append({**call, "args": args})

        return AIMessage(
            content=response.content,
            tool_calls=normalized_calls,
        )

    content = response.content

    if not isinstance(content, str):
        return response

    content = content.strip()

    fenced = re.fullmatch(
        r"```(?:json)?\s*(.*?)\s*```",
        content,
        flags=re.DOTALL | re.IGNORECASE,
    )

    if fenced:
        content = fenced.group(1).strip()

    payload = None
    decoder = json.JSONDecoder()

    for index, character in enumerate(content):
        if character != "{":
            continue

        try:
            candidate, _ = decoder.raw_decode(content[index:])
        except json.JSONDecodeError:
            continue

        if (
            isinstance(candidate, dict)
            and candidate.get("name") in VALID_TOOL_NAMES
            and isinstance(candidate.get("arguments", {}), dict)
        ):
            payload = candidate
            break

    if payload is None:
        return response

    tool_name = payload["name"]
    arguments = dict(payload.get("arguments", {}))

    if workspace_path:
        arguments["workspace_path"] = workspace_path

    return AIMessage(
        content="",
        tool_calls=[
            {
                "name": tool_name,
                "args": arguments,
                "id": f"call_{uuid.uuid4().hex}",
                "type": "tool_call",
            }
        ],
    )
