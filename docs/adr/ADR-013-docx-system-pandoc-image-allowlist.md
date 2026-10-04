# ADR-013: DOCX Through System Pandoc With a Two-Pass Image Allowlist

## Status

Accepted (2026-10-04)

## Context

DOCX reports are assembled from Markdown fragments written by the LLM (`src/epic_news/utils/docx_report/docx_builder.py`) and converted by pandoc through `pypandoc`. Two problems had to be solved:

1. **Which pandoc.** `pypandoc-binary` bundled an x86_64 pandoc that does not run natively on Apple Silicon, and it pinned the pandoc version to the wheel. The project switched to `pypandoc` plus a system pandoc (Homebrew locally, `apt` in CI and the Docker image).
2. **Untrusted Markdown.** Fragments are LLM output, partly derived from scraped web content. An image such as `![](file:///app/.env)` or `![](http://169.254.169.254/...)` makes pandoc read a local file or call a URL and embed the result in a DOCX that is then emailed.

`pandoc --sandbox` looked like the answer but fails with distro builds: Debian bookworm (2.17) and Ubuntu (3.1) packages are not built with embedded data files, so the DOCX writer stops with `Could not find data file data/docx/[Content_Types].xml` (exit 97) under the sandbox. A Lua filter alone is not enough either: pandoc 2.x fetches DOCX media **before** running filters.

## Decision

- Use system pandoc: `pandoc` is installed by `apt` in `.github/workflows/ci.yml` and in the Dockerfile runtime stage; `pypandoc` (not `pypandoc-binary`) is the Python dependency.
- Convert in two passes:
  1. Markdown → pandoc JSON with `--lua-filter safe_images.lua`. JSON output fetches no resources. The filter keeps only images whose path is under `output/` (relative `output/...` or absolute under the resolved output root) and replaces every other image (URLs, any `scheme:` URI, `..`, other absolute paths) with its alt text. The root arrives as the `epic_image_root` metadata field, which the filter deletes so it never reaches the DOCX properties.
     The same pass also runs `strip_rules.lua` (#218), which drops every `HorizontalRule`: LLM fragments separate paragraphs with `---`, and headings already structure the report. Markdown is read as `markdown-yaml_metadata_block` so `---` stays a rule instead of breaking YAML parsing.
  2. JSON → DOCX with `--toc --standalone --reference-doc`. Pandoc only sees allowed images, so it can only fetch those.
- Do not use `--sandbox`.

## Consequences

- Works with any pandoc version (verified with Debian 2.17 and Homebrew 3.12); no extra binary to download or pin per architecture.
- Reports can include images produced by our own code (charts written under `output/`); anything the LLM points at elsewhere is dropped.
- Developers must have pandoc on `PATH`. An old virtualenv that still contains `pypandoc_binary` logs "Bad CPU type" and falls back to the system binary; fix with `uv sync --all-extras --reinstall-package pypandoc`.
- Tests cover both passes, including that the DOCX pass never receives a forbidden image (`tests/utils/holiday_report/test_docx_builder.py`).
