
"use client";

import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";

type Health = {
  status?: string;
  service?: string;
  version?: string;
  detail?: string;
};

type ChangeProposal = {
  proposal_id: string;
  file_path: string;
  diff: string;
  status: string;
};

type AgentResult = {
  answer?: string;
  detail?: string;
  proposal?: ChangeProposal | null;
};

type ChangeDecisionResult = {
  proposal_id?: string;
  status?: string;
  detail?: string;
};

export default function Home() {
  const [workspacePath, setWorkspacePath] = useState(
    "C:\\Users\\soham\\Devpilot-ai",
  );
  const [task, setTask] = useState("");
  const [health, setHealth] = useState<Health | null>(null);
  const [checkingHealth, setCheckingHealth] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [answer, setAnswer] = useState("");
  const [error, setError] = useState("");
  const [lastTask, setLastTask] = useState("");
  const [proposal, setProposal] = useState<ChangeProposal | null>(null);
  const [proposalAction, setProposalAction] = useState<"approve" | "reject" | null>(null);
  const [proposalMessage, setProposalMessage] = useState("");

  const checkHealth = useCallback(async () => {
    setCheckingHealth(true);

    try {
      const response = await fetch("/api/health", { cache: "no-store" });
      const data = (await response.json()) as Health;
      setHealth(response.ok ? data : null);
    } catch {
      setHealth(null);
    } finally {
      setCheckingHealth(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function loadInitialHealth() {
      try {
        const response = await fetch("/api/health", { cache: "no-store" });
        const data = (await response.json()) as Health;
        if (!cancelled) setHealth(response.ok ? data : null);
      } catch {
        if (!cancelled) setHealth(null);
      } finally {
        if (!cancelled) setCheckingHealth(false);
      }
    }

    void loadInitialHealth();

    return () => {
      cancelled = true;
    };
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const message = task.trim();
    if (!message || submitting) return;

    setSubmitting(true);
    setError("");
    setAnswer("");
    setProposal(null);
    setProposalAction(null);
    setProposalMessage("");
    setLastTask(message);

    try {
      const response = await fetch("/api/agent/runs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message,
          workspace_path: workspacePath.trim() || null,
        }),
      });

      const data = (await response.json()) as AgentResult;

      if (!response.ok) {
        throw new Error(
          data.detail || `Agent request failed (${response.status}).`,
        );
      }

      if (typeof data.answer !== "string") {
        throw new Error("The backend response did not contain an answer.");
      }

      setAnswer(data.answer);
      setProposal(data.proposal ?? null);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Something went wrong while contacting the agent.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  async function handleProposalDecision(
    decision: "approve" | "reject",
  ) {
    if (!proposal || proposalAction) return;

    setProposalAction(decision);
    setProposalMessage("");

    try {
      const response = await fetch(
        `/api/changes/${encodeURIComponent(proposal.proposal_id)}/${decision}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({}),
        },
      );

      const data = (await response.json().catch(() => ({}))) as ChangeDecisionResult;

      if (!response.ok) {
        throw new Error(
          data.detail || `Could not ${decision} proposal (${response.status}).`,
        );
      }

      const nextStatus =
        data.status ?? (decision === "approve" ? "approved" : "rejected");

      setProposal((current) =>
        current ? { ...current, status: nextStatus } : current,
      );

      setProposalMessage(
        decision === "approve"
          ? "Approval request succeeded. Verify the file contents in your workspace."
          : "Proposal rejected.",
      );
    } catch (err) {
      setProposalMessage(
        err instanceof Error
          ? err.message
          : "Could not update the proposal.",
      );
    } finally {
      setProposalAction(null);
    }
  }
  const backendOnline = health?.status === "ok";

  return (
    <main className="min-h-screen bg-[#090b10] text-[#e8eaf0]">
      <div className="flex min-h-screen">
        <aside className="hidden w-[246px] shrink-0 flex-col border-r border-white/[0.07] bg-[#0d1017] px-4 py-5 md:flex">
          <div className="mb-10 flex items-center gap-3 px-2">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-500 text-lg font-bold text-white shadow-lg shadow-blue-500/20">
              D
            </span>
            <span>
              <span className="block text-[15px] font-semibold tracking-tight">
                DevPilot AI
              </span>
              <span className="mt-0.5 block text-[11px] text-slate-500">
                Engineering workspace
              </span>
            </span>
          </div>

          <p className="mb-3 px-3 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-500">
            Workspace
          </p>

          <div className="flex items-center gap-3 rounded-xl border border-blue-400/15 bg-blue-500/[0.09] px-3 py-3 text-sm text-blue-100">
            <span className="text-base">âŒ˜</span>
            <span className="font-medium">Agent workspace</span>
            <span className="ml-auto h-1.5 w-1.5 rounded-full bg-blue-400" />
          </div>

          <div className="mt-auto rounded-xl border border-white/[0.07] bg-white/[0.025] p-3.5">
            <div className="flex items-center gap-2 text-xs font-medium text-slate-300">
              <span
                className={`h-2 w-2 rounded-full ${
                  checkingHealth
                    ? "bg-amber-400"
                    : backendOnline
                      ? "bg-emerald-400"
                      : "bg-rose-400"
                }`}
              />
              Local AI backend
            </div>
            <p className="mt-2 text-[11px] leading-5 text-slate-500">
              {checkingHealth
                ? "Checking connectionâ€¦"
                : backendOnline
                  ? `${health?.service ?? "FastAPI"} Â· v${health?.version ?? "unknown"}`
                  : "Backend unavailable"}
            </p>
            <button
              type="button"
              onClick={() => void checkHealth()}
              className="mt-3 text-xs text-slate-400 transition hover:text-white"
            >
              â†» Check connection
            </button>
          </div>
        </aside>

        <section className="flex min-w-0 flex-1 flex-col">
          <header className="flex min-h-[68px] items-center justify-between gap-3 border-b border-white/[0.07] px-5 sm:px-8">
            <div>
              <p className="text-sm font-medium text-slate-100">
                Agent workspace
              </p>
              <p className="mt-1 text-xs text-slate-500">
                Plan, inspect, and improve your codebase
              </p>
            </div>

            <div
              className={`flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs ${
                checkingHealth
                  ? "border-amber-400/20 bg-amber-400/[0.06] text-amber-200"
                  : backendOnline
                    ? "border-emerald-400/20 bg-emerald-400/[0.06] text-emerald-300"
                    : "border-rose-400/20 bg-rose-400/[0.06] text-rose-300"
              }`}
            >
              <span
                className={`h-1.5 w-1.5 rounded-full ${
                  checkingHealth
                    ? "bg-amber-400"
                    : backendOnline
                      ? "bg-emerald-400"
                      : "bg-rose-400"
                }`}
              />
              {checkingHealth
                ? "Connecting"
                : backendOnline
                  ? "Backend connected"
                  : "Backend offline"}
            </div>
          </header>

          <div className="mx-auto flex w-full max-w-5xl flex-1 flex-col px-5 py-8 sm:px-8 sm:py-12">
            <div className="mb-9">
              <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-blue-400/15 bg-blue-400/[0.06] px-3 py-1.5 text-xs text-blue-200">
                <span>âœ³</span>
                Your local AI engineering agent
              </div>

              <h1 className="max-w-3xl text-3xl font-semibold tracking-[-0.04em] text-white sm:text-4xl">
                Ship better code.
                <span className="block text-slate-400">
                  Let&apos;s work on your next idea.
                </span>
              </h1>

              <p className="mt-4 max-w-2xl text-sm leading-6 text-slate-400">
                Give DevPilot an engineering task. It will send your request to
                the configured agent and show the response returned by your
                local backend.
              </p>
            </div>

            <form
              onSubmit={handleSubmit}
              className="overflow-hidden rounded-2xl border border-white/[0.10] bg-[#10141d] shadow-2xl shadow-black/20"
            >
              <div className="border-b border-white/[0.07] px-4 py-4 sm:px-5">
                <label
                  htmlFor="workspace"
                  className="mb-2 block text-xs font-medium text-slate-300"
                >
                  Repository workspace
                </label>
                <div className="flex items-center gap-3 rounded-lg border border-white/[0.08] bg-[#0b0e15] px-3">
                  <span className="text-slate-500">âŒ</span>
                  <input
                    id="workspace"
                    value={workspacePath}
                    onChange={(event) => setWorkspacePath(event.target.value)}
                    spellCheck={false}
                    className="min-w-0 flex-1 bg-transparent py-3 text-sm text-slate-200 outline-none placeholder:text-slate-600"
                    placeholder="C:\path\to\your\project"
                    aria-label="Repository workspace path"
                  />
                  <span className="hidden text-[10px] text-slate-500 sm:inline">
                    LOCAL PATH
                  </span>
                </div>
                <p className="mt-2 text-[11px] leading-5 text-slate-500">
                  This path is sent to your local FastAPI service. Make sure
                  the backend process has permission to access it.
                </p>
              </div>

              <div className="p-4 sm:p-5">
                <label
                  htmlFor="task"
                  className="mb-3 block text-xs font-medium text-slate-300"
                >
                  What should we work on?
                </label>
                <textarea
                  id="task"
                  value={task}
                  onChange={(event) => setTask(event.target.value)}
                  rows={5}
                  maxLength={10000}
                  disabled={submitting}
                  placeholder="e.g. Find where MongoDB connections are configured and explain how the current setup works. Don't change any files yet."
                  className="w-full resize-y bg-transparent text-sm leading-7 text-slate-100 outline-none placeholder:text-slate-600 disabled:opacity-60"
                />

                <div className="mt-4 flex flex-col gap-3 border-t border-white/[0.07] pt-4 sm:flex-row sm:items-center sm:justify-between">
                  <span className="text-[11px] text-slate-500">
                    {task.length}/10,000 characters
                  </span>
                  <button
                    type="submit"
                    disabled={submitting || !task.trim()}
                    className="inline-flex items-center justify-center gap-2 rounded-lg bg-blue-500 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-400 disabled:cursor-not-allowed disabled:opacity-45"
                  >
                    {submitting ? (
                      <>
                        <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                        Workingâ€¦
                      </>
                    ) : (
                      <>
                        Run agent <span aria-hidden="true">â†—</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            </form>

            {!backendOnline && !checkingHealth && (
              <div className="mt-4 rounded-xl border border-amber-400/20 bg-amber-400/[0.05] p-4 text-sm">
                <p className="font-medium text-amber-200">
                  Your backend is not responding
                </p>
                <p className="mt-1 leading-6 text-slate-400">
                  Start FastAPI on port 8000 and ensure your local Ollama
                  service and configured model are available. Then check the
                  connection again.
                </p>
              </div>
            )}

            {error && (
              <div
                role="alert"
                className="mt-5 rounded-xl border border-rose-400/20 bg-rose-400/[0.06] p-4"
              >
                <p className="text-sm font-medium text-rose-300">
                  Agent request failed
                </p>
                <p className="mt-2 whitespace-pre-wrap break-words text-sm leading-6 text-slate-300">
                  {error}
                </p>
              </div>
            )}

            {(submitting || answer) && (
              <section
                aria-live="polite"
                className="mt-7 overflow-hidden rounded-2xl border border-white/[0.09] bg-[#10141d]"
              >
                <div className="flex items-center gap-3 border-b border-white/[0.07] px-5 py-4">
                  <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500/10 text-blue-300">
                    âœ³
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-slate-100">
                      Agent response
                    </p>
                    <p className="mt-1 truncate text-xs text-slate-500">
                      {lastTask}
                    </p>
                  </div>
                  {submitting && (
                    <span className="text-xs text-blue-300">Processing</span>
                  )}
                </div>
                <div className="p-5">
                  {submitting ? (
                    <div className="space-y-3 py-2">
                      <div className="h-3 w-4/5 animate-pulse rounded bg-white/[0.07]" />
                      <div className="h-3 w-full animate-pulse rounded bg-white/[0.05]" />
                      <div className="h-3 w-3/5 animate-pulse rounded bg-white/[0.05]" />
                      <p className="pt-2 text-xs text-slate-500">
                        Waiting for the backend agent. Complex tasks can take
                        some time.
                      </p>
                    </div>
                  ) : (
                    <div className="whitespace-pre-wrap break-words text-sm leading-7 text-slate-300">
                      {answer}
                    </div>
                  )}
                </div>
              </section>
            )}

            {proposal && (
              <section className="mt-5 overflow-hidden rounded-2xl border border-amber-400/20 bg-[#10141d]">
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/[0.07] px-5 py-4">
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-slate-100">
                      Proposed file change
                    </p>
                    <p className="mt-1 break-all text-xs text-slate-400">
                      {proposal.file_path}
                    </p>
                  </div>
                  <span className="rounded-full border border-amber-400/20 bg-amber-400/[0.06] px-3 py-1 text-xs text-amber-200">
                    {proposal.status}
                  </span>
                </div>

                <div className="p-5">
                  <p className="mb-3 text-xs leading-5 text-slate-400">
                    Review the diff before deciding. Approval may write changes directly to your workspace.
                  </p>

                  <pre className="max-h-[420px] overflow-auto whitespace-pre-wrap break-words rounded-xl border border-white/[0.08] bg-[#090b10] p-4 font-mono text-xs leading-6 text-slate-300">
                    {proposal.diff || "No diff was returned."}
                  </pre>

                  {proposal.status.toLowerCase() === "pending" && (
                    <div className="mt-4 flex flex-wrap justify-end gap-3">
                      <button
                        type="button"
                        disabled={proposalAction !== null}
                        onClick={() => void handleProposalDecision("reject")}
                        className="rounded-lg border border-white/10 px-4 py-2 text-sm text-slate-300 transition hover:bg-white/5 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        {proposalAction === "reject" ? "Rejecting..." : "Reject"}
                      </button>

                      <button
                        type="button"
                        disabled={proposalAction !== null}
                        onClick={() => void handleProposalDecision("approve")}
                        className="rounded-lg bg-emerald-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        {proposalAction === "approve" ? "Approving..." : "Approve change"}
                      </button>
                    </div>
                  )}

                  {proposalMessage && (
                    <p role="status" className="mt-4 whitespace-pre-wrap break-words text-sm leading-6 text-slate-300">
                      {proposalMessage}
                    </p>
                  )}
                </div>
              </section>
            )}
            {!submitting && !answer && !error && (
              <div className="mt-7 rounded-xl border border-dashed border-white/[0.10] px-5 py-6">
                <p className="text-sm font-medium text-slate-300">
                  Ready when you are
                </p>
                <p className="mt-2 text-sm leading-6 text-slate-500">
                  Start with a question about your codebase. For the first
                  test, ask the agent to explain something rather than modify
                  files.
                </p>
              </div>
            )}

            <footer className="mt-auto pt-12 text-center text-[11px] text-slate-600">
              DevPilot AI Â· Local development workspace
            </footer>
          </div>
        </section>
      </div>
    </main>
  );
}

