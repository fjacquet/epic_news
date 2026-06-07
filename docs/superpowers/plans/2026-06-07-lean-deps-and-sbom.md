# Lean Dependencies + Official, Secured SBOM — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prune removable dependencies, tame the Dependabot PR flood, and produce an official CycloneDX SBOM that is vuln-scanned (replacing deprecated `safety`) and published as a release artifact.

**Architecture:** Pure tooling/config change — no application logic changes except removing one dead optional-import branch and declaring four currently-undeclared direct imports. SBOM is generated from `uv.lock` via `uv export` → `cyclonedx-py requirements` (run through `uvx`, no added lockfile weight). `osv-scanner` scans the generated SBOM with a documented allowlist. A new `security.yml` workflow runs the scan on PR/push/weekly-schedule and attaches the SBOM to GitHub Releases on tags. `deptry` is added as an ongoing dependency-hygiene guardrail.

**Tech Stack:** `uv`, `cyclonedx-bom` 7.3.0 (via `uvx`), `osv-scanner` v2.3.8, `deptry`, GitHub Actions (`actions/checkout@v6`, `astral-sh/setup-uv@v8.1.0`, `actions/upload-artifact@v4`), `gh` CLI.

**Spec:** `docs/superpowers/specs/2026-06-07-lean-deps-and-sbom-design.md`

**Validated facts (do not re-derive):**
- `cyclonedx-bom` 7.3.0 has **no** `uv` subcommand. Use `requirements` subcommand. Flags: `--output-format JSON|XML`, `--spec-version`/`--sv`, `--output-file`/`-o`. Proven to emit CycloneDX 1.6 with 236 runtime components.
- `osv-scanner` scans an SBOM via `osv-scanner scan source -L <file>` (SBOM auto-detected by the `.cdx.json` suffix). Config file is `osv-scanner.toml` (no leading dot), `[[IgnoredVulns]]` entries take `id`, `reason`, optional `ignoreUntil = YYYY-MM-DD`. Exits non-zero on un-ignored findings.
- osv-scanner v2.3.8 linux asset: `https://github.com/google/osv-scanner/releases/download/v2.3.8/osv-scanner_linux_amd64`.
- Working branch is `chore/lean-deps-sbom` (already created).

---

## File Structure

| File | Responsibility | Action |
|---|---|---|
| `pyproject.toml` | Dependency declarations + `[tool.deptry]` config | Modify |
| `src/epic_news/app.py` | Streamlit app; `html_to_markdown` helper | Modify (drop dead branch) |
| `tests/test_advanced_libraries.py` | Library smoke tests | Modify (drop pendulum test) |
| `Makefile` | Dev/CI command targets | Modify (`sbom`, `deps-audit`, rewrite `security`, `.PHONY`, clean) |
| `osv-scanner.toml` | Vuln allowlist (documented ignores) | Create |
| `.github/dependabot.yml` | Update grouping/caps | Replace |
| `.github/workflows/security.yml` | SBOM + scan + release-attach CI | Create |
| `.gitignore` | Ignore generated SBOM artifacts | Modify |

---

## Task 1: Prune safe-removal dependencies

Removes `chromadb` (redundant runtime pin — `crewai` hard-depends `chromadb~=1.1.0`), `langsmith` + `pendulum` (test, unused/meta-test only), and `vulture` (dev tool never invoked).

**Files:**
- Modify: `pyproject.toml` (dependencies, optional-dependencies.test, dependency-groups.dev)
- Modify: `tests/test_advanced_libraries.py`

- [ ] **Step 1: Remove `chromadb` from runtime dependencies**

In `pyproject.toml`, delete this line from `[project] dependencies`:

```toml
    "chromadb>=0.5.23",
```

- [ ] **Step 2: Remove `langsmith` and `pendulum` from the test extra**

In `pyproject.toml` `[project.optional-dependencies] test`, delete these two lines:

```toml
    "pendulum>=3.1.0",
    "langsmith",
```

- [ ] **Step 3: Remove `vulture` from the dev group**

In `pyproject.toml` `[dependency-groups] dev`, delete this line:

```toml
    "vulture>=2.14",
```

- [ ] **Step 4: Drop the pendulum meta-test**

Replace the entire contents of `tests/test_advanced_libraries.py` with (removes `pendulum` + `faker` imports and the `test_faker_and_pendulum` function — `faker` remains used in other test files; keeps the `pytest-mock` test):

```python
def test_mocking_with_pytest_mock(mocker):
    """
    This test demonstrates the use of pytest-mock.
    """
    # Create a mock object
    mock_object = mocker.Mock()

    # Configure the mock to return a specific value when a method is called
    mock_object.get_name.return_value = "Test Name"

    # Call the method on the mock object
    result = mock_object.get_name()

    # Assert that the method was called and returned the expected value
    mock_object.get_name.assert_called_once()
    assert result == "Test Name"
```

- [ ] **Step 5: Re-lock and sync**

Run: `uv lock && uv sync --all-extras`
Expected: resolves successfully; `uv.lock` updated; no errors. `chromadb` remains in the lock (now pulled transitively by `crewai`); `langsmith`, `pendulum`, `vulture` removed from the resolved dev/test set.

- [ ] **Step 6: Verify chromadb still present transitively (regression guard)**

Run: `uv run python -c "import chromadb; print('chromadb', chromadb.__version__)"`
Expected: prints a `chromadb 1.x` version (proves dropping the direct pin did not remove it).

- [ ] **Step 7: Run the test suite**

Run: `uv run pytest -q`
Expected: PASS (no collection error for the removed `test_faker_and_pendulum`; `faker`-using tests elsewhere still pass).

- [ ] **Step 8: Commit**

```bash
git add pyproject.toml uv.lock tests/test_advanced_libraries.py
git commit -m "chore(deps): prune chromadb pin, langsmith, pendulum, vulture

chromadb is a hard transitive dep of crewai (~=1.1.0); our >=0.5.23 pin
was redundant and misleading. langsmith unused; pendulum only in a
library meta-test; vulture never invoked in Makefile/pre-commit/CI.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 2: Fix undeclared-but-imported dependencies

Removes the dead `markdownify` optional branch (a BeautifulSoup fallback already exists) and declares `tabulate`, `urllib3`, and `python-dateutil` — currently imported directly but only present transitively (latent breakage). Declaring `urllib3`/`python-dateutil` adds **no** new resolved packages.

**Files:**
- Modify: `src/epic_news/app.py:43-63`
- Modify: `pyproject.toml`
- Test: `tests/test_html_to_markdown.py` (Create)

- [ ] **Step 1: Write a failing test for `html_to_markdown`**

Create `tests/test_html_to_markdown.py`:

```python
from epic_news.app import html_to_markdown


def test_html_to_markdown_extracts_text():
    html = "<h1>Title</h1><p>Hello <b>world</b></p>"
    result = html_to_markdown(html)
    assert "Title" in result
    assert "Hello" in result
    assert "world" in result
    assert "<" not in result  # tags stripped


def test_html_to_markdown_handles_garbage_gracefully():
    # Non-HTML input must not raise.
    assert isinstance(html_to_markdown(""), str)
```

- [ ] **Step 2: Run the test to verify current behavior**

Run: `uv run pytest tests/test_html_to_markdown.py -v`
Expected: PASS today (the function already works via the markdownify branch or bs4 fallback). This test pins the behavior we must preserve after removing the branch.

- [ ] **Step 3: Remove the `markdownify` branch in `app.py`**

In `src/epic_news/app.py`, replace the `html_to_markdown` function (currently lines ~43-63) with:

```python
def html_to_markdown(html: str) -> str:
    """Best-effort HTML→Markdown conversion for displaying/downloading.

    Uses BeautifulSoup text extraction; returns original HTML on failure.
    """
    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "html.parser")
        # Keep basic structure using newlines
        text = soup.get_text("\n")
        return text.strip()
    except Exception:
        return html
```

- [ ] **Step 4: Run the test to verify behavior preserved**

Run: `uv run pytest tests/test_html_to_markdown.py -v`
Expected: PASS (text extraction still works via bs4).

- [ ] **Step 5: Declare `tabulate` in the dev group**

In `pyproject.toml` `[dependency-groups] dev`, add (alphabetical-ish, after `safety`/before `yamllint` is fine):

```toml
    "tabulate>=0.9.0",
```

- [ ] **Step 6: Declare `urllib3` and `python-dateutil` in runtime dependencies**

In `pyproject.toml` `[project] dependencies`, under the `# --- HTTP / Web ---` section add:

```toml
    "urllib3>=2.0.0",
```

and under `# --- Data sources / scraping ---` add:

```toml
    "python-dateutil>=2.9.0",
```

- [ ] **Step 7: Re-lock and sync**

Run: `uv lock && uv sync --all-extras`
Expected: resolves with no version changes to the transitive tree (these were already present); `urllib3` / `python-dateutil` / `tabulate` now appear as direct.

- [ ] **Step 8: Run lint + the focused test**

Run: `uv run ruff check src/epic_news/app.py && uv run pytest tests/test_html_to_markdown.py -q`
Expected: lint clean, tests PASS.

- [ ] **Step 9: Commit**

```bash
git add pyproject.toml uv.lock src/epic_news/app.py tests/test_html_to_markdown.py
git commit -m "chore(deps): declare urllib3/dateutil/tabulate, drop dead markdownify branch

urllib3 (tools/*_base.py) and python-dateutil (unified_rss_tool.py) were
imported directly but only present transitively. tabulate is used by
scripts/optimize_crews.py. markdownify branch removed (bs4 fallback covers it).

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 3: Add `deptry` dependency-hygiene guardrail

**Files:**
- Modify: `pyproject.toml` (dev group + `[tool.deptry]`)
- Modify: `Makefile` (`deps-audit` target + `.PHONY`)

- [ ] **Step 1: Add `deptry` to the dev group**

In `pyproject.toml` `[dependency-groups] dev`, add:

```toml
    "deptry>=0.20.0",
```

- [ ] **Step 2: Add the `[tool.deptry]` config**

Append to `pyproject.toml` (after the `[tool.bandit]` block). This ignore-set was validated to produce a **clean exit** against the post-prune codebase:

```toml
[tool.deptry]
known_first_party = ["epic_news"]
# Treat the `test` optional-dependency group as dev so test-only libs are not
# flagged as unused in the runtime source.
pep621_dev_dependency_groups = ["test"]

[tool.deptry.per_rule_ignores]
# DEP002: declared but not imported in our source — intentional.
DEP002 = [
    "litellm",          # LLM backend used by crewai at runtime; CVE-floor pin, not imported
    "uvicorn",          # ASGI server invoked via CLI (Dockerfile.api, Makefile)
    "lxml",             # required transitively by newspaper3k at runtime
    "lxml-html-clean",  # required by newspaper3k (lxml.html.clean split-out)
    "wikipedia-mcp-server",  # launched via MCP config command string, not imported
    # pytest plugins / CLI tools (used via fixtures or config, never imported)
    "pytest-cov", "pytest-asyncio", "pytest-env", "pytest-mock",
    "pytest-regressions", "pytest-datadir", "coverage",
]
# DEP003: editable self-install shows up as transitive — it is first-party.
DEP003 = ["epic_news"]
```

- [ ] **Step 3: Add the `deps-audit` Makefile target**

In `Makefile`, add this target (place it just before the `security:` target around line 112):

```makefile
deps-audit: ## Audit dependencies for unused/missing/transitive issues (deptry)
	@echo "$(GREEN)Auditing dependencies with deptry...$(RESET)"
	uv run deptry .
```

- [ ] **Step 4: Register `deps-audit` in `.PHONY`**

In `Makefile`, change the `.PHONY` line (currently line 6):

```makefile
        pre-commit security type-check \
```

to:

```makefile
        pre-commit security type-check deps-audit sbom \
```

(`sbom` is added now to avoid a second edit in Task 4.)

- [ ] **Step 5: Sync and run the audit**

Run: `uv sync --all-extras && make deps-audit`
Expected: deptry runs and exits **0** ("Success! No dependency issues found"). If any DEP00x line appears, it is a real new issue — fix the import or add a justified ignore; do not suppress blindly.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml uv.lock Makefile
git commit -m "chore(deps): add deptry guardrail + make deps-audit target

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 4: SBOM generation (`make sbom`)

**Files:**
- Modify: `Makefile` (`sbom` target)
- Modify: `.gitignore`

- [ ] **Step 1: Add the `sbom` Makefile target**

In `Makefile`, add this target immediately after the `deps-audit` target from Task 3 (the validated, working command sequence):

```makefile
sbom: ## Generate a CycloneDX SBOM (sbom.cdx.json) from the uv lockfile
	@echo "$(GREEN)Generating CycloneDX SBOM from uv.lock...$(RESET)"
	uv export --no-dev --no-emit-project --no-hashes \
		--format requirements.txt -o sbom-requirements.txt
	uvx --from cyclonedx-bom cyclonedx-py requirements sbom-requirements.txt \
		--output-format JSON --spec-version 1.6 --output-file sbom.cdx.json
	@rm -f sbom-requirements.txt
	@echo "$(GREEN)✓ sbom.cdx.json generated$(RESET)"
```

- [ ] **Step 2: Ignore generated SBOM artifacts**

Append to `.gitignore`:

```gitignore
# Generated SBOM artifacts (produced fresh in CI / on demand)
sbom.cdx.json
sbom-requirements.txt
```

- [ ] **Step 3: Generate and validate the SBOM**

Run: `make sbom`
Expected: prints "✓ sbom.cdx.json generated"; `sbom.cdx.json` exists.

- [ ] **Step 4: Verify it is valid CycloneDX**

Run:
```bash
uv run python -c "import json; d=json.load(open('sbom.cdx.json')); assert d['bomFormat']=='CycloneDX'; assert d['specVersion']=='1.6'; print('components:', len(d['components']))"
```
Expected: prints `components: <N>` with N > 200; no assertion error.

- [ ] **Step 5: Confirm the artifact is git-ignored**

Run: `git status --porcelain sbom.cdx.json`
Expected: empty output (file ignored, not tracked).

- [ ] **Step 6: Commit**

```bash
git add Makefile .gitignore
git commit -m "feat(security): add make sbom (CycloneDX from uv.lock)

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 5: Replace `safety` with `osv-scanner` vuln scanning

**Files:**
- Modify: `pyproject.toml` (remove `safety`)
- Create: `osv-scanner.toml`
- Modify: `Makefile` (rewrite `security`, update `clean-test`)

- [ ] **Step 1: Remove `safety` from the dev group**

In `pyproject.toml` `[dependency-groups] dev`, delete this line:

```toml
    "safety>=3.8.1",
```

- [ ] **Step 2: Create the allowlist `osv-scanner.toml`**

Create `osv-scanner.toml` at the repo root:

```toml
# OSV-Scanner vulnerability allowlist.
# Each entry MUST carry a reason and SHOULD carry an ignoreUntil review date.
# Format: https://google.github.io/osv-scanner/configuration/
#
# Seed entry (commented) for the known unfixable upstream chain documented in
# pyproject.toml (crewai 1.14.x <-> pydantic <-> litellm). Uncomment and set the
# real OSV id + expiry if/when osv-scanner reports it and no fix is available.
#
# [[IgnoredVulns]]
# id = "GHSA-xxxx-xxxx-xxxx"
# ignoreUntil = 2026-09-01
# reason = "Transitive via crewai 1.14.x pydantic/litellm pin; no compatible fix upstream yet."
```

- [ ] **Step 3: Rewrite the `security` Makefile target**

In `Makefile`, replace the entire `security:` target (currently lines ~112-127) with:

```makefile
security: sbom ## Run security checks (bandit + osv-scanner against the SBOM)
	@echo "$(GREEN)Checking for security issues in code...$(RESET)"
	@if uv run python -c "import bandit" 2>/dev/null; then \
		uv run bandit -r $(SRC_DIR) -f json -o bandit-report.json || true; \
		uv run bandit -r $(SRC_DIR); \
	else \
		echo "$(YELLOW)⚠ bandit not installed. Install with: uv add --dev bandit$(RESET)"; \
	fi
	@echo ""
	@echo "$(GREEN)Scanning SBOM for known vulnerabilities (osv-scanner)...$(RESET)"
	@if command -v osv-scanner >/dev/null 2>&1; then \
		osv-scanner scan source -L sbom.cdx.json --config=osv-scanner.toml; \
	else \
		echo "$(YELLOW)⚠ osv-scanner not installed. Install: brew install osv-scanner$(RESET)"; \
		echo "$(YELLOW)  (CI installs the pinned binary automatically.)$(RESET)"; \
	fi
```

- [ ] **Step 4: Drop the `safety-report.json` cleanup line**

In `Makefile` `clean-test` target (around line 209-210), delete this line:

```makefile
	rm -f safety-report.json
```

- [ ] **Step 5: Sync (removes safety)**

Run: `uv lock && uv sync --all-extras`
Expected: `safety` no longer in the resolved dev set.

- [ ] **Step 6: Run security locally**

Run: `make security`
Expected: SBOM regenerates; `bandit` runs and reports; the osv-scanner step either runs clean (exit 0) if installed, or prints the install hint. If `osv-scanner` IS installed locally and reports an un-ignored vuln, that is a real finding — record it in `osv-scanner.toml` with a reason or fix the dependency.

- [ ] **Step 7: Commit**

```bash
git add pyproject.toml uv.lock Makefile osv-scanner.toml
git commit -m "feat(security): replace deprecated safety with osv-scanner SBOM scan

bandit + osv-scanner against the CycloneDX SBOM, gated by a documented
osv-scanner.toml allowlist. Removes safety (now login-gated/deprecated).

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 6: Tame the Dependabot PR flood

**Files:**
- Modify: `.github/dependabot.yml`

- [ ] **Step 1: Replace `.github/dependabot.yml`**

Replace the entire file with (groups all minor+patch Python bumps into one weekly PR, caps open PRs, and adds a grouped github-actions ecosystem; major bumps stay individual so they get attention):

```yaml
---
# Dependabot: grouped, capped updates to minimise upgrade-chore noise.
# https://docs.github.com/code-security/dependabot/dependabot-version-updates/configuration-options-for-the-dependabot.yml-file
version: 2
updates:
  - package-ecosystem: "uv"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
    groups:
      python-minor-patch:
        update-types:
          - "minor"
          - "patch"

  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
    groups:
      github-actions-all:
        patterns:
          - "*"
```

- [ ] **Step 2: Validate YAML**

Run: `uv run yamllint .github/dependabot.yml`
Expected: no errors (the repo's yamllint config disables line-length; `---` start and final newline are present).

- [ ] **Step 3: Commit**

```bash
git add .github/dependabot.yml
git commit -m "ci(deps): group + cap dependabot updates; add github-actions ecosystem

Collapses the weekly per-package chore(deps) flood into grouped
minor/patch PRs (majors stay individual). Adds grouped action updates.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 7: CI security workflow (`security.yml`)

Runs SBOM generation, `deptry`, and `osv-scanner` on PR/push/weekly-schedule; uploads the SBOM as an artifact always; attaches it to the GitHub Release on tag pushes.

**Files:**
- Create: `.github/workflows/security.yml`

- [ ] **Step 1: Create `.github/workflows/security.yml`**

```yaml
---
name: Security & SBOM

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]
    tags: ["v*"]
  schedule:
    - cron: "0 6 * * 1"  # Mondays 06:00 UTC — catch newly-disclosed CVEs
  workflow_dispatch:

permissions:
  contents: read

jobs:
  sbom-and-scan:
    name: SBOM + vulnerability scan
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v6

      - name: Install uv
        uses: astral-sh/setup-uv@v8.1.0
        with:
          enable-cache: true

      - name: Set up Python
        run: uv python install 3.13

      - name: Sync dependencies (locked)
        run: uv sync --all-extras --locked

      - name: Generate CycloneDX SBOM
        run: make sbom

      - name: Dependency hygiene audit (deptry)
        run: make deps-audit

      - name: Install osv-scanner (pinned)
        run: |
          curl -sSL \
            https://github.com/google/osv-scanner/releases/download/v2.3.8/osv-scanner_linux_amd64 \
            -o osv-scanner
          chmod +x osv-scanner
          ./osv-scanner --version

      - name: Vulnerability scan (blocking, honors allowlist)
        run: ./osv-scanner scan source -L sbom.cdx.json --config=osv-scanner.toml

      - name: Upload SBOM artifact
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: sbom-cyclonedx
          path: sbom.cdx.json
          if-no-files-found: error

  publish-sbom:
    name: Attach SBOM to GitHub Release
    needs: sbom-and-scan
    if: startsWith(github.ref, 'refs/tags/v')
    runs-on: ubuntu-latest
    permissions:
      contents: write
    steps:
      - name: Checkout repository
        uses: actions/checkout@v6

      - name: Install uv
        uses: astral-sh/setup-uv@v8.1.0
        with:
          enable-cache: true

      - name: Set up Python
        run: uv python install 3.13

      - name: Generate CycloneDX SBOM
        run: make sbom

      - name: Upload SBOM to the release
        env:
          GH_TOKEN: ${{ github.token }}
        run: |
          gh release view "${GITHUB_REF_NAME}" >/dev/null 2>&1 \
            || gh release create "${GITHUB_REF_NAME}" --generate-notes
          gh release upload "${GITHUB_REF_NAME}" sbom.cdx.json --clobber
```

- [ ] **Step 2: Validate workflow YAML**

Run: `uv run yamllint .github/workflows/security.yml`
Expected: no errors.

- [ ] **Step 3: (Optional) Static-check with actionlint if available**

Run: `command -v actionlint >/dev/null && actionlint .github/workflows/security.yml || echo "actionlint not installed — skipping"`
Expected: no errors, or the skip message.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/security.yml
git commit -m "ci(security): add SBOM + osv-scanner workflow, attach SBOM to releases

PR/push/weekly scan of the CycloneDX SBOM (blocking, allowlist-gated),
deptry hygiene audit, SBOM uploaded as artifact always and attached to
GitHub Releases on v* tags.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Task 8: Full validation + push

**Files:** none (verification only)

- [ ] **Step 1: Full local validation**

Run: `make validate`
Expected: lint + mypy + tests all pass (matches CI's gate).

- [ ] **Step 2: Security + SBOM end-to-end**

Run: `make security`
Expected: SBOM regenerates, bandit clean, osv-scanner runs clean (or prints install hint locally).

- [ ] **Step 3: Dependency audit clean**

Run: `make deps-audit`
Expected: deptry exits 0.

- [ ] **Step 4: Confirm no stray tracked artifacts**

Run: `git status --porcelain`
Expected: clean (no `sbom.cdx.json` / `sbom-requirements.txt` / `bandit-report.json` tracked).

- [ ] **Step 5: Push the branch and open a PR**

```bash
git push -u origin chore/lean-deps-sbom
gh pr create --title "Lean dependencies + official secured SBOM" \
  --body "Implements docs/superpowers/specs/2026-06-07-lean-deps-and-sbom-design.md.

- Prune: chromadb pin, langsmith, pendulum, vulture
- Declare undeclared imports: urllib3, python-dateutil, tabulate; drop dead markdownify branch
- deptry guardrail (make deps-audit)
- CycloneDX SBOM (make sbom) from uv.lock
- Replace deprecated safety with osv-scanner (allowlist-gated, blocking)
- Dependabot grouping + caps + github-actions ecosystem
- security.yml: scan on PR/push/weekly, attach SBOM to releases"
```

- [ ] **Step 6: Verify CI is green**

After the PR opens, confirm both the existing `CI` workflow and the new `Security & SBOM` workflow pass. Per project rule, no red checks may merge — fix any failure in this PR. Also check CodeRabbitAI comments before merge.

---

## Self-Review

**Spec coverage:**
- Lean/prune (spec §1a–1e) → Tasks 1, 2 (+ deptry §2 → Task 3). Follow-up `newspaper3k`→`trafilatura` is explicitly out of scope per spec; not planned here. ✓
- Tame dependabot noise (spec §3) → Task 6. ✓
- SBOM generation, CycloneDX (spec §4) → Task 4. ✓
- Vuln scan, drop safety, allowlist (spec §5) → Task 5. ✓
- CI workflow (spec §6) → Task 7. ✓
- Official publication / release artifact (spec §7) → Task 7 `publish-sbom` job. ✓
- No signing/SPDX/image-SBOM (spec non-goals) → correctly absent. ✓

**Placeholder scan:** No TBD/TODO; every code/config block is complete; all commands have expected output. The seed `[[IgnoredVulns]]` in `osv-scanner.toml` is intentionally commented (no active CVE to ignore yet) — documented as such, not a placeholder.

**Type/name consistency:** `make sbom` produces `sbom.cdx.json`; Tasks 5 & 7 scan exactly that filename via `-L sbom.cdx.json`. `osv-scanner.toml` (no dot) is consistent across the config file, `make security`, and `security.yml`. `deps-audit`/`sbom` both registered in `.PHONY` (Task 3 Step 4). osv-scanner version `v2.3.8` consistent between Makefile hint and CI download.
