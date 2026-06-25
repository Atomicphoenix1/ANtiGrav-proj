import { useState } from "react";
import { Play, Loader2, Terminal, X } from "lucide-react";
import { simulateExecution, type ExecutionResult } from "@/lib/codeRunner";
import type { CodePreviewConfig } from "@/data/portfolioData";

interface CodePreviewWindowProps {
  projectId: string;
  config: CodePreviewConfig;
  onClose: () => void;
}

type RunState = "idle" | "running" | "done" | "error";

export function CodePreviewWindow({ projectId, config, onClose }: CodePreviewWindowProps) {
  const [runState, setRunState] = useState<RunState>("idle");
  const [result, setResult] = useState<ExecutionResult | null>(null);

  async function handleRun() {
    if (runState === "running") return;
    setRunState("running");
    setResult(null);
    try {
      const res = await simulateExecution(projectId);
      setResult(res);
      setRunState(res.success ? "done" : "error");
    } catch {
      setRunState("error");
    }
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={`Code preview: ${projectId}`}
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
    >
      {/* Scrim */}
      <button
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
        aria-label="Close code preview"
        tabIndex={-1}
      />

      {/* Window */}
      <div className="relative z-10 flex w-full max-w-2xl flex-col overflow-hidden rounded-xl border border-border bg-card shadow-2xl">
        {/* Title bar */}
        <div className="flex items-center justify-between border-b border-border bg-secondary/50 px-4 py-3">
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded-full bg-red-500/80" aria-hidden="true" />
            <div className="h-3 w-3 rounded-full bg-yellow-500/80" aria-hidden="true" />
            <div className="h-3 w-3 rounded-full bg-green-500/80" aria-hidden="true" />
          </div>
          <span className="text-xs font-medium text-muted-foreground">
            {config.language} — display only
          </span>
          <button
            onClick={onClose}
            aria-label="Close"
            className="cursor-pointer rounded p-1 text-muted-foreground transition-colors hover:text-foreground"
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        </div>

        {/* Code pane */}
        <div className="overflow-x-auto bg-background/60 p-5">
          <pre className="font-mono text-xs leading-relaxed text-foreground/90 sm:text-sm">
            <code>{config.displayCode}</code>
          </pre>
        </div>

        {/* Output pane */}
        <div className="border-t border-border bg-background/80">
          <div className="flex items-center gap-2 border-b border-border/40 px-4 py-2">
            <Terminal className="h-3.5 w-3.5 text-accent" aria-hidden="true" />
            <span className="text-xs font-semibold text-muted-foreground">Output</span>
          </div>
          <div className="min-h-[100px] p-4">
            {runState === "idle" && (
              <p className="font-mono text-xs text-muted-foreground/60">
                Press ▶ Run to execute on the secure server…
              </p>
            )}
            {runState === "running" && (
              <div className="flex items-center gap-2 text-accent">
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                <span className="font-mono text-xs">Executing on server…</span>
              </div>
            )}
            {(runState === "done" || runState === "error") && result && (
              <pre
                className={[
                  "font-mono text-xs leading-relaxed whitespace-pre-wrap",
                  result.success ? "text-foreground/90" : "text-destructive",
                ].join(" ")}
              >
                {result.output}
                {"\n\n"}
                <span className="text-muted-foreground">
                  — completed in {(result.durationMs / 1000).toFixed(1)}s (simulated)
                </span>
              </pre>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-3 border-t border-border px-4 py-3">
          <button
            onClick={onClose}
            className="cursor-pointer rounded-lg px-4 py-2 text-sm text-muted-foreground transition-colors hover:text-foreground"
          >
            Close
          </button>
          <button
            onClick={handleRun}
            disabled={runState === "running"}
            className="flex cursor-pointer items-center gap-2 rounded-lg bg-accent px-5 py-2 text-sm font-semibold text-accent-foreground transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {runState === "running" ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                Running…
              </>
            ) : (
              <>
                <Play className="h-4 w-4" aria-hidden="true" />
                Run
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
