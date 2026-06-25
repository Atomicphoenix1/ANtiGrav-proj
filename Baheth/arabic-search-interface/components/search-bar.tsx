"use client"

import { useState, useRef, useEffect } from "react"
import type { FormEvent } from "react"
import { Search, X, SlidersHorizontal, ChevronDown } from "lucide-react"
import { Button } from "@/components/ui/button"
import type { FilterOptions } from "@/lib/mock-data"

interface SearchBarProps {
  value: string
  onChange: (value: string) => void
  onSubmit: () => void
  loading?: boolean
  filters: FilterOptions
  selectedBook: string
  selectedSheikh: string
  selectedYear: string
  onBookChange: (v: string) => void
  onSheikhChange: (v: string) => void
  onYearChange: (v: string) => void
}

export function SearchBar({
  value,
  onChange,
  onSubmit,
  loading,
  filters,
  selectedBook,
  selectedSheikh,
  selectedYear,
  onBookChange,
  onSheikhChange,
  onYearChange,
}: SearchBarProps) {
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    onSubmit()
  }

  const hasActiveFilters = selectedBook || selectedSheikh || selectedYear

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="flex items-center gap-2">
        <div className="group relative flex flex-1 items-center">
          <Search
            className="pointer-events-none absolute start-4 size-5 text-muted-foreground transition-colors group-focus-within:text-primary"
            aria-hidden="true"
          />
          <input
            type="search"
            dir="rtl"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder="ابحث في النصوص والمتون..."
            aria-label="حقل البحث"
            className="h-14 w-full rounded-2xl border border-border bg-card ps-12 pe-12 text-lg text-card-foreground shadow-sm outline-none transition-all placeholder:text-muted-foreground focus:border-primary focus:ring-4 focus:ring-primary/15"
          />
          {value && (
            <button
              type="button"
              onClick={() => onChange("")}
              aria-label="مسح البحث"
              className="absolute end-4 flex size-6 items-center justify-center rounded-full text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            >
              <X className="size-4" aria-hidden="true" />
            </button>
          )}
        </div>

        <Button
          type="submit"
          size="lg"
          disabled={loading}
          className="h-14 rounded-2xl px-6 text-base font-bold shadow-sm"
        >
          {loading ? "...جارٍ البحث" : "بحث"}
        </Button>

        <div className="relative" ref={dropdownRef}>
          <Button
            type="button"
            variant="outline"
            size="lg"
            aria-label="خيارات البحث"
            className={`h-14 rounded-2xl bg-card px-4 sm:inline-flex ${hasActiveFilters ? "border-primary text-primary" : ""}`}
            onClick={() => setDropdownOpen((o) => !o)}
          >
            <SlidersHorizontal className="size-5" aria-hidden="true" />
          </Button>

          {dropdownOpen && (
            <div className="absolute left-0 top-full mt-2 w-72 rounded-2xl border border-border bg-card p-4 shadow-2xl z-50">
              <div className="flex items-center justify-between mb-3">
                <span className="text-sm font-bold text-foreground">تصفية النتائج</span>
                <button
                  type="button"
                  onClick={() => {
                    onBookChange("")
                    onSheikhChange("")
                    onYearChange("")
                  }}
                  className="text-xs text-muted-foreground hover:text-foreground"
                >
                  إعادة تعيين
                </button>
              </div>

              <div className="space-y-3">
                <div>
                  <label className="block text-xs text-muted-foreground mb-1">الكتاب</label>
                  <div className="relative">
                    <select
                      value={selectedBook}
                      onChange={(e) => onBookChange(e.target.value)}
                      className="w-full appearance-none rounded-xl border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
                    >
                      <option value="">الكل</option>
                      {filters.book_titles.map((t) => (
                        <option key={t} value={t}>{t}</option>
                      ))}
                    </select>
                    <ChevronDown className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground pointer-events-none" />
                  </div>
                </div>

                <div>
                  <label className="block text-xs text-muted-foreground mb-1">الشيخ</label>
                  <div className="relative">
                    <select
                      value={selectedSheikh}
                      onChange={(e) => onSheikhChange(e.target.value)}
                      className="w-full appearance-none rounded-xl border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
                    >
                      <option value="">الكل</option>
                      {filters.sheikh_names.map((s) => (
                        <option key={s} value={s}>{s}</option>
                      ))}
                    </select>
                    <ChevronDown className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground pointer-events-none" />
                  </div>
                </div>

                <div>
                  <label className="block text-xs text-muted-foreground mb-1">السنة</label>
                  <div className="relative">
                    <select
                      value={selectedYear}
                      onChange={(e) => onYearChange(e.target.value)}
                      className="w-full appearance-none rounded-xl border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
                    >
                      <option value="">الكل</option>
                      {filters.year_dates.map((y) => (
                        <option key={y} value={y}>{y}</option>
                      ))}
                    </select>
                    <ChevronDown className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground pointer-events-none" />
                  </div>
                </div>
              </div>

              <button
                type="button"
                onClick={() => setDropdownOpen(false)}
                className="w-full mt-4 rounded-xl bg-primary py-2 text-sm font-bold text-primary-foreground hover:bg-primary/90 transition-colors"
              >
                تطبيق
              </button>
            </div>
          )}
        </div>
      </div>
    </form>
  )
}
