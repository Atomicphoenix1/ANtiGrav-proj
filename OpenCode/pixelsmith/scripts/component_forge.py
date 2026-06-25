"""
PixelSmith — Component Forge
Generates production-ready React/TypeScript components from natural language specs.
"""

import argparse
import json
import os
import re
import textwrap
from pathlib import Path
from typing import Optional

COMPONENT_TEMPLATES = {
    "button": {
        "name": "Button",
        "description": "Versatile button with variants, sizes, icon support, loading state",
        "variants": ["primary", "secondary", "outline", "ghost", "danger", "link"],
        "sizes": ["sm", "md", "lg", "xl"],
    },
    "card": {
        "name": "Card",
        "description": "Container card with image, header, body, and footer slots",
        "variants": ["default", "bordered", "elevated"],
        "sizes": ["md"],
    },
    "modal": {
        "name": "Modal",
        "description": "Portal-based dialog with focus trap, backdrop, and keyboard dismiss",
        "variants": ["default"],
        "sizes": ["md"],
    },
    "input": {
        "name": "Input",
        "description": "Form input with label, error, helper text, and icon slots",
        "variants": ["default", "floating"],
        "sizes": ["md"],
    },
    "select": {
        "name": "Select",
        "description": "Dropdown select with search, keyboard navigation, and async options",
        "variants": ["default"],
        "sizes": ["md"],
    },
    "toast": {
        "name": "Toast",
        "description": "Toast notification with variants, auto-dismiss, and stack management",
        "variants": ["success", "error", "warning", "info"],
        "sizes": ["md"],
    },
    "badge": {
        "name": "Badge",
        "description": "Inline badge / pill for status, counts, and labels",
    },
    "tabs": {
        "name": "Tabs",
        "description": "Tab navigation with underline style, keyboard arrows, and panels",
    },
    "accordion": {
        "name": "Accordion",
        "description": "Collapsible sections with animated expand/collapse",
    },
    "switch": {
        "name": "Switch",
        "description": "Toggle switch with label, disabled state, and dark mode",
    },
}


def parse_spec(spec: str) -> dict:
    """Parse a natural language component description into structured data."""
    spec_lower = spec.lower()
    result = {
        "uses_card": False,
        "uses_modal": False,
        "uses_form": False,
        "has_icon": False,
        "has_loading": False,
        "has_dark_mode": True,
        "has_animation": True,
        "variants": [],
        "sizes": [],
    }

    for keyword in ["icon", "svg", "leading icon", "trailing icon", "left icon", "right icon"]:
        if keyword in spec_lower:
            result["has_icon"] = True
            break

    if any(w in spec_lower for w in ["loading", "spinner", "pending", "submitting"]):
        result["has_loading"] = True

    if any(w in spec_lower for w in ["no dark", "light only", "light-mode"]):
        result["has_dark_mode"] = False

    if any(w in spec_lower for w in ["no animation", "static", "no motion"]):
        result["has_animation"] = False

    variant_keywords = {
        "primary": "primary", "secondary": "secondary", "outline": "outline",
        "ghost": "ghost", "danger": "danger", "error": "danger", "success": "success",
        "warning": "warning", "info": "info", "link": "link",
    }
    for word, variant in variant_keywords.items():
        if word in spec_lower:
            result["variants"].append(variant)

    size_keywords = {"sm": "sm", "small": "sm", "md": "md", "medium": "md",
                     "lg": "lg", "large": "lg", "xl": "xl", "extra large": "xl"}
    for word, size in size_keywords.items():
        if word in spec_lower:
            if size not in result["sizes"]:
                result["sizes"].append(size)

    if "card" in spec_lower or "tile" in spec_lower:
        result["uses_card"] = True
    if any(w in spec_lower for w in ["modal", "dialog", "popup", "overlay"]):
        result["uses_modal"] = True
    if any(w in spec_lower for w in ["form", "input", "field", "textfield"]):
        result["uses_form"] = True

    for name, info in COMPONENT_TEMPLATES.items():
        if name in spec_lower:
            result["component_type"] = name
            result["component_name"] = info["name"]
            result["component_desc"] = info["description"]
            if not result["variants"] and "variants" in info:
                result["variants"] = info["variants"]
            if not result["sizes"] and "sizes" in info:
                result["sizes"] = info["sizes"]
            break
    else:
        result["component_type"] = "custom"
        result["component_name"] = guess_component_name(spec)
        result["component_desc"] = spec.strip()

    return result


def guess_component_name(spec: str) -> str:
    words = spec.strip().split()
    filtered = [w for w in words if w.lower() not in
                {"a", "an", "the", "with", "for", "and", "or", "in", "on", "of", "to"}]
    if not filtered:
        return "Component"
    name = " ".join(filtered[:3])
    name = re.sub(r'[^a-zA-Z0-9 ]', '', name)
    return name.title().replace(" ", "")


SNIPPET_LIBRARY = {
    "loading_spinner": textwrap.dedent("""\
    {isLoading && (
      <svg
        className="animate-spin -ml-1 mr-2 h-4 w-4"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
    )}
    """),
    "icon_placeholder": textwrap.dedent("""\
    {icon && (
      <span className={clsx("-ml-0.5 mr-1.5", iconClasses)} aria-hidden="true">
        {icon}
      </span>
    )}
    """)
}


VARIANT_STYLES = {
    "primary": "bg-blue-600 text-white hover:bg-blue-700 focus-visible:ring-blue-500 active:bg-blue-800",
    "secondary": "bg-gray-100 text-gray-900 hover:bg-gray-200 focus-visible:ring-gray-400 active:bg-gray-300 dark:bg-gray-700 dark:text-gray-100 dark:hover:bg-gray-600",
    "outline": "border border-gray-300 bg-transparent text-gray-700 hover:bg-gray-50 focus-visible:ring-gray-400 active:bg-gray-100 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800",
    "ghost": "bg-transparent text-gray-700 hover:bg-gray-100 focus-visible:ring-gray-400 active:bg-gray-200 dark:text-gray-300 dark:hover:bg-gray-800",
    "danger": "bg-red-600 text-white hover:bg-red-700 focus-visible:ring-red-500 active:bg-red-800",
    "success": "bg-green-600 text-white hover:bg-green-700 focus-visible:ring-green-500 active:bg-green-800",
    "warning": "bg-amber-500 text-white hover:bg-amber-600 focus-visible:ring-amber-400 active:bg-amber-700",
    "info": "bg-sky-600 text-white hover:bg-sky-700 focus-visible:ring-sky-500 active:bg-sky-800",
    "link": "bg-transparent text-blue-600 underline-offset-2 hover:underline focus-visible:ring-blue-500 dark:text-blue-400",
}

SIZE_STYLES = {
    "sm": "px-2.5 py-1.5 text-xs gap-1 rounded",
    "md": "px-4 py-2 text-sm gap-1.5 rounded-md",
    "lg": "px-5 py-2.5 text-base gap-2 rounded-lg",
    "xl": "px-6 py-3 text-lg gap-2 rounded-xl",
}


def generate_component(spec: dict) -> str:
    """Generate the full component source code."""
    name = spec.get("component_name", "Component")
    desc = spec.get("component_desc", "")
    variants = spec.get("variants", [])
    sizes = spec.get("sizes", [])
    has_icon = spec.get("has_icon", False)
    has_loading = spec.get("has_loading", False)
    has_animation = spec.get("has_animation", True)
    has_dark_mode = spec.get("has_dark_mode", True)
    uses_card = spec.get("uses_card", False)
    uses_modal = spec.get("uses_modal", False)
    uses_form = spec.get("uses_form", False)

    default_variant = variants[0] if variants else "primary"
    default_size = sizes[0] if sizes else "md"

    props_interface = f"""interface {name}Props extends React.ButtonHTMLAttributes<HTMLButtonElement> {{
  variant?: '{default_variant}'"""
    if len(variants) > 1:
        props_interface = props_interface.replace(
            f"'{default_variant}'",
            " | ".join(f"'{v}'" for v in variants)
        )

    props_interface += f"""
  size?: '{default_size}'"""
    if len(sizes) > 1:
        props_interface = props_interface.replace(
            f"'{default_size}'",
            " | ".join(f"'{s}'" for s in sizes)
        )

    if has_icon:
        props_interface += """
  icon?: React.ReactNode
  iconPosition?: 'left' | 'right'"""
    if has_loading:
        props_interface += """
  isLoading?: boolean"""
    props_interface += """
  className?: string
}"""

    variant_map_items = "\n".join(
        f"      '{v}': '{VARIANT_STYLES.get(v, VARIANT_STYLES['primary'])}',"
        for v in variants
    ) if variants else f"      '{default_variant}': '{VARIANT_STYLES[default_variant]}',"

    size_map_items = "\n".join(
        f"      '{s}': '{SIZE_STYLES.get(s, SIZE_STYLES['md'])}',"
        for s in sizes
    ) if sizes else f"      '{default_size}': '{SIZE_STYLES[default_size]}',"

    icon_block = ""
    if has_icon:
        icon_block = f"""
  const {name.lower()}_icon = iconPosition === 'right' ? (
    <span className="order-1 ml-1.5" aria-hidden="true">{{icon}}</span>
  ) : (
    <span className="-ml-0.5 mr-1.5" aria-hidden="true">{{icon}}</span>
  );"""

    loading_block = ""
    if has_loading:
        loading_block = f"""
  if (isLoading) {{
    return (
      <button
        disabled
        className={{clsx(baseStyles, variantStyles, sizeStyles, 'opacity-60 cursor-not-allowed', className)}}
        aria-busy="true"
        {{...rest}}
      >
        <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" aria-hidden="true">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        <span>{{children}}</span>
      </button>
    );
  }}"""

    animation_import = ""
    motion_wrapper_start = ""
    motion_wrapper_end = ""
    if has_animation:
        animation_import = 'import { motion } from "framer-motion";'
        motion_wrapper_start = textwrap.dedent(f"""\
  const Motion{name} = motion.button;

  const animationProps = {{
    whileHover: {{ scale: 1.02 }},
    whileTap: {{ scale: 0.98 }},
    transition: {{ type: "spring", stiffness: 400, damping: 17 }},
  }};""")
        motion_wrapper_end = "      {{...animationProps}}"

    motion_tag_open = "MotionButton" if has_animation else "button"
    motion_tag_close = "MotionButton" if has_animation else "button"

    source = f"""import React, {{ forwardRef }} from "react";
import clsx from "clsx";
{animation_import}

{props_interface}

const variantStyles: Record<string, string> = {{
{variant_map_items}
}};

const sizeStyles: Record<string, string> = {{
{size_map_items}
}};

const {name} = forwardRef<HTMLButtonElement, {name}Props>(
  (
    {{
      variant = "{default_variant}",
      size = "{default_size}",
      className,
      children,
      disabled,
      {"icon," if has_icon else ""}
      {"iconPosition = 'left'," if has_icon else ""}
      {"isLoading = false," if has_loading else ""}
      ...rest
    }},
    ref
  ) => {{
    const baseStyles =
      "inline-flex items-center justify-center font-medium transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none select-none";
    const vStyles = variantStyles[variant] || variantStyles["{default_variant}"];
    const sStyles = sizeStyles[size] || sizeStyles["{default_size}"];
    {"const {name.lower()}_icon = icon && (iconPosition === 'right' ? <span className='order-1 ml-1.5' aria-hidden='true'>{icon}</span> : <span className='-ml-0.5 mr-1.5' aria-hidden='true'>{icon}</span>);" if has_icon else ""}
    {"if (isLoading) return ( <button disabled className={clsx(baseStyles, vStyles, sStyles, 'opacity-60 cursor-not-allowed', className)} aria-busy='true' {...rest}> <svg className='animate-spin h-4 w-4' xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' aria-hidden='true'> <circle className='opacity-25' cx='12' cy='12' r='10' stroke='currentColor' strokeWidth='4' /> <path className='opacity-75' fill='currentColor' d='M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z' /> </svg> <span>{children}</span> </button> );" if has_loading else ""}

    return (
      <{motion_tag_open}
        ref={{ref}}
        className={{clsx(baseStyles, vStyles, sStyles, className)}}
        disabled={{disabled || isLoading}}
        aria-disabled={{disabled || isLoading || undefined}}
        {{...rest}}
        {{motion_wrapper_end}}
      >
        {has_icon and "icon && iconPosition === 'left' && {name.lower()}_icon"}
        {{children}}
        {has_icon and "icon && iconPosition === 'right' && {name.lower()}_icon"}
      </{motion_tag_close}>
    );
  }}
);

{name}.displayName = "{name}";

export default {name};
export type {{ {name}Props }};
"""

    return source


def generate_story(spec: dict) -> str:
    """Generate a Storybook story file for the component."""
    name = spec.get("component_name", "Component")
    variants = spec.get("variants", ["primary"])
    sizes = spec.get("sizes", ["md"])
    has_loading = spec.get("has_loading", False)

    variant_args = "\n".join(
        f"    {{ variant: '{v}', children: '{v.title()}' }},"
        for v in variants
    )
    size_args = "\n".join(
        f"    {{ size: '{s}', children: 'Size {s.upper()}' }},"
        for s in sizes
    )
    loading_story = f"""
export const Loading: Story = {{
  args: {{
    children: "Loading...",
    isLoading: true,
    variant: "primary",
  }},
}};
""" if has_loading else ""

    return f"""import type {{ Meta, StoryObj }} from "@storybook/react";
import {name} from "./{name}";

const meta: Meta<typeof {name}> = {{
  title: "UI/{name}",
  component: {name},
  tags: ["autodocs"],
  argTypes: {{
    variant: {{
      control: "select",
      options: [{', '.join(f"'{v}'" for v in variants)}],
    }},
    size: {{
      control: "select",
      options: [{', '.join(f"'{s}'" for s in sizes)}],
    }},
    disabled: {{ control: "boolean" }},
    {"isLoading: { control: 'boolean' }," if has_loading else ""}
  }},
}};

export default meta;
type Story = StoryObj<typeof {name}>;

export const Default: Story = {{
  args: {{
    children: "{name}",
    variant: "{variants[0] if variants else 'primary'}",
    size: "{sizes[0] if sizes else 'md'}",
  }},
}};

export const Variants: Story = {{
  render: () => (
    <div className="flex flex-wrap gap-4">
{variant_args}
    </div>
  ),
}};

export const Sizes: Story = {{
  render: () => (
    <div className="flex flex-wrap items-end gap-4">
{size_args}
    </div>
  ),
}};

export const Disabled: Story = {{
  args: {{
    children: "Disabled",
    disabled: true,
    variant: "primary",
  }},
}};
{loading_story}
"""


def main():
    parser = argparse.ArgumentParser(
        description="PixelSmith Component Forge — generate React components from natural language"
    )
    parser.add_argument("description", type=str, help="Natural language component description")
    parser.add_argument("--output-dir", "-o", type=str, default="./components/ui",
                        help="Output directory (default: ./components/ui)")
    parser.add_argument("--list", "-l", action="store_true",
                        help="List all supported component types")

    args = parser.parse_args()

    if args.list:
        print("Supported component types:")
        for name, info in COMPONENT_TEMPLATES.items():
            print(f"  {name:12s} — {info['description']}")
        print("\nYou can also describe custom components in plain English.")
        return

    spec = parse_spec(args.description)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    component = generate_component(spec)
    component_path = output_dir / f"{spec['component_name']}.tsx"
    component_path.write_text(component, encoding="utf-8")
    print(f"[OK] Generated: {component_path}")

    story = generate_story(spec)
    story_path = output_dir / f"{spec['component_name']}.stories.ts"
    story_path.write_text(story, encoding="utf-8")
    print(f"[OK] Generated: {story_path}")

    print(f"\nComponent: {spec['component_name']}")
    print(f"  Variants: {spec['variants'] or 'default'}")
    print(f"  Sizes:    {spec['sizes'] or 'default'}")
    print(f"  Icon:     {'yes' if spec['has_icon'] else 'no'}")
    print(f"  Loading:  {'yes' if spec['has_loading'] else 'no'}")
    print(f"  Dark:     {'yes' if spec['has_dark_mode'] else 'no'}")
    print(f"  Motion:   {'yes' if spec['has_animation'] else 'no'}")


if __name__ == "__main__":
    main()
