"""
PixelSmith — Token Extractor
Reverse-engineers design tokens from existing CSS/Tailwind/JSX codebases.
"""

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Optional


COLOR_HEX_RE = re.compile(r'#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\b')
COLOR_RGB_RE = re.compile(r'rgb\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\)')
COLOR_HSL_RE = re.compile(r'hsl\(\s*\d+\s*,\s*\d+%?\s*,\s*\d+%?\s*\)')
SPACING_RE = re.compile(r'(?:margin|padding|gap|inset|top|right|bottom|left)\s*:\s*(\d+(?:\.\d+)?(?:px|rem|em|%))', re.IGNORECASE)
BORDER_RADIUS_RE = re.compile(r'border-radius\s*:\s*(\d+(?:\.\d+)?(?:px|rem|%))', re.IGNORECASE)
FONT_SIZE_RE = re.compile(r'font-size\s*:\s*(\d+(?:\.\d+)?(?:px|rem|em))', re.IGNORECASE)
LINE_HEIGHT_RE = re.compile(r'line-height\s*:\s*(\d+(?:\.\d+)?(?:px|rem|%))', re.IGNORECASE)
SHADOW_RE = re.compile(r'(?:box-shadow|text-shadow)\s*:\s*([^;{]+)', re.IGNORECASE)
FONT_FAMILY_RE = re.compile(r'font-family\s*:\s*([^;{]+)', re.IGNORECASE)
BREAKPOINT_RE = re.compile(r'@media\s*\(?\s*(?:min|max)-width\s*:\s*(\d+(?:\.\d+)?(?:px|rem|em))', re.IGNORECASE)

TAILWIND_COLORS = {
    "slate", "gray", "zinc", "neutral", "stone", "red", "orange", "amber",
    "yellow", "lime", "green", "emerald", "teal", "cyan", "sky", "blue",
    "indigo", "violet", "purple", "fuchsia", "pink", "rose",
}

TAILWIND_SCALE = [50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 950]

TAILWIND_SPACING = {0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 16, 20, 24, 28, 32, 36, 40, 44, 48, 52, 56, 60, 64, 72, 80, 96}


def extract_colors(text: str) -> list[str]:
    colors = COLOR_HEX_RE.findall(text)
    colors.extend(COLOR_RGB_RE.findall(text))
    colors.extend(COLOR_HSL_RE.findall(text))
    return colors


def normalize_value(value: str) -> float:
    if value.endswith("px"):
        return float(value.replace("px", ""))
    if value.endswith("rem"):
        return float(value.replace("rem", "")) * 16
    if value.endswith("em"):
        return float(value.replace("em", "")) * 16
    if value.endswith("%"):
        return float(value.replace("%", ""))
    return float(value)


def round_to_nearest(n: float, step: float = 2) -> float:
    return round(n / step) * step


def suggest_tailwind_spacing(values: list[float]) -> dict:
    closest = {}
    for v in values:
        v_rounded = round_to_nearest(v, 1)
        best = min(TAILWIND_SPACING, key=lambda x: abs(x - v_rounded / 4))
        closest[f"{v}px"] = best
    return closest


def extract_tailwind_classes(text: str) -> dict:
    classes = re.findall(r'className=["\']([^"\']+)["\']', text)
    result = defaultdict(set)

    for cls_str in classes:
        for cls in cls_str.split():
            for color in TAILWIND_COLORS:
                match = re.match(rf'({color})-(\d{{2,3}})', cls)
                if match:
                    result["colors"].add(f"{match.group(1)}-{match.group(2)}")
                    break

            match = re.match(r'^([mpg])[tblrxy]?-(\d+(?:\.\d+)?)$', cls)
            if match:
                result["spacing"].add(f"{match.group(1)}-{match.group(2)}")

            match = re.match(r'^text-(xs|sm|base|lg|xl|2xl|3xl|4xl|5xl|6xl|7xl|8xl|9xl)$', cls)
            if match:
                result["font_sizes"].add(match.group(0))

            match = re.match(r'^rounded(-(none|sm|md|lg|xl|2xl|3xl|full))?$', cls)
            if match:
                result["radii"].add(match.group(0))

            match = re.match(r'^shadow(-(sm|md|lg|xl|2xl|inner|none))?$', cls)
            if match:
                result["shadows"].add(match.group(0))

    return {k: sorted(v) for k, v in result.items()}


def scan_directory(path: Path) -> dict:
    """Scan a directory for CSS/styling tokens."""
    tokens = {
        "colors": Counter(),
        "spacing": Counter(),
        "font_sizes": Counter(),
        "line_heights": Counter(),
        "radii": Counter(),
        "shadows": Counter(),
        "font_families": Counter(),
        "breakpoints": Counter(),
        "tailwind": defaultdict(Counter),
        "files_scanned": 0,
    }

    ext_whitelist = {".css", ".scss", ".less", ".tsx", ".jsx", ".js", ".ts", ".html"}

    for filepath in path.rglob("*"):
        if filepath.suffix not in ext_whitelist:
            continue
        if any(part.startswith(".") for part in filepath.parts):
            continue
        if filepath.name.startswith("."):
            continue

        try:
            text = filepath.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        tokens["files_scanned"] += 1

        for c in extract_colors(text):
            tokens["colors"][c] += 1

        for m in SPACING_RE.finditer(text):
            tokens["spacing"][m.group(1)] += 1

        for m in FONT_SIZE_RE.finditer(text):
            tokens["font_sizes"][m.group(1)] += 1

        for m in LINE_HEIGHT_RE.finditer(text):
            tokens["line_heights"][m.group(1)] += 1

        for m in BORDER_RADIUS_RE.finditer(text):
            tokens["radii"][m.group(1)] += 1

        for m in SHADOW_RE.finditer(text):
            tokens["shadows"][m.group(1).strip()] += 1

        for m in FONT_FAMILY_RE.finditer(text):
            tokens["font_families"][m.group(1).strip()] += 1

        for m in BREAKPOINT_RE.finditer(text):
            tokens["breakpoints"][m.group(1)] += 1

        tailwind_data = extract_tailwind_classes(text)
        for category, items in tailwind_data.items():
            for item in items:
                tokens["tailwind"][category][item] += 1

    return tokens


def format_css_vars(tokens: dict) -> str:
    """Format tokens as CSS custom properties."""
    lines = [":root {", ""]

    if tokens["colors"]:
        lines.append("  /* Colors */")
        for color, count in tokens["colors"].most_common(30):
            safe_name = f"color-{color.lower().strip('#')}"
            safe_name = re.sub(r'[^a-z0-9-]', '-', safe_name)
            lines.append(f"  --{safe_name}: {color};")
        lines.append("")

    if tokens["spacing"]:
        lines.append("  /* Spacing */")
        for spacing, count in tokens["spacing"].most_common(20):
            safe = spacing.replace("px", "").replace("rem", "").replace("em", "").replace(".", "-")
            lines.append(f"  --space-{safe}: {spacing};")
        lines.append("")

    if tokens["font_sizes"]:
        lines.append("  /* Font Sizes */")
        for fs, count in tokens["font_sizes"].most_common(10):
            safe = fs.replace("px", "").replace("rem", "").replace(".", "-")
            lines.append(f"  --font-size-{safe}: {fs};")
        lines.append("")

    if tokens["radii"]:
        lines.append("  /* Border Radius */")
        for r, count in tokens["radii"].most_common(10):
            safe = r.replace("px", "").replace("rem", "").replace("%", "pct").replace(".", "-")
            lines.append(f"  --radius-{safe}: {r};")
        lines.append("")

    if tokens["shadows"]:
        lines.append("  /* Shadows */")
        for i, (shadow, count) in enumerate(tokens["shadows"].most_common(5)):
            lines.append(f"  --shadow-{i + 1}: {shadow};")
        lines.append("")

    if tokens["breakpoints"]:
        lines.append("  /* Breakpoints */")
        for bp, count in tokens["breakpoints"].most_common(10):
            safe = bp.replace("px", "").replace("rem", "").replace(".", "-")
            lines.append(f"  --bp-{safe}: {bp};")
        lines.append("")

    lines.append("}")
    return "\n".join(lines)


def format_tailwind_config(tokens: dict) -> str:
    """Format tokens as Tailwind CSS v4 @theme block."""
    lines = ["@theme {", ""]

    if tokens["colors"]:
        lines.append("  /* Colors */")
        for color, count in tokens["colors"].most_common(30):
            safe_name = color.lower().strip("#")
            safe_name = re.sub(r'[^a-z0-9-]', '-', safe_name)
            lines.append(f"  --color-{safe_name}: {color};")
        lines.append("")

    if tokens["spacing"]:
        lines.append("  /* Spacing */")
        for spacing, count in tokens["spacing"].most_common(20):
            safe = spacing.replace("px", "").replace("rem", "").replace(".", "-")
            lines.append(f"  --spacing-{safe}: {spacing};")
        lines.append("")

    if tokens["font_sizes"]:
        lines.append("  /* Font Sizes */")
        for fs, count in tokens["font_sizes"].most_common(10):
            safe = fs.replace("px", "").replace("rem", "").replace(".", "-")
            lines.append(f"  --font-size-{safe}: {fs};")
        lines.append("")

    lines.append("}")
    return "\n".join(lines)


def format_json(tokens: dict) -> str:
    """Format tokens as structured JSON."""
    output = {
        "meta": {"files_scanned": tokens["files_scanned"]},
        "colors": dict(tokens["colors"].most_common(50)),
        "spacing": dict(tokens["spacing"].most_common(30)),
        "font_sizes": dict(tokens["font_sizes"].most_common(15)),
        "line_heights": dict(tokens["line_heights"].most_common(10)),
        "border_radii": dict(tokens["radii"].most_common(10)),
        "shadows": dict(tokens["shadows"].most_common(10)),
        "font_families": dict(tokens["font_families"].most_common(10)),
        "breakpoints": dict(tokens["breakpoints"].most_common(10)),
    }
    if tokens["tailwind"]:
        output["tailwind"] = {
            k: dict(v.most_common(30))
            for k, v in tokens["tailwind"].items()
        }
    return json.dumps(output, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="PixelSmith Token Extractor — extract design tokens from codebases"
    )
    parser.add_argument("--input", "-i", type=str, required=True,
                        help="Directory to scan for style tokens")
    parser.add_argument("--format", "-f", choices=["css", "tailwind", "json"], default="css",
                        help="Output format (default: css)")
    parser.add_argument("--output", "-o", type=str, default=None,
                        help="Output file path (default: stdout)")

    args = parser.parse_args()
    input_path = Path(args.input)

    if not input_path.exists():
        print(f"Error: {input_path} does not exist.")
        return
    if not input_path.is_dir():
        print(f"Error: {input_path} is not a directory.")
        return

    print(f"Scanning {input_path}...")
    tokens = scan_directory(input_path)

    if tokens["files_scanned"] == 0:
        print("No style files found. Supported: .css .scss .tsx .jsx .ts .js .html")
        return

    print(f"Scanned {tokens['files_scanned']} files.")
    print(f"  Colors:         {len(tokens['colors'])} unique")
    print(f"  Spacing values: {len(tokens['spacing'])} unique")
    print(f"  Font sizes:     {len(tokens['font_sizes'])} unique")
    print(f"  Radii:          {len(tokens['radii'])} unique")
    print(f"  Shadows:        {len(tokens['shadows'])} unique")
    print(f"  Breakpoints:    {len(tokens['breakpoints'])} unique")

    if args.format == "css":
        output = format_css_vars(tokens)
    elif args.format == "tailwind":
        output = format_tailwind_config(tokens)
    else:
        output = format_json(tokens)

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output, encoding="utf-8")
        print(f"\nWrote: {out_path}")
    else:
        print("\n" + "-" * 40)
        print(output)


if __name__ == "__main__":
    main()
