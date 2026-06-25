import { BookOpen, FileText, Bookmark } from "lucide-react"
import type { SearchResult } from "@/lib/mock-data"
import { SafeHtml } from "@/components/safe-html"

interface ResultCardProps {
  result: SearchResult
  index: number
  active?: boolean
  onClick?: () => void
}

export function ResultCard({ result, index, active, onClick }: ResultCardProps) {
  const matchPercent = result.score !== undefined 
    ? Math.round(result.score * 100) 
    : Math.round(Math.abs(result.rank || 0) * 10) // FTS5 ranks are typically small float values

  return (
    <article 
      onClick={onClick}
      className={`group relative rounded-2xl border bg-card p-5 shadow-sm transition-all cursor-pointer sm:p-6 ${
        active 
          ? "border-primary ring-2 ring-primary/20" 
          : "border-border hover:border-primary/40 hover:shadow-md"
      }`}
    >
      {/* Header: source + relevance */}
      <header className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
            <BookOpen className="size-5" aria-hidden="true" />
          </span>
          <div className="flex flex-col">
            <h3 className="text-base font-bold leading-tight text-card-foreground">
              {result.source || `شظية نصية #${result.id}`}
            </h3>
            <span className="text-sm text-muted-foreground">{result.author || `معرف: ${result.id}`}</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {result.score !== undefined ? (
            <span className="rounded-full bg-accent/20 px-2.5 py-1 text-xs font-bold text-accent-foreground">
              مطابقة {matchPercent}٪
            </span>
          ) : (
            <span className="rounded-full bg-accent/20 px-2.5 py-1 text-xs font-bold text-accent-foreground">
              الترتيب: {result.rank !== undefined ? result.rank : "غير محدد"}
            </span>
          )}
          <span className="flex size-7 items-center justify-center rounded-full bg-muted text-xs font-bold text-muted-foreground">
            {index + 1}
          </span>
        </div>
      </header>

      {/* The matched text with sanitized HTML */}
      <SafeHtml
        html={result.original_text}
        className="text-lg leading-loose text-card-foreground sm:text-xl"
      />

      {/* Footer: location metadata (show only if available) */}
      {(result.book || result.chapter || result.page !== undefined) && (
        <footer className="mt-5 flex flex-wrap items-center gap-x-5 gap-y-2 border-t border-border pt-4 text-sm text-muted-foreground">
          {result.book && (
            <span className="inline-flex items-center gap-1.5">
              <Bookmark className="size-4" aria-hidden="true" />
              {result.book}
            </span>
          )}
          {result.chapter && (
            <span className="inline-flex items-center gap-1.5">
              <FileText className="size-4" aria-hidden="true" />
              {result.chapter}
            </span>
          )}
          {result.page !== undefined && (
            <span className="ms-auto font-medium tabular-nums">
              صفحة {result.page}
            </span>
          )}
        </footer>
      )}
    </article>
  )
}
