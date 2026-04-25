"""Federated UI theme configuration.

Single source of truth for CSS variables used in HTML reports.
The template_manager injects these values at render time via generate_theme_css().
"""

# Light mode CSS variable values
_LIGHT = {
    "bg-color": "#ffffff",
    "text-color": "#343a40",
    "container-bg": "#ffffff",
    "border-color": "#dee2e6",
    "heading-color": "#0056b3",
    "h2-color": "#2980b9",
    "h3-color": "#2c3e50",
    "highlight-bg": "#f8f9fa",
    "highlight-border": "#dee2e6",
    "shadow-color": "rgba(0, 0, 0, 0.1)",
    "accent-color": "#007bff",
    "subheader-color": "#6b7280",
    "text-muted": "#6c757d",
    "link-color": "#007bff",
}

# Dark mode CSS variable values
_DARK = {
    "bg-color": "#1a1a1a",
    "text-color": "#e0e0e0",
    "container-bg": "#2d2d2d",
    "border-color": "#444",
    "heading-color": "#64b5f6",
    "h2-color": "#90caf9",
    "h3-color": "#bbdefb",
    "highlight-bg": "#333",
    "highlight-border": "#444",
    "shadow-color": "rgba(0, 0, 0, 0.3)",
    "accent-color": "#64b5f6",
    "subheader-color": "#9ca3af",
    "text-muted": "#9ca3af",
    "link-color": "#64b5f6",
}

# Typography and layout (not theme-dependent)
FONT_FAMILY = (
    '"Arial Nova Light", "Arial Nova", '
    '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, '
    'Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol"'
)
FONT_SIZE_SCREEN = "1rem"
FONT_SIZE_PRINT = "9pt"
LINE_HEIGHT_PRINT = "1.35"
BORDER_RADIUS = "8px"
CONTAINER_MAX_WIDTH = "1200px"

# Flat dict for programmatic access by renderers
UI_THEME = {**{f"light_{k}": v for k, v in _LIGHT.items()}, **{f"dark_{k}": v for k, v in _DARK.items()}}


def generate_theme_css() -> str:
    """Generate the CSS :root, dark theme, and print-media blocks from theme config."""
    light_vars = "\n".join(f"      --{k}: {v};" for k, v in _LIGHT.items())
    dark_vars = "\n".join(f"      --{k}: {v};" for k, v in _DARK.items())
    return f"""    /* Theme Variables — generated from ui_theme.py */
    :root {{
{light_vars}
      --font-family-base: {FONT_FAMILY};
      --font-size-base: {FONT_SIZE_SCREEN};
    }}

    [data-theme="dark"] {{
{dark_vars}
    }}

    /* Print compaction — Arial Nova Light @ {FONT_SIZE_PRINT} as base, headings scale via rem */
    @media print {{
      html {{ font-size: {FONT_SIZE_PRINT}; }}
      body {{
        font-family: var(--font-family-base);
        line-height: {LINE_HEIGHT_PRINT};
        background: #fff !important;
        color: #000 !important;
        padding: 0 !important;
      }}
      .container {{
        max-width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
        box-shadow: none !important;
      }}
      .theme-toggle {{ display: none !important; }}
      a {{ color: inherit !important; text-decoration: none !important; }}
      h1, h2, h3, h4, h5, h6 {{ page-break-after: avoid; }}
      table, figure, .section, .news-item, .article-summary, .feed-digest {{
        page-break-inside: avoid;
      }}
    }}"""
