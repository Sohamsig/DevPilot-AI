import { NextResponse } from "next/server";

const backendUrl =
  process.env.DEVPILOT_API_URL ?? "http://127.0.0.1:8000";

export async function POST(
  _request: Request,
  context: { params: Promise<{ proposalId: string }> },
) {
  try {
    const { proposalId } = await context.params;

    const response = await fetch(
      `${backendUrl}/v1/changes/${encodeURIComponent(proposalId)}/approve`,
      {
        method: "POST",
        cache: "no-store",
        signal: AbortSignal.timeout(15000),
      },
    );

    const data = await response.json().catch(() => ({
      detail: "The backend returned an invalid response.",
    }));

    return NextResponse.json(data, { status: response.status });
  } catch {
    return NextResponse.json(
      { detail: "Unable to reach the DevPilot backend." },
      { status: 502 },
    );
  }
}