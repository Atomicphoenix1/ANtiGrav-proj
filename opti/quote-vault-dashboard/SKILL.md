# Skill: Cosmic Alchemist Theme Kit
# Path: C:\Users\SDS Scholar\.gemini\antigravity\scratch\quote-vault-dashboard\SKILL.md

A specialized agent skill designed to teach any AI coding assistant how to instantly apply the premium **"Cosmic Alchemist"** theme to any web application, dashboard, or UI layout. It blends deep space canvas starfields, glowing cyberpunk neon borders, and classical academic journal typography.

## 📋 Metadata
*   **Name**: `cosmic_alchemist_themekit`
*   **Version**: `1.0.0`
*   **Description**: Styles any web application with an immersive dark cosmic space, glassmorphism cards, glowing cyber-neon highlights, and rich classical typography.
*   **Trigger Keywords**: `cosmic theme`, `alchemist vibe`, `glassmorphism dark`, `twinkling stars background`, `premium dashboard`, `gold and cyan neon`

---

## 🛠️ Step-by-Step Integration Guide

To apply this theme kit to any index page, follow these three phases:

### Phase 1: The HTML Head & Structure
Add the following Google Fonts, Lucide icons, and canvas overlay to the target page.

```html
<!-- 1. Import Google Fonts -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cinzel+Decorative:wght@700&family=Playfair+Display:ital,wght@0,400..700;1,400..700&family=JetBrains+Mono:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">

<!-- 2. Import Lucide Icons (Premium UI visual indicators) -->
<script src="https://unpkg.com/lucide@latest"></script>

<!-- 3. Add Twinkling Canvas Starfield at the start of <body> -->
<canvas id="starfield" style="position:fixed; top:0; left:0; width:100vw; height:100vh; z-index:-1; pointer-events:none;"></canvas>
```

---

### Phase 2: The Core Style System (`style.css`)
Inject these custom design tokens, scrollbars, glowing cards, and animations into your CSS.

```css
/* --- Color Tokens & Layout --- */
:root {
  --space-black: #05060d;
  --space-indigo: #0b0c1b;
  --space-purple: #1e113a;
  --glass-bg: rgba(11, 13, 28, 0.6);
  --glass-border: rgba(255, 255, 255, 0.06);
  
  --neon-gold: #f59e0b;
  --neon-gold-rgb: 245, 158, 11;
  --neon-cyan: #06b6d4;
  --neon-cyan-rgb: 6, 182, 212;
  --neon-violet: #8b5cf6;
  --parchment: #fef08a;
  
  --font-title: 'Cinzel Decorative', serif;
  --font-body: 'Playfair Display', serif;
  --font-mono: 'JetBrains Mono', monospace;
  --font-sans: 'Inter', sans-serif;
  
  --radius-md: 16px;
  --radius-lg: 24px;
}

body {
  background-color: var(--space-black);
  background-image: radial-gradient(circle at 50% 50%, var(--space-indigo) 0%, var(--space-black) 100%);
  color: #f3f4f6;
  font-family: var(--font-sans);
  min-height: 100vh;
}

/* --- Scrollbar Customization --- */
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: rgba(11, 13, 28, 0.3); }
::-webkit-scrollbar-thumb { background: rgba(245, 158, 11, 0.2); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: rgba(245, 158, 11, 0.4); }

/* --- Translucent Glass Cards --- */
.card-glass {
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-radius: var(--radius-md);
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
}

/* --- Cosmic Alchemist Focus Cards --- */
.focus-card-glow {
  position: relative;
  background: rgba(10, 11, 23, 0.55);
  border: 1px solid rgba(245, 158, 11, 0.2);
  backdrop-filter: blur(20px);
  border-radius: var(--radius-lg);
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6), 
              0 0 20px rgba(245, 158, 11, 0.25);
  overflow: hidden;
}

.focus-card-glow::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; height: 2px;
  background: linear-gradient(90deg, transparent, var(--neon-gold), var(--neon-cyan), transparent);
  animation: pan-glow 4s infinite linear;
}

/* Cyber Alchemist Card Corner Brackets */
.card-bracket {
  position: absolute; width: 14px; height: 14px; border-color: var(--neon-gold); border-style: solid; opacity: 0.6; pointer-events: none;
}
.card-bracket.top-left { top: 12px; left: 12px; border-width: 2px 0 0 2px; }
.card-bracket.top-right { top: 12px; right: 12px; border-width: 2px 2px 0 0; }
.card-bracket.bottom-left { bottom: 12px; left: 12px; border-width: 0 0 2px 2px; }
.card-bracket.bottom-right { bottom: 12px; right: 12px; border-width: 0 2px 2px 0; }

/* --- Glow Animations --- */
@keyframes pan-glow {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
```

---

### Phase 3: The Particle Engine Script (`starfield.js`)
Include this canvas-based space generator and execute it.

```javascript
window.initStarfield = function() {
  const canvas = document.getElementById('starfield');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let stars = [];
  const STAR_COUNT = 120;
  const SPEED = 0.05;
  const COLORS = ['rgba(255,255,255,0.8)', 'rgba(173,216,230,0.7)', 'rgba(221,160,221,0.6)', 'rgba(255,223,186,0.7)'];

  function resizeCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    initStars();
  }

  function initStars() {
    stars = [];
    for (let i = 0; i < STAR_COUNT; i++) {
      stars.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        size: Math.random() * 1.5 + 0.5,
        color: COLORS[Math.floor(Math.random() * COLORS.length)],
        twinkleSpeed: Math.random() * 0.02 + 0.005,
        twinklePhase: Math.random() * Math.PI,
        angle: Math.random() * Math.PI * 2
      });
    }
  }

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Ambient cosmic dust background glow
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const gradient = ctx.createRadialGradient(centerX, centerY, 10, centerX, centerY, Math.max(canvas.width, canvas.height) * 0.8);
    gradient.addColorStop(0, 'rgba(30, 15, 60, 0.25)');
    gradient.addColorStop(0.5, 'rgba(10, 15, 35, 0.1)');
    gradient.addColorStop(1, 'rgba(5, 5, 15, 0)');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    for (let i = 0; i < stars.length; i++) {
      const star = stars[i];
      star.twinklePhase += star.twinkleSpeed;
      const alphaMultiplier = Math.abs(Math.sin(star.twinklePhase));

      ctx.beginPath();
      ctx.arc(star.x, star.y, star.size, 0, Math.PI * 2);
      ctx.fillStyle = star.color.replace(/[\d.]+\)$/, `${alphaMultiplier})`);
      ctx.shadowBlur = star.size * 3;
      ctx.shadowColor = star.color;
      ctx.fill();
      ctx.shadowBlur = 0;

      // Float drift mechanics
      star.x += Math.cos(star.angle) * SPEED;
      star.y += Math.sin(star.angle) * SPEED;

      if (star.x < 0) star.x = canvas.width;
      if (star.x > canvas.width) star.x = 0;
      if (star.y < 0) star.y = canvas.height;
      if (star.y > canvas.height) star.y = 0;
    }
    requestAnimationFrame(draw);
  }

  window.addEventListener('resize', resizeCanvas);
  resizeCanvas();
  draw();
};
```

---

## 🎨 Design Rules for the Agent
When applying this skill theme kit, verify the following design parameters are met:
1.  **Strict Contrast**: High contrast must be maintained. Monospaced elements (`var(--font-mono)`) must represent dynamic metrics (e.g. counters, timestamps).
2.  **Glassmorphic Hierarchy**: Secondary cards use standard translucent blurred panels. Interactive focus cards get the custom dual glowing gradients and metallic brackets.
3.  **Typography Consistency**: Header logos use `Cinzel Decorative` (bold uppercase with letters spaced apart). Body content and quotes use `Playfair Display` (slightly italicized, larger font sizes). System tags, stats, and metadata labels use uppercase `JetBrains Mono`.
