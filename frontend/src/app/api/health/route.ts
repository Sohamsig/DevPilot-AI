import { NextResponse } from "next/server";

export async function GET() {
  const baseUrl = (
    process.env.DEVPILOT_API_URL ?? "http://127.0.0.1:8000"
  ).replace(/\/+$/, "");

  try {
    const response = await fetch(`${baseUrl}/health`, {
      cache: "no-store",
      signal: AbortSignal.timeout(5000),
    });

    const body = await response.json().catch(() => ({
      detail: "The backend returned an invalid JSON response.",
    }));

    return NextResponse.json(body, { status: response.status });
  } catch {
    return NextResponse.json(
      {
        status: "unavailable",
        detail: "Cannot reach FastAPI at the configured local API URL.",
      },
      { status: 502 },
    );
  }
}

