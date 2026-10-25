import { NextResponse } from "next/server";

export async function POST(request: Request) {
  const baseUrl = (
    process.env.DEVPILOT_API_URL ?? "http://127.0.0.1:8000"
  ).replace(/\/+$/, "");

  let body: unknown;

  try {
    body = await request.json();
  } catch {
    return NextResponse.json(
      { detail: "Request body must be valid JSON." },
      { status: 400 },
    );
  }

  if (
    typeof body !== "object" ||
    body === null ||
    !("message" in body) ||
    typeof body.message !== "string" ||
    !body.message.trim()
  ) {
    return NextResponse.json(
      { detail: "Enter a task before submitting it." },
      { status: 400 },
    );
  }

  const payload = {
    message: body.message.trim(),
    workspace_path:
      "workspace_path" in body &&
      typeof body.workspace_path === "string" &&
      body.workspace_path.trim()
        ? body.workspace_path.trim()
        : null,
  };

  try {
    const response = await fetch(`${baseUrl}/v1/agent/runs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      cache: "no-store",
      signal: AbortSignal.timeout(120_000),
    });

    const responseBody = await response.json().catch(() => ({
      detail: "The backend returned an invalid JSON response.",
    }));

    return NextResponse.json(responseBody, {
      status: response.status,
    });
  } catch {
    return NextResponse.json(
      {
        detail:
          "Could not reach the AI backend, or the request timed out. Check that FastAPI and Ollama are running.",
      },
      { status: 502 },
    );
  }
}

