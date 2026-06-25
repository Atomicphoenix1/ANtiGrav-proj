# Accessibility Standards — WCAG 2.2 AA Per-Component Checklist

## Core Principles

1. **Perceivable** — Content must be presentable to all senses
2. **Operable** — UI must be usable with any input method
3. **Understandable** — Content and UI must be clear
4. **Robust** — Must work with current and future assistive technologies

---

## Button

- [ ] Uses `<button>` or has `role="button"` + keyboard handling
- [ ] Text describes the action (not just "click here")
- [ ] Visible focus ring (`:focus-visible`)
- [ ] Disabled state is visually distinct and `aria-disabled`
- [ ] Loading state announces to screen reader (`aria-busy="true"`)
- [ ] Icon buttons have `aria-label` text
- [ ] Color is not the only indicator (add underline or icon)
- [ ] Touch target >= 44×44px

```tsx
<button
  aria-label={iconOnly ? "Close dialog" : undefined}
  aria-busy={isLoading}
  disabled={isLoading}
  className="..."
>
  {icon && <span aria-hidden="true">{icon}</span>}
  {!iconOnly && children}
</button>
```

---

## Input & Text Field

- [ ] Associated with `<label>` (not placeholder-only)
- [ ] Required fields marked with `aria-required` and visual indicator
- [ ] Error message linked via `aria-describedby` or `aria-errormessage`
- [ ] Error state has an `aria-invalid` attribute
- [ ] Helper text linked via `aria-describedby`
- [ ] Placeholder is not the only label
- [ ] Autocomplete attribute for common fields (`given-name`, `email`, etc.)

```tsx
<div role="group">
  <label htmlFor="email">Email</label>
  <input
    id="email"
    type="email"
    aria-required
    aria-invalid={!!error}
    aria-describedby={error ? "email-error" : "email-helper"}
    aria-errormessage={error ? "email-error" : undefined}
    autoComplete="email"
  />
  {error && <p id="email-error" role="alert">{error}</p>}
  {helper && !error && <p id="email-helper">{helper}</p>}
</div>
```

---

## Select (Native + Custom)

- [ ] Native select: use `<select>` with `<option>`
- [ ] Custom select: has `role="listbox"`, options have `role="option"`
- [ ] Keyboard navigation: arrow keys, Enter/Space to select, Escape to close
- [ ] Active option tracked via `aria-activedescendant`
- [ ] Selected option has `aria-selected`
- [ ] Multi-select uses `aria-multiselectable`
- [ ] Combobox pattern: `role="combobox"`, `aria-expanded`, `aria-controls`, `aria-autocomplete`

```tsx
// Custom select pattern
<button
  role="combobox"
  aria-expanded={isOpen}
  aria-controls="listbox-id"
  aria-haspopup="listbox"
  aria-activedescendant={activeOption ? `option-${activeOption}` : undefined}
  onClick={toggle}
>
  {selectedLabel}
</button>
<ul
  id="listbox-id"
  role="listbox"
  aria-label="Options"
  hidden={!isOpen}
>
  {options.map((opt) => (
    <li
      id={`option-${opt.value}`}
      key={opt.value}
      role="option"
      aria-selected={opt.value === selectedValue}
    >
      {opt.label}
    </li>
  ))}
</ul>
```

---

## Card

- [ ] If clickable, use `<button>` or `<a>` not a div with onclick
- [ ] If entire card is a link, content inside uses `aria-hidden="true"` for decorative elements
- [ ] Images have `alt` text describing the content (not just decorative)
- [ ] Heading hierarchy is maintained (`h1`→`h6` order)
- [ ] Focus visible on interactive parts
- [ ] Tab order matches visual order

```tsx
<article className="card">
  <img src={image} alt={imageAlt} />
  <h3>{title}</h3>
  <p>{description}</p>
  <a href={link}>Read more</a>
</article>
```

---

## Modal / Dialog

- [ ] Uses `role="dialog"` or `role="alertdialog"` (for errors/confirmations)
- [ ] Has `aria-modal="true"` and `aria-label` or `aria-labelledby`
- [ ] Focus is trapped inside the modal when open
- [ ] Focus returns to trigger element on close
- [ ] Escape key closes the modal
- [ ] Backdrop click closes (provide visual affordance)
- [ ] Body scroll is locked when modal is open
- [ ] Content behind modal is `inert`
- [ ] Close button has `aria-label="Close"`
- [ ] On open, focus moves to first focusable element or the modal title

```tsx
<div
  role="dialog"
  aria-modal="true"
  aria-labelledby="dialog-title"
  aria-describedby="dialog-desc"
>
  <h2 id="dialog-title">Confirm Delete</h2>
  <p id="dialog-desc">This action cannot be undone.</p>
  <button onClick={confirm}>Delete</button>
  <button onClick={close} aria-label="Close">X</button>
</div>
```

---

## Toast / Notification

- [ ] Uses `role="status"` (non-critical) or `role="alert"` (critical)
- [ ] Live region announces content: `aria-live="polite"` or `aria-live="assertive"`
- [ ] Toast is focusable if it contains actions (undo button, dismiss)
- [ ] Auto-dismiss is pausable on hover/focus
- [ ] Dismiss button has `aria-label="Dismiss notification"`
- [ ] Multiple toasts are managed in a stack (ordered, stacked)

```tsx
<div
  role="alert"
  aria-live="assertive"
  aria-atomic="true"
  className="toast"
>
  <span>{message}</span>
  {action && <button onClick={action}>{actionLabel}</button>}
  <button aria-label="Dismiss notification" onClick={dismiss}>×</button>
</div>
```

---

## Switch / Toggle

- [ ] Uses `role="switch"` (not checkbox)
- [ ] Has `aria-checked` reflecting state (not `aria-selected`)
- [ ] Has visible label (not just icon)
- [ ] Keyboard toggle via Enter or Space
- [ ] Visual state doesn't rely on color alone (add icon/text label)
- [ ] Disabled state has `aria-disabled`

```tsx
<button
  role="switch"
  aria-checked={isOn}
  aria-label="Enable dark mode"
  onClick={toggle}
>
  <span className="slider" />
</button>
```

---

## Tabs

- [ ] Tab list has `role="tablist"`
- [ ] Each tab has `role="tab"` + `aria-selected` + `aria-controls` pointing to panel
- [ ] Each panel has `role="tabpanel"` + `aria-labelledby` pointing to tab
- [ ] Arrow keys navigate tabs (left/right or up/down)
- [ ] Home/End keys go to first/last tab
- [ ] Focusable panels have `tabindex="0"`

```tsx
<div role="tablist" aria-label="Content sections">
  <button role="tab" aria-selected="true" aria-controls="panel-1" id="tab-1">
    Tab 1
  </button>
</div>
<div role="tabpanel" aria-labelledby="tab-1" id="panel-1">
  Panel content
</div>
```

---

## Color & Contrast

| Element | Minimum Ratio | Enhanced Ratio |
|---------|--------------|----------------|
| Normal text (<18px) | 4.5:1 AA | 7:1 AAA |
| Large text (≥18px bold or ≥24px) | 3:1 AA | 4.5:1 AAA |
| UI components & graphical objects | 3:1 | — |
| Focus indicators | 3:1 | — |

### Quick contrast check
```css
/* Use this to audit contrast */
* {
  outline: 2px solid color-mix(in srgb, currentColor 50%, transparent) !important;
}
```

### Ensure color independence
```css
/* Never rely on hue alone */
.error-text {
  color: var(--color-danger);
}

/* ✅ Always pair color with a secondary indicator */
.error-text::before {
  content: "⚠ ";
}
```

---

## Focus Management

- [ ] All interactive elements have visible focus styles
- [ ] Use `:focus-visible` not `:focus` (shows ring only on keyboard nav)
- [ ] Remove focus ring for mouse/pointer interactions while keeping keyboard focus visible
- [ ] Skip navigation link is first focusable element on page
- [ ] Custom focus ring is at least 2px thick with 3:1 contrast to adjacent colors

```css
/* Modern focus ring */
:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
  border-radius: 2px;
}

/* Remove focus ring for pointer interactions */
:focus:not(:focus-visible) {
  outline: none;
}
```

---

## Testing Checklist

### Automated
- [ ] Run axe-core or WAVE on every page/component
- [ ] Check color contrast with a tool (axe, Colour Contrast Analyser)
- [ ] Validate HTML (no duplicate IDs, proper nesting)

### Keyboard
- [ ] Tab through the entire page (no keyboard traps)
- [ ] Tab order matches visual order
- [ ] All interactive elements are reachable and operable with keyboard
- [ ] Escape closes modals, dropdowns, menus
- [ ] Arrow keys work for navigation widgets

### Screen Reader
- [ ] Test with NVDA (Windows) or VoiceOver (Mac)
- [ ] Navigate via headings (H key)
- [ ] Navigate via landmarks (D key)
- [ ] Navigate via form controls (Tab)
- [ ] Dynamic content changes are announced

### Zoom
- [ ] Page works at 200% zoom without horizontal scrolling
- [ ] Text doesn't get clipped when resized
- [ ] Responsive layout holds up at 400% zoom (1280px → 320px equivalent)
