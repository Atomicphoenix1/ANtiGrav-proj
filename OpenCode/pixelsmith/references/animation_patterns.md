# Animation Patterns — Performant, Accessible Motion

## GPU-Composited Properties Only

For 60fps animations, only animate properties the GPU can composite without triggering layout or paint.

### Safe to animate
```css
/* ✅ GPU-composited — transforms and opacity only */
transform: translate(), scale(), rotate()
opacity
filter (in some browsers)
clip-path (in some browsers)
```

### Avoid animating
```css
/* ❌ Triggers layout (too expensive) */
width, height, top, left, right, bottom
margin, padding, border-width
font-size, line-height
flex-basis, grid-template

/* ⚠️ Triggers paint (expensive) */
color, background-color, border-color
box-shadow (position changes are OK with will-change)
border-radius
```

### Framer Motion enforcement
Framer Motion automatically converts layout animations to `transform` where possible.

---

## The FLIP Technique

FLIP = First, Last, Invert, Play. Animates expensive layout changes as transforms.

```javascript
// Manual FLIP
function flipAnimation(element, callback) {
  const first = element.getBoundingClientRect();
  callback(); // make the layout change
  const last = element.getBoundingClientRect();

  const dx = first.left - last.left;
  const dy = first.top - last.top;
  const dw = first.width / last.width;
  const dh = first.height / last.height;

  element.animate([
    { transform: `translate(${dx}px, ${dy}px) scale(${dw}, ${dh})` },
    { transform: "translate(0, 0) scale(1, 1)" }
  ], { duration: 300, easing: "ease-out" });
}

// Framer Motion layout animation
<motion.div layout transition={{ type: "spring", stiffness: 300, damping: 25 }}>
```

---

## Reduced Motion — `prefers-reduced-motion`

Always respect user preferences.

```css
/* Kill all animation globally */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

### Framer Motion with reduced motion
```tsx
import { useReducedMotion } from "framer-motion";

function Component() {
  const shouldReduceMotion = useReducedMotion();

  return (
    <motion.div
      animate={shouldReduceMotion ? { opacity: 1 } : { x: 0, opacity: 1 }}
      initial={shouldReduceMotion ? { opacity: 0 } : { x: -20, opacity: 0 }}
      transition={{ duration: shouldReduceMotion ? 0 : 0.3 }}
    />
  );
}
```

### Provide safe fallback animations
```tsx
const variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.05 }
  }
};

const childVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: (i) => ({
    opacity: 1,
    y: 0,
    transition: {
      delay: i * 0.05,
      type: "spring",
      stiffness: 300,
      damping: 24,
    },
  }),
};
```

---

## Spring Physics

Springs feel more natural than linear or ease transitions.

```tsx
// Soft spring (gentle)
<motion.div
  transition={{ type: "spring", stiffness: 100, damping: 20 }}
/>

// Snappy spring (bouncy)
<motion.div
  transition={{ type: "spring", stiffness: 400, damping: 10 }}
/>

// Stiff spring (precise)
<motion.div
  transition={{ type: "spring", stiffness: 500, damping: 30 }}
/>
```

| Stiffness | Damping | Feel |
|-----------|---------|------|
| 100 | 20 | Soft, slow, rubbery |
| 200 | 15 | Medium bounce |
| 300 | 12 | Bouncy, playful |
| 400 | 10 | Snappy, energetic |
| 500 | 30 | Stiff, precise |
| 1000 | 50 | Almost instant |

---

## Stagger Patterns

Animate children in sequence for polished list reveals.

```tsx
// Container
const container = {
  hidden: {},
  show: {
    transition: {
      staggerChildren: 0.07,
      delayChildren: 0.1,
    },
  },
};

// Child
const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 },
};

// Usage
<motion.ul variants={container} initial="hidden" animate="show">
  {items.map((item) => (
    <motion.li key={item.id} variants={item}>
      {item.content}
    </motion.li>
  ))}
</motion.ul>
```

---

## Scroll-Triggered Animations

### Intersection Observer pattern
```tsx
import { useInView } from "framer-motion";

function RevealSection({ children }) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 50 }}
      animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 50 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
    >
      {children}
    </motion.div>
  );
}
```

### Pure CSS scroll-driven
```css
@keyframes reveal {
  from {
    opacity: 0;
    transform: scale(0.8);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.reveal {
  animation: reveal linear both;
  animation-timeline: view();
  animation-range: entry 0% entry 100%;
}
```

---

## Page Transitions

```tsx
<AnimatePresence mode="wait">
  <motion.div
    key={router.asPath}
    initial={{ opacity: 0, y: 8 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -8 }}
    transition={{ duration: 0.2, ease: "easeInOut" }}
  >
    <Component {...pageProps} />
  </motion.div>
</AnimatePresence>
```

---

## Performance Checklist

- [ ] Only animate `opacity` and `transform`
- [ ] Use `transform: translateZ(0)` or `will-change: transform` on animated elements (sparingly)
- [ ] Avoid animating `width`, `height`, `top`, `left`
- [ ] Prefer CSS animations over JS `requestAnimationFrame` loops
- [ ] Use `content-visibility: auto` on off-screen animated elements
- [ ] Test on low-power devices (phone, older laptop)
- [ ] Respect `prefers-reduced-motion`
- [ ] Keep animation duration under 500ms for functional motion
- [ ] Use `useReducedMotion()` in Framer Motion projects
- [ ] Avoid animating more than 10-15 elements simultaneously
