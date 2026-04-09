# PRD: Federated HTML Theme

## Problem

CSS theme variables were hardcoded in `universal_report_template.html`. Changing colors or typography required editing HTML directly, with no programmatic control for crews generating HTML via Python renderers.

## Solution

Single source of truth in `src/epic_news/config/ui_theme.py`:

- `_LIGHT` dict: light mode CSS variable values
- `_DARK` dict: dark mode CSS variable values
- `generate_theme_css()`: generates `:root` and `[data-theme="dark"]` CSS blocks
- `UI_THEME` flat dict: for programmatic access by renderers

The template uses a `{{ theme_css_vars }}` placeholder. `TemplateManager.render_report()` injects the generated CSS at render time.

## Benefits

- Change theme colors in one Python file, all reports update automatically
- Renderers can access theme values programmatically via `UI_THEME`
- No manual sync between Python config and HTML template
- Dark mode support preserved
