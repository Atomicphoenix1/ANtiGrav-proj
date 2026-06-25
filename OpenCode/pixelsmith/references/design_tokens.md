# Design Tokens — Architecture & Best Practices

## What Are Design Tokens?

Design tokens are the visual atoms of a design system — named variables that store design decisions (color, spacing, typography, shadow, motion) so they can be used consistently across platforms.

---

## Token Naming Convention

### Semantic vs. Primitive Tokens

```
Primitive (raw values)
  --blue-500: #3b82f6
  --spacing-4: 1rem
  --font-size-lg: 1.125rem

Semantic (contextual meaning)
  --color-primary: var(--blue-500)
  --space-inset-md: var(--spacing-4)
  --text-heading: var(--font-size-lg)
```

**Rule:** Components always reference semantic tokens. Primitives only change when you update the palette.

### Naming Structure

```
--{category}-{property}-{variant}-{state}
```

| Part | Examples |
|------|---------|
| Category | `color`, `space`, `font`, `shadow`, `radius`, `motion` |
| Property | `background`, `text`, `border`, `inset`, `stack`, `inline`, `size`, `weight` |
| Variant | `primary`, `secondary`, `danger`, `sm`, `md`, `lg`, `heading`, `body` |
| State | `hover`, `active`, `disabled`, `focus` |

```
--color-background-primary
--color-text-on-primary
--color-border-focus
--space-stack-md
--space-inline-lg
--font-size-heading-xl
--font-weight-semibold
--shadow-elevation-md
--radius-sm
--motion-duration-fast
--motion-easing-bounce
```

---

## Theme Architecture

### Light / Dark / High-Contrast Structure

```css
:root,
[data-theme="light"] {
  color-scheme: light;
  
  /* Primitives */
  --white: #ffffff;
  --gray-50: #f9fafb;
  --gray-900: #111827;
  --blue-500: #3b82f6;
  --red-500: #ef4444;

  /* Semantic tokens */
  --color-surface: var(--white);
  --color-text: var(--gray-900);
  --color-primary: var(--blue-500);
  --color-danger: var(--red-500);
}

[data-theme="dark"] {
  color-scheme: dark;

  /* Same semantic tokens, different primitives */
  --color-surface: var(--gray-900);
  --color-text: var(--gray-50);
}

[data-theme="high-contrast"] {
  --color-primary: Highlight;
  --color-text: CanvasText;
  --color-surface: Canvas;
}
```

### Using `light-dark()` (CSS-native theming)

```css
:root {
  color-scheme: light dark;
  --color-surface: light-dark(#ffffff, #1a1a2e);
  --color-text: light-dark(#1a1a2e, #e8e8f0);
  --color-primary: light-dark(#3b82f6, #60a5fa);
}
```

---

## Spacing Scale

A consistent spacing scale prevents layout drift.

```css
:root {
  --space-0:   0px;
  --space-1:   0.25rem;  /*  4px */
  --space-2:   0.5rem;   /*  8px */
  --space-3:   0.75rem;  /* 12px */
  --space-4:   1rem;     /* 16px */
  --space-5:   1.25rem;  /* 20px */
  --space-6:   1.5rem;   /* 24px */
  --space-8:   2rem;     /* 32px */
  --space-10:  2.5rem;   /* 40px */
  --space-12:  3rem;     /* 48px */
  --space-16:  4rem;     /* 64px */
  --space-20:  5rem;     /* 80px */
  --space-24:  6rem;     /* 96px */

  /* Semantic spacing */
  --space-inset-sm: var(--space-2);
  --space-inset-md: var(--space-4);
  --space-inset-lg: var(--space-6);
  --space-stack-sm: var(--space-2);
  --space-stack-md: var(--space-4);
  --space-stack-lg: var(--space-8);
  --space-inline-sm: var(--space-2);
  --space-inline-md: var(--space-4);
  --space-inline-lg: var(--space-6);
}
```

---

## Typography Scale

```css
:root {
  /* Size scale */
  --font-size-xs:    0.75rem;   /* 12px */
  --font-size-sm:    0.875rem;  /* 14px */
  --font-size-base:  1rem;      /* 16px */
  --font-size-lg:    1.125rem;  /* 18px */
  --font-size-xl:    1.25rem;   /* 20px */
  --font-size-2xl:   1.5rem;    /* 24px */
  --font-size-3xl:   1.875rem;  /* 30px */
  --font-size-4xl:   2.25rem;   /* 36px */
  --font-size-5xl:   3rem;      /* 48px */

  /* Weight */
  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;

  /* Line height */
  --leading-tight: 1.25;
  --leading-normal: 1.5;
  --leading-relaxed: 1.625;

  /* Letter spacing */
  --tracking-tight: -0.025em;
  --tracking-normal: 0;
  --tracking-wide: 0.025em;

  /* Semantic typography */
  --text-heading-1: var(--font-size-4xl) / var(--leading-tight) var(--font-weight-bold);
  --text-heading-2: var(--font-size-3xl) / var(--leading-tight) var(--font-weight-semibold);
  --text-heading-3: var(--font-size-2xl) / var(--leading-normal) var(--font-weight-semibold);
  --text-body:      var(--font-size-base) / var(--leading-normal) var(--font-weight-normal);
  --text-small:     var(--font-size-sm) / var(--leading-normal) var(--font-weight-normal);
  --text-label:     var(--font-size-sm) / var(--leading-normal) var(--font-weight-medium);
}
```

---

## Shadow & Elevation

```css
:root {
  --shadow-xs:   0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow-sm:   0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
  --shadow-md:   0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
  --shadow-lg:   0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
  --shadow-xl:   0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);

  /* Dark mode shadows (lighter for dark backgrounds) */
  [data-theme="dark"] & {
    --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.4), 0 2px 4px -2px rgb(0 0 0 / 0.3);
  }
}
```

---

## Border Radius

```css
:root {
  --radius-none: 0px;
  --radius-sm:   0.125rem;   /*  2px */
  --radius-md:   0.375rem;   /*  6px */
  --radius-lg:   0.5rem;     /*  8px */
  --radius-xl:   0.75rem;    /* 12px */
  --radius-2xl:  1rem;       /* 16px */
  --radius-3xl:  1.5rem;     /* 24px */
  --radius-full: 9999px;
}
```

---

## Motion Tokens

```css
:root {
  /* Durations */
  --duration-instant: 0ms;
  --duration-fast:   150ms;
  --duration-normal: 250ms;
  --duration-slow:   350ms;
  --duration-slower: 500ms;

  /* Easing curves */
  --easing-linear: linear;
  --easing-in:     cubic-bezier(0.4, 0, 1, 1);
  --easing-out:    cubic-bezier(0, 0, 0.2, 1);
  --easing-in-out: cubic-bezier(0.4, 0, 0.2, 1);
  --easing-spring: cubic-bezier(0.34, 1.56, 0.64, 1);

  /* Semantic motion */
  --motion-enter: var(--duration-normal) var(--easing-out);
  --motion-exit:  var(--duration-fast) var(--easing-in);
  --motion-shift: var(--duration-normal) var(--easing-in-out);
  --motion-bounce: var(--duration-normal) var(--easing-spring);
}
```

---

## Organizing Token Files

```
styles/
  tokens/
    _primitives.css      # Raw color, spacing, type values
    _semantic.css        # Contextual mappings
    _theme-light.css     # Light theme overrides
    _theme-dark.css      # Dark theme overrides
    _theme-contrast.css  # High contrast overrides
  globals.css            # @import all token layers + base styles
```

---

## Token Checklist

- [ ] Every color in components comes from a semantic token
- [ ] No hardcoded spacing values in components
- [ ] Typography uses the scale — no arbitrary font-size
- [ ] Shadows use elevation tokens
- [ ] Radii use the radius scale
- [ ] Motion has duration and easing tokens
- [ ] Dark mode uses the same tokens with different values
- [ ] High contrast mode is a theme variant, not a media query hack
- [ ] Tokens are documented (where they are and how to use them)
- [ ] No dead tokens (tokens that nothing references)
