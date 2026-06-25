"""
PixelSmith — Animation Lab
Generates CSS keyframes and Framer Motion variants from natural language descriptions.
"""

import argparse
import json
import re
import textwrap
from pathlib import Path
from typing import Optional

ANIMATION_PATTERNS: dict = {
    "fade_in": {
        "description": "Fade in from transparent to opaque",
        "css": textwrap.dedent("""\
            @keyframes fadeIn {
              from { opacity: 0; }
              to   { opacity: 1; }
            }
            .animate-fade-in {
              animation: fadeIn var(--duration, 300ms) var(--easing, ease-out) forwards;
            }"""),
        "framer": {
            "initial": {"opacity": 0},
            "animate": {"opacity": 1},
            "exit": {"opacity": 0},
            "transition": {"duration": 0.3, "ease": "easeOut"},
        },
    },
    "fade_out": {
        "description": "Fade out from opaque to transparent",
        "css": textwrap.dedent("""\
            @keyframes fadeOut {
              from { opacity: 1; }
              to   { opacity: 0; }
            }
            .animate-fade-out {
              animation: fadeOut var(--duration, 250ms) var(--easing, ease-in) forwards;
            }"""),
        "framer": {
            "initial": {"opacity": 1},
            "animate": {"opacity": 0},
            "exit": {"opacity": 0},
            "transition": {"duration": 0.25, "ease": "easeIn"},
        },
    },
    "slide_up": {
        "description": "Slide in from below",
        "css": textwrap.dedent("""\
            @keyframes slideUp {
              from { opacity: 0; transform: translateY(24px); }
              to   { opacity: 1; transform: translateY(0); }
            }
            .animate-slide-up {
              animation: slideUp var(--duration, 350ms) var(--easing, cubic-bezier(0.16, 1, 0.3, 1)) forwards;
            }"""),
        "framer": {
            "initial": {"opacity": 0, "y": 24},
            "animate": {"opacity": 1, "y": 0},
            "exit": {"opacity": 0, "y": -10},
            "transition": {"duration": 0.35, "ease": [0.16, 1, 0.3, 1]},
        },
    },
    "slide_down": {
        "description": "Slide in from above",
        "css": textwrap.dedent("""\
            @keyframes slideDown {
              from { opacity: 0; transform: translateY(-24px); }
              to   { opacity: 1; transform: translateY(0); }
            }
            .animate-slide-down {
              animation: slideDown var(--duration, 350ms) var(--easing, cubic-bezier(0.16, 1, 0.3, 1)) forwards;
            }"""),
        "framer": {
            "initial": {"opacity": 0, "y": -24},
            "animate": {"opacity": 1, "y": 0},
            "exit": {"opacity": 0, "y": 10},
            "transition": {"duration": 0.35, "ease": [0.16, 1, 0.3, 1]},
        },
    },
    "slide_left": {
        "description": "Slide in from the right",
        "css": textwrap.dedent("""\
            @keyframes slideLeft {
              from { opacity: 0; transform: translateX(24px); }
              to   { opacity: 1; transform: translateX(0); }
            }
            .animate-slide-left {
              animation: slideLeft var(--duration, 300ms) var(--easing, cubic-bezier(0.16, 1, 0.3, 1)) forwards;
            }"""),
        "framer": {
            "initial": {"opacity": 0, "x": 24},
            "animate": {"opacity": 1, "x": 0},
            "exit": {"opacity": 0, "x": -24},
            "transition": {"duration": 0.3, "ease": [0.16, 1, 0.3, 1]},
        },
    },
    "slide_right": {
        "description": "Slide in from the left",
        "css": textwrap.dedent("""\
            @keyframes slideRight {
              from { opacity: 0; transform: translateX(-24px); }
              to   { opacity: 1; transform: translateX(0); }
            }
            .animate-slide-right {
              animation: slideRight var(--duration, 300ms) var(--easing, cubic-bezier(0.16, 1, 0.3, 1)) forwards;
            }"""),
        "framer": {
            "initial": {"opacity": 0, "x": -24},
            "animate": {"opacity": 1, "x": 0},
            "exit": {"opacity": 0, "x": 24},
            "transition": {"duration": 0.3, "ease": [0.16, 1, 0.3, 1]},
        },
    },
    "scale_in": {
        "description": "Scale in from smaller size",
        "css": textwrap.dedent("""\
            @keyframes scaleIn {
              from { opacity: 0; transform: scale(0.95); }
              to   { opacity: 1; transform: scale(1); }
            }
            .animate-scale-in {
              animation: scaleIn var(--duration, 200ms) var(--easing, ease-out) forwards;
            }"""),
        "framer": {
            "initial": {"opacity": 0, "scale": 0.95},
            "animate": {"opacity": 1, "scale": 1},
            "exit": {"opacity": 0, "scale": 0.95},
            "transition": {"duration": 0.2, "ease": "easeOut"},
        },
    },
    "scale_out": {
        "description": "Scale out to smaller size",
        "css": textwrap.dedent("""\
            @keyframes scaleOut {
              from { opacity: 1; transform: scale(1); }
              to   { opacity: 0; transform: scale(0.95); }
            }
            .animate-scale-out {
              animation: scaleOut var(--duration, 150ms) var(--easing, ease-in) forwards;
            }"""),
        "framer": {
            "initial": {"opacity": 1, "scale": 1},
            "animate": {"opacity": 0, "scale": 0.95},
            "exit": {"opacity": 0, "scale": 0.95},
            "transition": {"duration": 0.15, "ease": "easeIn"},
        },
    },
    "rotate": {
        "description": "Rotation animation (e.g. spinner)",
        "css": textwrap.dedent("""\
            @keyframes rotate {
              from { transform: rotate(0deg); }
              to   { transform: rotate(360deg); }
            }
            .animate-rotate {
              animation: rotate var(--duration, 1s) linear infinite;
            }"""),
        "framer": {
            "animate": {"rotate": 360},
            "transition": {"duration": 1, "repeat": float("inf"), "ease": "linear"},
        },
    },
    "pulse": {
        "description": "Gentle pulsing opacity",
        "css": textwrap.dedent("""\
            @keyframes pulse {
              0%, 100% { opacity: 1; }
              50%      { opacity: 0.5; }
            }
            .animate-pulse {
              animation: pulse var(--duration, 2s) var(--easing, ease-in-out) infinite;
            }"""),
        "framer": {
            "animate": {"opacity": [1, 0.5, 1]},
            "transition": {"duration": 2, "repeat": float("inf"), "ease": "easeInOut"},
        },
    },
    "bounce": {
        "description": "Bouncing entrance with overshoot",
        "css": textwrap.dedent("""\
            @keyframes bounceIn {
              0%   { opacity: 0; transform: scale(0.3); }
              50%  { opacity: 1; transform: scale(1.05); }
              70%  { transform: scale(0.9); }
              100% { transform: scale(1); }
            }
            .animate-bounce-in {
              animation: bounceIn var(--duration, 500ms) var(--easing, cubic-bezier(0.68, -0.55, 0.27, 1.55)) forwards;
            }"""),
        "framer": {
            "initial": {"opacity": 0, "scale": 0.3},
            "animate": {"opacity": 1, "scale": 1},
            "exit": {"opacity": 0, "scale": 0.3},
            "transition": {"type": "spring", "stiffness": 300, "damping": 12},
        },
    },
    "blur_in": {
        "description": "Blur in from blurry to sharp",
        "css": textwrap.dedent("""\
            @keyframes blurIn {
              from { opacity: 0; filter: blur(8px); }
              to   { opacity: 1; filter: blur(0); }
            }
            .animate-blur-in {
              animation: blurIn var(--duration, 400ms) var(--easing, ease-out) forwards;
            }"""),
        "framer": {
            "initial": {"opacity": 0, "filter": "blur(8px)"},
            "animate": {"opacity": 1, "filter": "blur(0px)"},
            "exit": {"opacity": 0, "filter": "blur(8px)"},
            "transition": {"duration": 0.4, "ease": "easeOut"},
        },
    },
    "flip": {
        "description": "3D flip animation",
        "css": textwrap.dedent("""\
            @keyframes flip {
              0%   { transform: perspective(400px) rotateY(0); }
              100% { transform: perspective(400px) rotateY(180deg); }
            }
            .animate-flip {
              animation: flip var(--duration, 600ms) var(--easing, ease-in-out) forwards;
              backface-visibility: hidden;
            }"""),
        "framer": {
            "initial": {"rotateY": 0},
            "animate": {"rotateY": 180},
            "transition": {"duration": 0.6, "ease": "easeInOut"},
        },
    },
    "wiggle": {
        "description": "Attention-grabbing wiggle/shake",
        "css": textwrap.dedent("""\
            @keyframes wiggle {
              0%, 100% { transform: rotate(0deg); }
              25%      { transform: rotate(-5deg); }
              75%      { transform: rotate(5deg); }
            }
            .animate-wiggle {
              animation: wiggle var(--duration, 300ms) var(--easing, ease-in-out) infinite;
            }"""),
        "framer": {
            "animate": {"rotate": [-5, 5, -5, 0]},
            "transition": {"duration": 0.3, "repeat": float("inf"), "ease": "easeInOut"},
        },
    },
    "stagger": {
        "description": "Stagger children entrance (container definition)",
        "css": None,
        "framer": {
            "container": {
                "initial": {},
                "animate": {"transition": {"staggerChildren": 0.07, "delayChildren": 0.1}},
                "exit": {"transition": {"staggerChildren": 0.03, "staggerDirection": -1}},
            },
            "child": {
                "initial": {"opacity": 0, "y": 20},
                "animate": {"opacity": 1, "y": 0},
                "exit": {"opacity": 0, "y": 20},
                "transition": {"duration": 0.3, "ease": "easeOut"},
            },
        },
    },
    "draw": {
        "description": "SVG stroke draw animation",
        "css": textwrap.dedent("""\
            @keyframes draw {
              from { stroke-dashoffset: var(--path-length, 1000); }
              to   { stroke-dashoffset: 0; }
            }
            .animate-draw {
              stroke-dasharray: var(--path-length, 1000);
              animation: draw var(--duration, 1.5s) var(--easing, ease-in-out) forwards;
            }"""),
        "framer": {
            "initial": {"pathLength": 0},
            "animate": {"pathLength": 1},
            "transition": {"duration": 1.5, "ease": "easeInOut"},
        },
    },
    "height_auto": {
        "description": "Animate height from 0 to auto (expand/collapse)",
        "css": textwrap.dedent("""\
            @keyframes expandHeight {
              from { max-height: 0; opacity: 0; overflow: hidden; }
              to   { max-height: var(--max-h, 500px); opacity: 1; }
            }
            @keyframes collapseHeight {
              from { max-height: var(--max-h, 500px); opacity: 1; }
              to   { max-height: 0; opacity: 0; overflow: hidden; }
            }
            .animate-expand {
              animation: expandHeight var(--duration, 300ms) var(--easing, ease-out) forwards;
              overflow: hidden;
            }
            .animate-collapse {
              animation: collapseHeight var(--duration, 250ms) var(--easing, ease-in) forwards;
              overflow: hidden;
            }"""),
        "framer": {
            "initial": {"height": 0, "opacity": 0},
            "animate": {"height": "auto", "opacity": 1},
            "exit": {"height": 0, "opacity": 0},
            "transition": {"duration": 0.3, "ease": "easeInOut"},
        },
    },
}


def parse_animation_spec(spec: str) -> list[dict]:
    """Parse natural language into matched animation patterns."""
    spec_lower = spec.lower()
    results = []

    keyword_map = {
        "fade in": "fade_in",
        "fade out": "fade_out",
        "slide up": "slide_up",
        "slide down": "slide_down",
        "slide left": "slide_left",
        "slide right": "slide_right",
        "slide from bottom": "slide_up",
        "slide from top": "slide_down",
        "scale in": "scale_in",
        "scale out": "scale_out",
        "scale up": "scale_in",
        "scale down": "scale_out",
        "spin": "rotate",
        "spinner": "rotate",
        "rotate": "rotate",
        "pulse": "pulse",
        "bounce": "bounce",
        "bounce in": "bounce",
        "blur in": "blur_in",
        "flip": "flip",
        "wiggle": "wiggle",
        "shake": "wiggle",
        "stagger": "stagger",
        "draw": "draw",
        "expand": "height_auto",
        "collapse": "height_auto",
        "accordion": "height_auto",
    }

    matched_keys = set()
    for keyword, pattern_key in keyword_map.items():
        if keyword in spec_lower:
            matched_keys.add(pattern_key)

    if not matched_keys:
        matched_keys.add("fade_in")

    for key in matched_keys:
        if key in ANIMATION_PATTERNS:
            results.append(ANIMATION_PATTERNS[key])

    return results


def format_css(patterns: list[dict], class_name: Optional[str] = None) -> str:
    """Generate CSS output from matched patterns."""
    parts = ["/* PixelSmith Animation Lab — Generated CSS */", ""]
    parts.append("@media (prefers-reduced-motion: reduce) {")
    parts.append("  *, *::before, *::after {")
    parts.append("    animation-duration: 0.01ms !important;")
    parts.append("    animation-iteration-count: 1 !important;")
    parts.append("    transition-duration: 0.01ms !important;")
    parts.append("  }")
    parts.append("}")
    parts.append("")

    for p in patterns:
        if p.get("css"):
            parts.append(f"/* {p['description']} */")
            parts.append(p["css"])
            parts.append("")

    if class_name:
        combined = ",".join(
            f".{class_name}-{key}" for key, _ in enumerate(patterns)
        )
        parts.append(f"{combined} {{")
        parts.append("  --duration: 300ms;")
        parts.append("  --easing: ease-out;")
        parts.append("}")

    return "\n".join(parts)


def format_framer(patterns: list[dict]) -> str:
    """Generate Framer Motion variants output."""
    output = {}
    for p in patterns:
        if p.get("framer"):
            output[p["description"]] = p["framer"]

    return json.dumps(output, indent=2)


def format_framer_code(patterns: list[dict]) -> str:
    """Generate ready-to-use Framer Motion React code."""
    lines = ['import { motion } from "framer-motion";', ""]

    for i, p in enumerate(patterns):
        name = p["description"].lower().replace(" ", "_").replace("/", "_")
        framer = p.get("framer", {})

        if "container" in framer:
            lines.append(f"const containerVariants = {json.dumps(framer['container'], indent=2)};")
            lines.append("")
            lines.append(f"const childVariants = {json.dumps(framer['child'], indent=2)};")
            lines.append("")
            lines.append("<motion.div")
            lines.append('  variants={containerVariants}')
            lines.append('  initial="initial"')
            lines.append('  animate="animate"')
            lines.append('  exit="exit"')
            lines.append(">")
            lines.append("  {items.map((item) => (")
            lines.append("    <motion.div key={item.id} variants={childVariants}>")
            lines.append("      {item.content}")
            lines.append("    </motion.div>")
            lines.append("  ))}")
            lines.append("</motion.div>")
        else:
            lines.append(f"// {p['description']}")
            lines.append(f"const {name}Variants = {json.dumps(framer, indent=2)};")
            lines.append("")
            lines.append("<motion.div")
            lines.append(f'  variants={{{name}Variants}}')
            lines.append('  initial="initial"')
            lines.append('  animate="animate"')
            lines.append('  exit="exit"')
            lines.append("/>")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="PixelSmith Animation Lab — generate animations from natural language"
    )
    parser.add_argument("description", type=str, help="Natural language animation description")
    parser.add_argument("--format", "-f", choices=["css", "framer", "framer-code"], default="css",
                        help="Output format (default: css)")
    parser.add_argument("--output-dir", "-o", type=str, default="./styles/animations",
                        help="Output directory")
    parser.add_argument("--list", "-l", action="store_true",
                        help="List all supported animation patterns")

    args = parser.parse_args()

    if args.list:
        print("Supported animation patterns:")
        for key, info in ANIMATION_PATTERNS.items():
            print(f"  {key:15s} — {info['description']}")
        return

    patterns = parse_animation_spec(args.description)

    if not patterns:
        print("No animation patterns matched. Try: fade in, slide up, bounce, pulse, stagger...")
        return

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.format == "css":
        content = format_css(patterns)
        ext = "css"
    elif args.format == "framer":
        content = format_framer(patterns)
        ext = "json"
    else:
        content = format_framer_code(patterns)
        ext = "tsx"

    slug = args.description.lower().replace(" ", "_")[:40]
    out_path = output_dir / f"animation_{slug}.{ext}"
    out_path.write_text(content, encoding="utf-8")

    print(f"[OK] Generated: {out_path}")
    print(f"  Patterns matched: {[p['description'] for p in patterns]}")


if __name__ == "__main__":
    main()
