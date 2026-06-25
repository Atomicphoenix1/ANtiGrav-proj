# Integration Guide: Arabic Search Engine Bridge (Phase 1.3)

This integration guide outlines the architecture and security controls required to safely bridge the FastAPI backend (with SQLite FTS5) and the Next.js React frontend.

---

## 1. Backend: FastAPI CORS Middleware Configuration

To allow the Next.js frontend (typically running on `http://localhost:3000` or `http://localhost:5173` depending on the environment) to call the local FastAPI backend (defaulting to `http://127.0.0.1:8000` or `http://localhost:8000`), we must configure CORS middleware in `main.py`.

### Code Implementation (`main.py`)

Add the following middleware configuration directly after creating the `FastAPI` instance:

```python
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from database import init_db, get_connection
from normalizer import normalize
from models import IndexShardsRequest, IndexShardsResponse, SearchResult, SearchResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="Fusha Arabic Search Engine", version="1.0.0", lifespan=lifespan)

# Define allowed origins (development local addresses)
origins = [
    "http://localhost:3000",      # Next.js dev server
    "http://127.0.0.1:3000",
    "http://localhost:5173",      # Vite dev server
    "http://127.0.0.1:5173",
]

# Register CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)
```

---

## 2. Frontend: Debounced API Fetching in React

To optimize performance and avoid spamming the backend FTS5 engine on every keystroke, we implement a custom hook `useDebounce` and handle search state transitions natively.

### 2.1 Debounce Hook (`useDebounce.ts`)

```typescript
import { useState, useEffect } from "react";

export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}
```

### 2.2 Search Component Fetch Logic (`SearchContainer.tsx`)

This component coordinates input queries, invokes the debounced search fetch, and processes state updates:

```tsx
import React, { useState, useEffect } from "react";
import { useDebounce } from "./useDebounce";

interface SearchResult {
  id: number;
  original_text: string;
  normalized_text: string;
  rank: number;
}

interface SearchResponse {
  query: string;
  normalized_query: string;
  results: SearchResult[];
}

export default function SearchContainer() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [activeResult, setActiveResult] = useState<SearchResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const debouncedQuery = useDebounce(query, 300); // 300ms delay

  useEffect(() => {
    const fetchResults = async () => {
      if (!debouncedQuery.trim()) {
        setResults([]);
        setError(null);
        return;
      }

      setLoading(true);
      setError(null);

      try {
        const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
        const response = await fetch(
          `${backendUrl}/search?q=${encodeURIComponent(debouncedQuery)}`
        );

        if (!response.ok) {
          throw new Error(`Server returned status: ${response.status}`);
        }

        const data: SearchResponse = await response.json();
        setResults(data.results);
      } catch (err: any) {
        console.error("Search Fetch Error:", err);
        setError(err.message || "Failed to communicate with server.");
        setResults([]);
      } finally {
        setLoading(false);
      }
    };

    fetchResults();
  }, [debouncedQuery]);

  return (
    <div className="flex flex-col h-screen" dir="rtl">
      {/* Search Header */}
      <div className="p-4 border-b">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="البحث في النصوص العربية..."
          className="w-full p-2 border rounded-md"
        />
        {loading && <p className="text-sm text-gray-500 mt-1">جاري البحث...</p>}
      </div>

      {/* Main Split View */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Reading Viewport */}
        <div className="w-2/3 p-6 overflow-y-auto border-l">
          <ReadingViewport activeResult={activeResult} />
        </div>

        {/* Right Results Pane */}
        <div className="w-1/3 p-4 overflow-y-auto bg-gray-50">
          {error && (
            <div className="p-3 bg-red-100 text-red-700 rounded-md mb-4">
              خطأ: {error === "Failed to fetch" ? "لا يمكن الاتصال بالخادم الرئيسي." : error}
            </div>
          )}
          
          {!loading && !error && results.length === 0 && query.trim() !== "" && (
            <div className="text-gray-500 text-center py-8">
              لا توجد نتائج مطابقة لبحثك.
            </div>
          )}

          <div className="space-y-2">
            {results.map((result) => (
              <div
                key={result.id}
                onClick={() => setActiveResult(result)}
                className={`p-3 border rounded-md cursor-pointer transition-colors ${
                  activeResult?.id === result.id ? "bg-blue-50 border-blue-300" : "bg-white hover:bg-gray-100"
                }`}
              >
                <div className="text-sm font-semibold text-gray-400">معرف الشظية: #{result.id}</div>
                <div 
                  className="text-gray-700 line-clamp-2 mt-1 font-serif"
                  dangerouslySetInnerHTML={{ __html: sanitizeHtml(result.original_text) }}
                />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
```

---

## 3. Secure HTML Injection (dangerouslySetInnerHTML)

Because the `original_text` field in our SQLite database can include structural and presentation markup (such as `<p>` and `<matn>`), it must be rendered as raw HTML. To prevent Cross-Site Scripting (XSS) vulnerabilities, the frontend must sanitize the HTML before passing it to `dangerouslySetInnerHTML`.

### 3.1 Sanitization Strategy
We use `dompurify` (or its lightweight isomorphic equivalent `isomorphic-dompurify`) to strip out harmful elements (such as `<script>`, `onload` handlers, etc.) while explicitly preserving structural tags like `<p>`, `<matn>`, `<strong>`, and `<span>`.

1. Install DOMPurify:
   ```bash
   npm install dompurify isomorphic-dompurify
   npm install --save-dev @types/dompurify
   ```

2. Implement the Sanitizer utility:
```typescript
import DOMPurify from "isomorphic-dompurify";

export function sanitizeHtml(rawHtml: string): string {
  return DOMPurify.sanitize(rawHtml, {
    ALLOWED_TAGS: ["p", "span", "strong", "em", "matn", "br", "div", "b", "i"],
    ALLOWED_ATTR: ["class", "id", "dir"],
  });
}
```

### 3.2 Reading Viewport Component (`ReadingViewport.tsx`)

This component displays the sanitized original text in the left pane:

```tsx
import React from "react";
import { sanitizeHtml } from "./sanitizeHtml";

interface ReadingViewportProps {
  activeResult: {
    id: number;
    original_text: string;
    normalized_text: string;
    rank: number;
  } | null;
}

export function ReadingViewport({ activeResult }: ReadingViewportProps) {
  if (!activeResult) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400 font-serif">
        الرجاء اختيار نتيجة بحث لعرض النص الكامل هنا.
      </div>
    );
  }

  // Sanitize markup for safe rendering
  const safeMarkup = sanitizeHtml(activeResult.original_text);

  return (
    <div className="max-w-prose mx-auto">
      <div className="flex items-center justify-between border-b pb-4 mb-6">
        <h1 className="text-xl font-bold text-gray-800">تفاصيل الشظية #{activeResult.id}</h1>
        <span className="text-xs bg-gray-200 text-gray-700 px-2 py-1 rounded">
          مستوى التطابق: {activeResult.rank}
        </span>
      </div>

      {/* Render the sanitized HTML natively */}
      <article 
        className="prose prose-lg dark:prose-invert font-serif text-right leading-relaxed text-gray-900"
        dangerouslySetInnerHTML={{ __html: safeMarkup }}
      />
    </div>
  );
}
```

---

## 4. Graceful Connection & Error Handling

To deliver a premium, resilient user experience, network requests are wrapped in explicit catch blocks that categorize and present errors user-friendly way:

1. **Server Unreachable / Connection Refused**: Displays a clear notification panel stating: *"تعذر الاتصال بالخادم الرئيسي. يرجى التحقق من تشغيل الواجهة البرمجية (FastAPI)."* instead of crashing.
2. **Empty States**: If search returns successfully but results is empty, a clean interface displaying *"لا توجد نتائج مطابقة"* is rendered.
3. **Invalid Request States**: Under-minimum query lengths (less than 1 character) are caught client-side, clearing previous states immediately.
