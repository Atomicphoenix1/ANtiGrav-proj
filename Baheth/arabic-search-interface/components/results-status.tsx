import { ListFilter } from "lucide-react"

interface ResultsStatusProps {
  count: number
  query: string
  durationMs: number
}

export function ResultsStatus({ count, query, durationMs }: ResultsStatusProps) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border pb-4">
      <p className="text-sm text-muted-foreground sm:text-base">
        عُثر على{" "}
        <span className="font-bold tabular-nums text-foreground">{count}</span>{" "}
        نتيجة
        {query && (
          <>
            {" "}
            لـ{" "}
            <span className="font-bold text-primary">«{query}»</span>
          </>
        )}{" "}
        <span className="text-muted-foreground/80">
          ({(durationMs / 1000).toFixed(2)} ثانية)
        </span>
      </p>

      <button
        type="button"
        className="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
      >
        <ListFilter className="size-4" aria-hidden="true" />
        الأكثر صلة
      </button>
    </div>
  )
}
