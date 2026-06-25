# CSS Mastery — Modern Techniques

## Container Queries

The responsive tool that queries the container's size, not the viewport.

```css
/* Define a containment context */
.card-container {
  container-type: inline-size;
  container-name: card;
}

/* Query the container */
@container card (min-width: 400px) {
  .card {
    display: grid;
    grid-template-columns: 200px 1fr;
  }
}

@container card (max-width: 399px) {
  .card {
    display: flex;
    flex-direction: column;
  }
}
```

### Container Query Units
- `cqw` — 1% of container width
- `cqh` — 1% of container height
- `cqi` — 1% of container inline size
- `cqb` — 1% of container block size
- `cqmin` — smaller of cqi / cqb
- `cqmax` — larger of cqi / cqb

```css
.card-title {
  font-size: clamp(1rem, 4cqi, 2rem);
}
```

---

## The `:has()` Parent Selector

Style a parent based on the state of its children.

```css
/* Card with an image gets a different layout */
.card:has(img) {
  grid-template-columns: 200px 1fr;
}

/* Form group with error state */
.field-group:has(:invalid) .error-message {
  display: block;
}

/* Style the parent when a child is focused */
.nav-item:has(:focus-visible) {
  outline: 2px solid blue;
  border-radius: 4px;
}

/* Dark mode toggle detection */
html:has([data-theme="dark"]) {
  --bg: #111;
  --text: #eee;
}

/* Stagger children that have content */
.grid:has(> :nth-child(3)) {
  --columns: 3;
}
```

---

## CSS Cascade Layers

Control specificity by layering styles explicitly.

```css
@layer reset, base, components, utilities;

@layer reset {
  *,
  *::before,
  *::after {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }
}

@layer base {
  :root {
    --color-primary: #3b82f6;
    --color-surface: #ffffff;
  }
  body {
    font-family: system-ui, sans-serif;
    line-height: 1.5;
    color: var(--color-text);
    background: var(--color-surface);
  }
}

@layer components {
  .btn {
    display: inline-flex;
    align-items: center;
    padding: 0.5rem 1rem;
    border-radius: 0.375rem;
    background: var(--color-primary);
    color: white;
  }
}

@layer utilities {
  .p-4 { padding: 1rem; }
  .text-center { text-align: center; }
}
```

---

## `color-mix()` — Dynamic Color Blending

Generate derived colors without pre-processors.

```css
:root {
  --brand: #3b82f6;
  --brand-light: color-mix(in srgb, var(--brand) 20%, white);
  --brand-dark: color-mix(in srgb, var(--brand) 80%, black);
  --brand-muted: color-mix(in srgb, var(--brand) 60%, transparent);
  --brand-text: color-mix(in srgb, var(--brand) 85%, black);
}

.btn-outline {
  border: 1px solid var(--brand);
  color: var(--brand);
  background: var(--brand-light);
}

.btn-outline:hover {
  background: color-mix(in srgb, var(--brand) 15%, white);
}
```

Color interpolation methods: `srgb`, `srgb-linear`, `lab`, `oklab`, `xyz`, `hsl`, `hwb`, `lch`, `oklch`.

---

## `light-dark()` — Native Dark Mode

CSS-native light/dark theming without `prefers-color-scheme` media queries.

```css
:root {
  color-scheme: light dark;
  --text: light-dark(#1a1a2e, #e8e8f0);
  --bg: light-dark(#ffffff, #0f0f1a);
  --surface: light-dark(#f5f5f7, #1a1a2e);
  --border: light-dark(#d4d4d8, #3f3f50);
  --primary: light-dark(#3b82f6, #60a5fa);
}

body {
  color: var(--text);
  background: var(--bg);
}

.card {
  background: var(--surface);
  border: 1px solid var(--border);
}
```

The `color-scheme` property is required for `light-dark()` to know which color to return.

---

## Scroll-Driven Animations

```css
/* Timeline attached to scroll container */
@keyframes fade-in {
  from { opacity: 0; transform: scale(0.8); }
  to { opacity: 1; transform: scale(1); }
}

@keyframes reveal {
  from { clip-path: inset(0 100% 0 0); }
  to { clip-path: inset(0 0 0 0); }
}

.animate-on-scroll {
  animation: fade-in linear both;
  animation-timeline: view();
  animation-range: entry 0% entry 100%;
}

.reveal-text {
  animation: reveal linear both;
  animation-timeline: view();
  animation-range: entry 0% entry 80%;
}
```

### Key Timeline Concepts
- `view()` — tracks element's position within its scrollport
- `scroll()` — tracks scrollport scroll position
- `animation-range` — defines start/end positions of the animation along the timeline
- `animation-timeline` — binds animation to a scroll timeline

---

## Advanced `clip-path` Techniques

```css
/* Diagonal section divider */
.hero {
  clip-path: polygon(0 0, 100% 0, 100% 85%, 0 100%);
}

/* Hexagonal shape */
.hexagon {
  clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%);
}

/* Smooth blob */
.blob {
  clip-path: path("M 0,0 C 30,10 40,40 50,20 S 70,50 100,0 Z");
}

/* Animated clip-path */
@keyframes morph {
  0% { border-radius: 60% 40% 30% 70% / 60% 30% 70% 40%; }
  50% { border-radius: 30% 60% 70% 40% / 50% 60% 30% 60%; }
  100% { border-radius: 60% 40% 30% 70% / 60% 30% 70% 40%; }
}

.morph-card {
  animation: morph 8s ease-in-out infinite;
}
```

---

## CSS Grid Patterns

### Auto-fill with minimum sizes
```css
.responsive-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 1rem;
}
```

### Subgrid
```css
.card-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
}

.card {
  display: grid;
  grid-row: span 3;
  grid-template-rows: subgrid;
}
```

### Masonry with CSS (experimental)
```css
.masonry {
  columns: 3;
  column-gap: 1rem;
}

.masonry > * {
  break-inside: avoid;
  margin-bottom: 1rem;
}
```

---

## `@property` — Registered Custom Properties

```css
@property --gradient-angle {
  syntax: "<angle>";
  inherits: false;
  initial-value: 0deg;
}

@property --gradient-color-1 {
  syntax: "<color>";
  inherits: false;
  initial-value: #667eea;
}

@property --gradient-color-2 {
  syntax: "<color>";
  inherits: false;
  initial-value: #764ba2;
}

.gradient-box {
  background: linear-gradient(var(--gradient-angle), var(--gradient-color-1), var(--gradient-color-2));
  transition: --gradient-angle 0.5s, --gradient-color-1 0.5s, --gradient-color-2 0.5s;
}

.gradient-box:hover {
  --gradient-angle: 180deg;
  --gradient-color-1: #f093fb;
  --gradient-color-2: #f5576c;
}
```

---

## Practical Anti-Patterns

| Avoid | Do Instead |
|---|---|
| `!important` everywhere | Use cascade layers or specificity |
| Magic number breakpoints | Use container queries for components |
| `will-change: transform` on everything | Only on elements that will change, remove after animation |
| `all: unset` | Explicitly reset what you need |
| `height: 100vh` on mobile | Use `100dvh` (dynamic viewport height) |
| `overflow: hidden` for layout | Use `min-height: 0` in flex/grid children |
| Nested calc() | Use `color-mix()` or CSS variables |
