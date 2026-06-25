import { sanitizeHtml } from "@/utils/sanitizeHtml"
import { cn } from "@/lib/utils"

interface SafeHtmlProps {
  html: string
  className?: string
}

/**
 * Renders backend HTML (e.g. the `original_text` field) after passing it
 * through a strict whitelist sanitizer. Diacritic-friendly spacing and
 * matn/mark styling are applied via the `.arabic-content` class.
 */
export function SafeHtml({ html, className }: SafeHtmlProps) {
  const clean = sanitizeHtml(html)
  return (
    <p
      className={cn("arabic-content text-pretty", className)}
      // Content is sanitized above with a strict tag/attribute whitelist.
      dangerouslySetInnerHTML={{ __html: clean }}
    />
  )
}
