# PixelSmith — UI Crafting Skill

Master the intersection of component engineering and CSS artistry. Generate production-grade, accessible, animated UI with deep design-system thinking.

## Quick Start

```bash
# Forge a component from a plain description
python scripts/component_forge.py "button with icon, loading state, 3 sizes, dark mode"

# Generate animations from plain English
python scripts/animation_lab.py "slide in from left with bounce"

# Extract design tokens from existing code
python scripts/token_extractor.py --input ./src --format tailwind
```

## Core Capabilities

### 1. Component Forge
Turns natural language specs into production-ready React/TypeScript components.

**What you get per component:**
- TypeScript with strict types
- Tailwind CSS v4 classes
- Variants (size, color, tone)
- All interactive states (hover, focus, active, disabled, loading)
- Framer Motion animations (mount, hover, tap)
- Dark mode via CSS `light-dark()` / Tailwind `dark:`
- WCAG-compliant ARIA attributes
- Storybook story file
- Compound component pattern where applicable

**Usage:**
```bash
python scripts/component_forge.py <description> [--output-dir <path>]
```

**Examples:**
```bash
python scripts/component_forge.py "toast notification with success/error/info variants, auto-dismiss, close button"
python scripts/component_forge.py "card with image, title, description, hover scale effect, dark mode"
python scripts/component_forge.py "dropdown select with search, keyboard navigation, async options"
```

### 2. Animation Lab
Generates CSS keyframes and Framer Motion variants from plain-language descriptions.

**Capabilities:**
- Entrance / exit animations (slide, fade, scale, rotate)
- Hover and tap interactions
- Scroll-triggered reveals
- Staggered list animations
- Spring-physics-based motion
- `prefers-reduced-motion` respect baked in
- GPU-optimized properties only

**Usage:**
```bash
python scripts/animation_lab.py <description> [--format css|framer] [--output-dir <path>]
```

**Examples:**
```bash
python scripts/animation_lab.py "stagger fade in from bottom for list items" --format framer
python scripts/animation_lab.py "pulse glow on hover with spring" --format css
python scripts/animation_lab.py "page transition slide left exit, slide right enter" --format framer
```

### 3. Token Extractor
Reverse-engineers design tokens from existing codebases.

**What it extracts:**
- Color palette (hex/rgb/hsl values from CSS, Tailwind, inline styles)
- Spacing scale (margin, padding, gap values)
- Typography scale (font sizes, line heights, font families)
- Shadow / blur values
- Border radius scale
- Breakpoints (media query values)

**Output formats:**
- CSS custom properties (`--color-primary: ...`)
- Tailwind CSS v4 config (`@theme { ... }`)
- Raw JSON for design tool import

**Usage:**
```bash
python scripts/token_extractor.py --input <path> [--format css|tailwind|json] [--output <path>]
```

**Examples:**
```bash
python scripts/token_extractor.py --input ./src/styles --format tailwind --output ./theme.css
python scripts/token_extractor.py --input ./src/components --format json
```

## Reference Library

| Document | What it covers |
|----------|---------------|
| `references/css_mastery.md` | Container queries, `:has()`, cascade layers, `color-mix()`, scroll-driven animations, clip-path, `light-dark()` |
| `references/design_tokens.md` | Semantic vs. primitive tokens, naming conventions, theme architecture, dark/light/high-contrast design, token scaling |
| `references/animation_patterns.md` | FLIP technique, GPU-composited properties, spring physics, reduced-motion patterns, scroll-triggered workflows, stagger timing |
| `references/a11y_standards.md` | Per-component WCAG 2.2 AA checklist, ARIA patterns, focus management, color contrast, keyboard navigation, screen reader support |

## Component Templates

Located in `templates/components/`:
- `Button` — 6 variants, 4 sizes, icon/loading/spinner support, dark mode
- `Card` — Image header, body, footer slots; hover effects; dark mode
- `Modal` — Portal-based, focus trap, escape close, backdrop, scroll lock, animated enter/exit
- `Input` — Label, error state, helper text, icon slots, dark mode, floating label variant
- `Select` — Native and custom variants, search/filter, keyboard nav, async options
- `Toast` — Stack manager, auto-dismiss, swipe-to-dismiss, progress bar, 4 variants

## Animation Templates

Located in `templates/animations/`:
- Common entrance sequences (fade, slide, scale, rotate)
- Hover / focus / active state transitions
- Scroll-triggered reveal specs
- Stagger timing configurations
- Page transition blueprints

## Development Workflow

```bash
# 1. Extract tokens to establish your design system
python scripts/token_extractor.py --input ./src --format tailwind --output ./tokens.css

# 2. Forge components using those tokens
python scripts/component_forge.py "primary button with icon" --output-dir ./components/ui

# 3. Add animations
python scripts/animation_lab.py "page transitions" --format framer --output-dir ./lib/animations

# 4. Reference docs for deep dives
#    - css_mastery.md for layout and visual techniques
#    - design_tokens.md for token architecture
#    - animation_patterns.md for animation best practices
#    - a11y_standards.md for accessibility compliance
```

## Best Practices Enforced

- Every component respects `prefers-reduced-motion`
- Every interactive element has visible focus styles
- Color contrast meets WCAG AA minimum (4.5:1)
- Components use semantic HTML where possible
- Dark mode via `light-dark()` or `@media prefers-color-scheme`
- Animations only animate `opacity` and `transform` (GPU-composited)
- All components accept `className` for override
- Ref forwarding for reusable library components

## Tech Stack

- **Languages:** Python 3.10+, TypeScript, CSS
- **Frontend:** React 18+, Tailwind CSS v4, Framer Motion 11+
- **Output targets:** Any React + Tailwind project
