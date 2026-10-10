import json
import re
import uuid

from langchain_core.messages import AIMessage


VALID_TOOL_NAMES = {
    "list_files",
    "read_file",
    "search_code",
    "preview_file_change",
    "propose_file_change",
}


def normalize_tool_call(
    response: AIMessage,
    workspace_path: str | None = None,
) -> AIMessage:
    """
    Normalize native or JSON-in-content tool calls.

    The workspace path is controlled by graph state.
    """

    if response.tool_calls:
        normalized_calls = []

        for call in response.tool_calls:
            name = call.get("name")
            args = dict(call.get("args") or {})

            if (
                name in VALID_TOOL_NAMES
                and workspace_path
                and not args.get("workspace_path")
            ):
                args["workspace_path"] = workspace_path

            normalized_calls.append(
                {
                    **call,
                    "args": args,
                }
            )

        return AIMessage(
            content=response.content,
            tool_calls=normalized_calls,
        )

    content = response.content

    if not isinstance(content, str):
        return response

    content = content.strip()

    # Ollama may put the tool-call JSON inside a fenced block
    # after explanatory text.
    candidates = [content]
    candidates.extend(
        re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
    )

    payload = None
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue

        if isinstance(parsed, dict) and "name" in parsed:
            payload = parsed
            break

    if payload is None:
        return response

    if not isinstance(payload, dict):
        return response

    tool_name = payload.get("name")
    arguments = payload.get("arguments", {})

    if tool_name not in VALID_TOOL_NAMES:
        return response

    if not isinstance(arguments, dict):
        return response

    arguments = dict(arguments)

    if workspace_path and not arguments.get("workspace_path"):
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
