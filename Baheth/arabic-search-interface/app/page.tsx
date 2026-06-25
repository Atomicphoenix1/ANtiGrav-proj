"use client"

import { useState, useEffect, useRef, useCallback } from "react"
import { Sparkles, Library, ScrollText, TrendingUp } from "lucide-react"
import { SearchBar } from "@/components/search-bar"
import { ResultsStatus } from "@/components/results-status"
import { ResultCard } from "@/components/result-card"
import { SafeHtml } from "@/components/safe-html"
import type { SearchResult, FilterOptions } from "@/lib/mock-data"
import { useDebounce } from "@/hooks/useDebounce"

const BACKEND_URL = "http://127.0.0.1:8000"

export default function Home() {
  const [query, setQuery] = useState("")
  const [submitted, setSubmitted] = useState("")
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<SearchResult[]>([])
  const [activeResult, setActiveResult] = useState<SearchResult | null>(null)
  const [durationMs, setDurationMs] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [page, setPage] = useState(1)

  const [filters, setFilters] = useState<FilterOptions>({ book_titles: [], sheikh_names: [], year_dates: [] })
  const [selectedBook, setSelectedBook] = useState("")
  const [selectedSheikh, setSelectedSheikh] = useState("")
  const [selectedYear, setSelectedYear] = useState("")

  const [playModes, setPlayModes] = useState<Record<string | number, "audio" | "video">>({})

  const activeMode = activeResult ? (playModes[activeResult.id] || "audio") : "audio"

  const setModeForActive = (mode: "audio" | "video") => {
    if (activeResult) {
      setPlayModes((prev) => ({ ...prev, [activeResult.id]: mode }))
    }
  }

  const debouncedQuery = useDebounce(query, 300)
  const audioRef = useRef<HTMLAudioElement>(null)

  useEffect(() => {
    setPage(1)
  }, [debouncedQuery, selectedBook, selectedSheikh, selectedYear])

  useEffect(() => {
    fetch(`${BACKEND_URL}/api/filters`)
      .then((r) => r.json())
      .then((data: FilterOptions) => setFilters(data))
      .catch(() => {})
  }, [])

  const buildSearchUrl = useCallback(() => {
    const params = new URLSearchParams()
    params.set("q", debouncedQuery.trim())
    params.set("page", String(page))
    params.set("page_size", "10")
    if (selectedBook) params.set("book_title", selectedBook)
    if (selectedSheikh) params.set("sheikh_name", selectedSheikh)
    if (selectedYear) params.set("year_date", selectedYear)
    return `${BACKEND_URL}/search?${params.toString()}`
  }, [debouncedQuery, page, selectedBook, selectedSheikh, selectedYear])

  useEffect(() => {
    const runSearchPipeline = async () => {
      const trimmed = debouncedQuery.trim()
      if (!trimmed) {
        setResults([])
        setActiveResult(null)
        setSubmitted("")
        setError(null)
        return;
      }

      setLoading(true)
      setError(null)
      const start = performance.now()

      try {
        const url = buildSearchUrl()
        const response = await fetch(url)

        if (!response.ok) {
          throw new Error(`Server returned error code: ${response.status}`)
        }

        const data = await response.json()
        
        if (page === 1) {
          setResults(data.results)
          if (data.results.length > 0) {
            setActiveResult(data.results[0])
          } else {
            setActiveResult(null)
          }
        } else {
          setResults(prev => [...prev, ...data.results])
        }

        setSubmitted(trimmed)
        setDurationMs(Math.round(performance.now() - start))
      } catch (err: any) {
        console.error("Integration Fault:", err)
        setError("تعذر الاتصال بالخادم الرئيسي. يرجى التحقق من تشغيل الواجهة البرمجية (FastAPI).")
        setResults([])
        setActiveResult(null)
      } finally {
        setLoading(false)
      }
    }

    runSearchPipeline()
  }, [debouncedQuery, page, buildSearchUrl])

  useEffect(() => {
    if (activeResult && activeResult.audio_url && audioRef.current) {
      if (activeMode === "audio") {
        audioRef.current.src = `${BACKEND_URL}${activeResult.audio_url}`
        audioRef.current.load()
        audioRef.current.currentTime = activeResult.start_time || 0
        audioRef.current.play().catch(err => {
          console.log("Audio autoplay interrupted:", err)
        })
      } else {
        audioRef.current.pause()
      }
    }
  }, [activeResult, activeMode])

  const handleInstantSearch = () => {}

  return (
    <div className="min-h-screen bg-background" dir="rtl">
      <header className="sticky top-0 z-20 border-b border-border bg-background/85 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-4 sm:px-6">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-2.5">
              <span className="flex size-10 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-sm">
                <ScrollText className="size-5" aria-hidden="true" />
              </span>
              <div className="flex flex-col leading-none">
                <span className="font-serif text-2xl font-bold text-foreground">
                  باحِث
                </span>
                <span className="text-xs text-muted-foreground">
                  محرك البحث في النصوص العربية
                </span>
              </div>
            </div>
            <span className="hidden items-center gap-1.5 rounded-full border border-border bg-card px-3 py-1.5 text-xs font-medium text-muted-foreground sm:inline-flex">
              <Sparkles className="size-3.5 text-accent" aria-hidden="true" />
              بحث دلالي ذكي
            </span>
          </div>

          <SearchBar
            value={query}
            onChange={setQuery}
            onSubmit={handleInstantSearch}
            loading={loading}
            filters={filters}
            selectedBook={selectedBook}
            selectedSheikh={selectedSheikh}
            selectedYear={selectedYear}
            onBookChange={setSelectedBook}
            onSheikhChange={setSelectedSheikh}
            onYearChange={setSelectedYear}
          />
        </div>
      </header>

      <main className="mx-auto grid max-w-7xl grid-cols-1 gap-6 px-4 py-6 sm:px-6 lg:grid-cols-[1.5fr_1fr]">
        <section 
          className="rounded-2xl border border-border bg-card p-6 shadow-sm min-h-[500px] flex flex-col" 
          aria-label="لوحة القراءة"
        >
          {activeResult ? (
            <div className="flex flex-col h-full">
              <div className="flex items-center justify-between border-b border-border pb-4 mb-6">
                <div>
                  <h2 className="text-xl font-bold text-foreground font-serif">
                    {activeResult.source || `شظية نصية #${activeResult.id}`}
                  </h2>
                  <p className="text-sm text-muted-foreground mt-1">
                    {activeResult.author || "مصدر تراثي"}
                  </p>
                </div>
                {activeResult.rank !== undefined && (
                  <span className="rounded-full bg-primary/10 px-3 py-1 text-xs font-bold text-primary">
                    درجة المطابقة: {activeResult.rank}
                  </span>
                )}
              </div>
              <div className="flex-1 overflow-y-auto max-w-prose">
                <SafeHtml
                  html={activeResult.original_text}
                  className="text-xl md:text-2xl leading-loose text-card-foreground font-serif arabic-content"
                />
              </div>
              {activeResult.youtube_url && (
                <div className="flex gap-2 mt-4 pb-2 border-b border-border">
                  <button
                    onClick={() => setModeForActive("audio")}
                    className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                      activeMode === "audio"
                        ? "bg-primary text-primary-foreground shadow-sm"
                        : "bg-secondary text-secondary-foreground hover:bg-muted"
                    }`}
                  >
                    🎵 Audio Mode (Default)
                  </button>
                  <button
                    onClick={() => setModeForActive("video")}
                    className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                      activeMode === "video"
                        ? "bg-primary text-primary-foreground shadow-sm"
                        : "bg-secondary text-secondary-foreground hover:bg-muted"
                    }`}
                  >
                    📺 Video Mode (Baheth Style)
                  </button>
                </div>
              )}

              {activeMode === "video" && activeResult.youtube_embed_url ? (
                <div className="mt-6 pt-4 border-t border-border flex flex-col gap-2">
                  <span className="text-sm font-semibold text-muted-foreground">الفيديو المصاحب (يوتيوب):</span>
                  <iframe
                    width="100%"
                    height="250"
                    src={activeResult.youtube_embed_url}
                    title="YouTube Video Player"
                    frameBorder="0"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                    className="rounded-lg border border-cyan-500/30 mt-2"
                  />
                </div>
              ) : (
                activeResult.audio_url && (
                  <div className="mt-6 pt-4 border-t border-border flex flex-col gap-2">
                    <span className="text-sm font-semibold text-muted-foreground">التلاوة / الصوت المصاحب:</span>
                    <audio ref={audioRef} controls className="w-full" />
                  </div>
                )
              )}
              {(activeResult.book || activeResult.chapter || activeResult.page !== undefined || activeResult.book_title || activeResult.sheikh_name) && (
                <div className="mt-8 pt-4 border-t border-border flex flex-wrap gap-4 text-sm text-muted-foreground">
                  {activeResult.book_title && <span>الكتاب: {activeResult.book_title}</span>}
                  {activeResult.sheikh_name && <span>الشيخ: {activeResult.sheikh_name}</span>}
                  {activeResult.year_date && <span>السنة: {activeResult.year_date}</span>}
                  {activeResult.book && <span>المصدر: {activeResult.book}</span>}
                  {activeResult.chapter && <span>الباب: {activeResult.chapter}</span>}
                  {activeResult.page !== undefined && <span>صفحة: {activeResult.page}</span>}
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center flex-1 text-muted-foreground py-20">
              <Library className="size-12 mb-4 text-muted-foreground/50" />
              <p className="text-lg font-serif">الرجاء اختيار نتيجة بحث لعرض النص الكامل هنا.</p>
            </div>
          )}
        </section>

        <section className="flex flex-col gap-5" aria-label="نتائج البحث">
          {error ? (
            <div className="rounded-2xl border border-destructive/20 bg-destructive/10 p-5 text-destructive text-sm leading-relaxed">
              {error}
            </div>
          ) : (
            <>
              {submitted && (
                <ResultsStatus
                  count={results.length}
                  query={submitted}
                  durationMs={durationMs}
                />
              )}

              {loading && page === 1 ? (
                <div className="flex flex-col gap-4">
                  {[0, 1, 2].map((i) => (
                    <div
                      key={i}
                      className="h-32 animate-pulse rounded-2xl border border-border bg-card"
                    />
                  ))}
                </div>
              ) : (
                <div className="flex flex-col gap-4">
                  {results.length > 0 ? (
                    <>
                      {results.map((result, i) => (
                        <ResultCard 
                          key={result.id} 
                          result={result} 
                          index={i} 
                          active={activeResult?.id === result.id}
                          onClick={() => setActiveResult(result)}
                        />
                      ))}
                      <button
                        type="button"
                        onClick={() => setPage(prev => prev + 1)}
                        className="w-full mt-2 py-3 px-4 rounded-xl border border-border bg-card hover:bg-muted text-sm font-bold transition-colors"
                      >
                        {loading ? "جاري التحميل..." : "تحميل المزيد"}
                      </button>
                    </>
                  ) : (
                    submitted && (
                      <div className="text-center py-12 text-muted-foreground rounded-2xl border border-dashed border-border bg-muted/20">
                        لا توجد نتائج مطابقة لبحثك.
                      </div>
                    )
                  )}
                </div>
              )}
            </>
          )}

          {!submitted && !loading && (
            <div className="rounded-2xl border border-border bg-card p-5 shadow-sm">
              <h2 className="mb-4 flex items-center gap-2 text-sm font-bold text-card-foreground">
                <TrendingUp className="size-4 text-primary" aria-hidden="true" />
                عمليات بحث شائعة
              </h2>
              <div className="flex flex-wrap gap-2">
                {["طلب العلم", "الإخلاص", "الصبر", "حسن الخلق", "التوكل"].map(
                  (term) => (
                    <button
                      key={term}
                      type="button"
                      onClick={() => setQuery(term)}
                      className="rounded-full border border-border bg-secondary px-3 py-1.5 text-xs font-medium text-secondary-foreground transition-colors hover:border-primary/40 hover:bg-primary/10 hover:text-primary"
                    >
                      {term}
                    </button>
                  ),
                )}
              </div>
            </div>
          )}
        </section>
      </main>
    </div>
  )
}
