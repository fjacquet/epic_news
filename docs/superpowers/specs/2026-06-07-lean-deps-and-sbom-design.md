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

Based on an import-usage audit of `src/` + `tests/`:

| Dep | Evidence | Action |
|---|---|---|
| `langsmith` (test extra) | 0 imports | **Remove** |
| `chromadb` (runtime, heavy) | 0 direct imports; provided transitively by `crewai` | **Drop direct pin** after verifying `crewai`'s resolved range still satisfies runtime |
| `lxml-html-clean` | 0 direct imports | **Verify** runtime need (`lxml.html.clean` was split out; may be required by `newspaper3k`/scraping). Keep only if needed; document why. |
| `newspaper3k` | 1 file; unmaintained since 2018, pins old `lxml` | **Flag** as chore-magnet → follow-up (replace with `trafilatura` or isolate). Not changed in this pass. |

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
- `deptry` false positives handled via its ignore config, not by disabling the check.

## Verification

- `make sbom` produces a valid CycloneDX JSON locally.
- `make security` runs `bandit` + `osv-scanner` clean against the allowlist.
- `make deps-audit` (`deptry`) exits 0 after pruning.
- A temporarily injected known-vuln dependency proves the gate **fires**; adding it to
  `.osv-scanner.toml` proves suppression **works**; both reverted before merge.
- Full suite green: `make validate` (lint + mypy + test) + `make security` + `make sbom`.

## Affected Files (anticipated)

- `pyproject.toml` — remove `langsmith`, `chromadb` (verify), `safety`; add `deptry`,
  `cyclonedx-py`; add `[tool.deptry]` config.
- `.github/dependabot.yml` — groups + caps + github-actions ecosystem.
- `.github/workflows/security.yml` — **new**.
- `Makefile` — `sbom`, `deps-audit` targets; rewrite `security`; drop `safety` branches/cleanup.
- `.osv-scanner.toml` — **new** (allowlist).
- `.gitignore` — ignore `sbom.cdx.json` (build artifact).
- `uv.lock` — regenerated.

## Open Items for Implementation Plan

- Confirm `crewai` resolved range keeps `chromadb` available before dropping the pin.
- Confirm `lxml-html-clean` runtime requirement (keep vs remove).
- Decide `cyclonedx-py` install (`dev` dep vs `uvx`) and pin policy.
- Decide release-attach lives in `security.yml` vs a new `release.yml`.
