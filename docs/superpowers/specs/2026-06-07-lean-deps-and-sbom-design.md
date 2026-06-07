# Design: Lean Dependencies + Official, Secured SBOM

- **Date:** 2026-06-07
- **Status:** Approved (design); pending implementation plan
- **Author:** Frederic Jacquet (with Claude Code)

## Problem

Two related maintenance pains:

1. **Dependency-upgrade chore.** ~40 direct runtime deps + 13 test + 8 dev resolve to
   ~1000 locked packages. Dependabot runs `uv` weekly, **ungrouped with no PR cap**, so it
   produces a flood of individual `chore(deps)` PRs (recent history: #110–#113 all dep bumps).
2. **No SBOM, decaying security tooling.** There is no Software Bill of Materials anywhere.
   Security is `bandit` + `safety`, and `safety check` is deprecated (now requires an
   account/login), making it its own upgrade chore.

## Goals

- **Lean deps:** prune what is removable *and* tame the dependabot PR noise.
- **Official SBOM:** generate a standard, machine-readable SBOM on every build.
- **Secured SBOM:** vuln-scan it with a free, no-login tool; replace `safety`.
- **Publish:** distribute the SBOM as an official release artifact.

## Non-Goals (YAGNI)

- SBOM signing / attestation / SLSA provenance.
- SPDX format (CycloneDX only).
- Per-image OS-package SBOMs for the Docker images (possible later add-on).
- Replacing `newspaper3k` in this pass (flagged as a follow-up; it changes scraping behavior).

## Decisions (from brainstorming)

| Question | Decision |
|---|---|
| Lean scope | **Prune AND tame noise** |
| SBOM layers | **Generate + vuln-scan (drop `safety`) + publish as release artifact** (no signing) |
| SBOM format | **CycloneDX** |
| Scan gating | **Blocking + documented allowlist** (respects "no red CI" + unfixable-upstream constraint) |
| Tooling | **uv-native Python stack** (Approach A): `cyclonedx-py` + `osv-scanner` + `deptry` |

### Tooling alternatives considered

- **A. `cyclonedx-py` + `osv-scanner` + `deptry` (chosen).** Lockfile-native, lean, single
  source of truth: generate the SBOM, scan that same SBOM, publish it. Python-only coverage.
- **B. `syft` + `grype` (Anchore).** Can SBOM Docker images incl. OS packages; one vendor.
  Rejected for now: Go binaries, heavier, noisier (whole-image), and image SBOMs weren't requested.
- **C. GitHub-native (dependency graph + Dependabot alerts).** Zero tooling but produces no
  portable CycloneDX file — fails the "create it officially" goal.

## Architecture / Data Flow

```
uv.lock
  └─(cyclonedx-py uv)─▶ sbom.cdx.json  (CycloneDX JSON)
                          ├─(osv-scanner --sbom, honors .osv-scanner.toml)─▶ CI gate (blocking)
                          ├─(actions/upload-artifact)──────────────────────▶ workflow artifact (always)
                          └─(on tag v*)────────────────────────────────────▶ GitHub Release asset
```

## Components

### 1. Dependency pruning (one-time, evidence-driven)

Full audit of **all** direct deps (40 runtime + 12 test + 8 dev) via `deptry` (in-env) plus an
import-usage sweep with corrected package→module mapping across `src/`, `tests/`, `scripts/`,
and non-import usages (CLI tools, pytest plugins/fixtures, MCP/config strings).

**1a. Safe removals (this pass):**

| Dep | Group | Evidence | Action |
|---|---|---|---|
| `langsmith` | test | 0 imports anywhere | **Remove** |
| `chromadb` | runtime | 0 imports; `crewai` hard-depends `chromadb~=1.1.0`. Our `>=0.5.23` pin is redundant *and* lower than crewai's actual floor (misleading). | **Remove direct pin** (transitive-guaranteed) |
| `vulture` | dev | declared but **never invoked** (no Makefile/pre-commit/CI reference) | **Remove** (or wire up — chosen: remove) |

**1b. Imported-but-undeclared (latent breakage — only works via transitive luck):**

| Dep | Where | Action |
|---|---|---|
| `markdownify` | `src/epic_news/app.py:51` — optional import with an existing BeautifulSoup fallback | **Drop the optional branch** (fallback already covers it) → no new dep |
| `tabulate` | `scripts/optimize_crews.py:18` | **Declare in `dev` group** (script-only utility) |

**1c. Biggest lean win (follow-up — touches scraping behavior, NOT this pass):**

`newspaper3k` is unmaintained (last release 2018) and is the **only** importer of `lxml` /
`lxml-html-clean` in the tree. Replacing it with `trafilatura` (maintained, lighter) cascades:

| Dep | Evidence | Action (follow-up) |
|---|---|---|
| `newspaper3k` | 1 file; unmaintained 2018 | Replace with `trafilatura` |
| `lxml` (direct pin) | 0 direct imports; bs4 uses stdlib `html.parser` everywhere; only transitive via `newspaper3k` | Drop direct pin once `newspaper3k` is gone |
| `lxml-html-clean` | 0 imports; only required by `newspaper3k` (`lxml.html.clean` split-out) | Drop once `newspaper3k` is gone |

→ Replacing **1 unmaintained dep removes up to 3 direct deps.** Deferred because it changes
article-extraction behavior and deserves its own change + verification.

**1d. Low-priority:**

| Dep | Evidence | Action |
|---|---|---|
| `pendulum` | test | Used only in `tests/test_advanced_libraries.py`, which tests faker+pendulum *themselves*, not project code | Remove dep + that meta-test (optional) |

**1e. Keep (verified, with rationale):**

- `litellm` — intentional CVE-floor pin (`>=1.87.0`); only an *optional* extra in `crewai`
  (`litellm<1.84; extra=='litellm'`), so it must stay declared directly. Documented constraint.
- `uvicorn` — runtime ASGI server invoked via CLI (`Dockerfile.api`, `Makefile`), not imported.
- `composio` — imported directly (`from composio import Composio`); also transitive via
  `composio-crewai`. Kept for explicit-import hygiene.
- All remaining runtime/test/dev deps are actively imported or invoked.

Each removal verified by: `uv sync`, `make lint`, `make test`, `make security`, `make sbom` all green.

### 2. Dependency guardrail (ongoing)

- Add **`deptry`** to the `dev` dependency group.
- Add a `make deps-audit` target running `uv run deptry src`.
- Configure `deptry` (in `pyproject.toml`) with a small ignore-list for intentional
  transitive/optional deps (e.g. anything kept by design).
- Wire `deptry` into CI (the new `security.yml`, non-flaky step).

### 3. Tame dependabot noise

Rewrite `.github/dependabot.yml`:

- `package-ecosystem: uv`, `directory: /`, `schedule: weekly`.
- **Groups:** `dev-dependencies` (all dev/test, minor+patch), `runtime` (minor+patch); major
  bumps remain individual PRs.
- `open-pull-requests-limit: 5`.
- Add a second `package-ecosystem: github-actions` block (workflows pin action versions),
  grouped, weekly. Net effect: ~10 PRs/week → ~2–3.

### 4. SBOM generation

- Add `cyclonedx-py` to the `dev` group (or run via `uvx` — decided at plan time).
- `make sbom` → `cyclonedx-py uv --output-format JSON -o sbom.cdx.json`.
- `sbom.cdx.json` is a build artifact: git-ignored locally, produced fresh in CI.

> **API note:** exact `cyclonedx-py` and `osv-scanner` CLI flags are validated against current
> docs (via context7 / official docs) during implementation before code is written.

### 5. Vuln scanning (replaces `safety`)

- Add `.osv-scanner.toml` with documented `[[IgnoredVulns]]` entries (id + `reason` + review
  date), seeded with the known unfixable `litellm`/`pydantic`/`crewai` chain if it surfaces a CVE.
- Rewrite `make security`: `bandit -r src` + `osv-scanner --sbom sbom.cdx.json`.
- **Remove `safety`:** dev dependency, Makefile branches, and `safety-report.json` cleanup.

### 6. CI workflow

New `.github/workflows/security.yml`:

- **Triggers:** `pull_request` (→ main), `push` (→ main), `schedule` (weekly — catches
  newly-disclosed CVEs with no code change), `workflow_dispatch`.
- **Steps:** checkout → setup uv → `make sbom` → `make deps-audit` → `osv-scanner` (blocking,
  honors allowlist) → `actions/upload-artifact` `sbom.cdx.json` (always, even on failure).
- **Permissions:** `contents: read` (least privilege).

### 7. Official publication

- On git tag `v*`: a job (in `security.yml` or a dedicated `release.yml`) attaches
  `sbom.cdx.json` to the GitHub Release for that tag.
- Leaves a documented hook to also attach SBOMs in the existing `docker-publish-*.yml`
  workflows if per-image SBOMs are wanted later.

## Error Handling / Edge Cases

- Vuln gate fails CI **only** on findings absent from `.osv-scanner.toml`. Allowlisted items
  carry a human reason and a review date.
- Honors the project's "no red CI" rule and the existing unfixable-upstream constraint by
  making suppression explicit and auditable rather than silently non-blocking.
- SBOM artifact is uploaded even when the scan step fails, so findings are inspectable.
- `deptry` false positives handled via its ignore config (e.g. DEP003 for the editable
  `epic_news` self-package; DEP002 for CLI-only dev tools and `litellm`/`uvicorn` intentional
  non-imported runtime deps), not by disabling the check.

## Verification

- `make sbom` produces a valid CycloneDX JSON locally.
- `make security` runs `bandit` + `osv-scanner` clean against the allowlist.
- `make deps-audit` (`deptry`) exits 0 after pruning.
- A temporarily injected known-vuln dependency proves the gate **fires**; adding it to
  `.osv-scanner.toml` proves suppression **works**; both reverted before merge.
- Full suite green: `make validate` (lint + mypy + test) + `make security` + `make sbom`.

## Affected Files (anticipated)

- `pyproject.toml` — remove `langsmith`, `chromadb`, `safety`, `vulture` (and optionally
  `pendulum`); add `deptry`, `cyclonedx-py`, `tabulate` (dev); add `[tool.deptry]` config.
- `src/epic_news/app.py` — drop the optional `markdownify` import branch (keep bs4 fallback).
- `tests/test_advanced_libraries.py` — remove if `pendulum` is dropped (it tests libs, not us).
- `.github/dependabot.yml` — groups + caps + github-actions ecosystem.
- `.github/workflows/security.yml` — **new**.
- `Makefile` — `sbom`, `deps-audit` targets; rewrite `security`; drop `safety` branches/cleanup.
- `.osv-scanner.toml` — **new** (allowlist).
- `.gitignore` — ignore `sbom.cdx.json` (build artifact).
- `uv.lock` — regenerated.
- **Follow-up change (separate):** `newspaper3k` → `trafilatura`, then drop `lxml` +
  `lxml-html-clean`.

## Open Items for Implementation Plan

- Confirm nothing breaks after dropping the `chromadb` direct pin (transitive via `crewai`).
- Confirm `markdownify`-branch removal leaves `app.py` markdown handling correct (fallback path).
- Decide whether to drop `pendulum` + its meta-test in this pass or defer.
- Decide `cyclonedx-py` install (`dev` dep vs `uvx`) and pin policy.
- Decide release-attach lives in `security.yml` vs a new `release.yml`.
- Follow-up: scope the `newspaper3k`→`trafilatura` migration (extraction-quality parity check).
