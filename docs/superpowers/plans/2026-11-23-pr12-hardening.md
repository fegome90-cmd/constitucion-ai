# PR #12 Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans, superpowers:test-driven-development and superpowers:verification-before-completion. Review gates follow pstack:pr-review; apply pstack:principle-sequence-verifiable-units.

**Goal:** Close six live review threads on PR #12 and make it safe to merge, without altering constitutional authority or unrelated user files.

**Architecture:** Preserve the existing CLI/scanner/fixer architecture; patch the behavioral boundaries of fixing and committing, with regression tests on real temporary files and git repos. Treat tests and manifest as clean-checkout evidence. Do not expand scope to an agent-policy engine.

**Tech Stack:** Python 3.12+, pytest, uv, Git, GitHub Actions, Bash.

**Spec:** PR #12 threads, Constitution v1.1 Laws I, IV, V, VI, VII, VIII; prior review of this conversation.

## Global Constraints

- Work solely in isolated worktree fix/pr12-review-20261123, based on origin/feat/integrate-starters at 13df642.
- Do not touch local untracked files under the original checkout or change policy authorities.
- No force-push. Do not merge with unresolved threads, absent executable checks, or unverified approval requirements.
- Per commit, test then inspect git diff. Do not infer test success from archived readiness reports.
- Keep fixes narrow: no new external dependencies.

## Review Focus

- Nested vendor directory with multiple files is renamed once at the matching path component.
- Scan-detected content is replaced only at reported line/column; fenced snippets remain unchanged.
- Executable permissions survive content edits; failure/backup paths preserve originals.
- A named file path works with plan/fix and global output flags work after subcommands.
- With staged user changes, --commit contains only fixer-changed paths and preserves other staged work.

---

### Task 1: Baseline and manifested integrity

**Files:** Modify: `MANIFEST.current.sha256`; Test: `tests/test_config_kits.py`.

**Interfaces:** Manifest checks only versioned repository paths; hashes of updated tracked files are regenerated at end.

- [ ] Confirm baseline `uv run --frozen pytest tests/ -q` fails on manifest referencing untracked `scripts/constitution_linter/AGENTS.md`.
- [ ] Change manifest generator/integrity test to require tracked paths or reconcile manifest to tracked paths and regenerate deterministically.
- [ ] Run focused manifest test to PASS; preserve integrity checks.

### Task 2: CLI and fixer file-path correctness

**Files:** Modify `scripts/constitution_linter/fixer.py`, `cli.py`; Test `tests/test_constitution_linter.py`.

**Interfaces:** `ConstitutionFixer(base_path: Path)`; `main(argv)`; base_path may be file or directory.

- [ ] Add tests for file argument to `plan` and `fix --dry-run`, and for `scan --ci --format json`.
- [ ] Run tests to observe RED.
- [ ] Correct fixer base directory / lazy backup creation and CLI flag placement.
- [ ] Run tests to GREEN, run full existing linter suite; record proof.

### Task 3: Fixer precision and filesystem semantics

**Files:** Modify `scripts/constitution_linter/fixer.py`; Test `tests/test_constitution_linter.py`.

**Interfaces:** `ConstitutionFixer.apply_plan`, `_apply_path_fix`, `_apply_content_fix`; `FixResult.files_modified` reflects changed paths.

- [ ] Add regression tests for nested `.claude/` renaming with two children; content in and outside fenced block; executable mode preserved; mixed path/content violation.
- [ ] Run RED.
- [ ] Replace only positions observed by scanner, choose non-overlapping matches, process content before path renames, de-duplicate directory rename targets; preserve modes on atomic swap.
- [ ] Run GREEN and full linter tests; inspect diff.

### Task 4: Scoped git commits

**Files:** Modify `scripts/constitution_linter/cli.py`; Test `tests/test_constitution_linter.py`.

**Interfaces:** `_run_commit_step(path, plan, files_modified)` accepts exact paths, no `git add -A` and no unrelated staged content in commit.

- [ ] Add isolated Git integration test with unrelated pre-staged file.
- [ ] Run RED. Implement scoped `git commit --only -- <paths>` and guard empty/invalid change.
- [ ] Run GREEN/full suite. Check no dirty user files lost.

### Task 5: Release gates and reconciliation

**Files:** Modify `README.md`, `docs/mandate-roles-and-jurisdiction.md`, `.reviewctl/project-gates.json`; Create `.github/workflows/ci.yml`; refresh `MANIFEST.current.sha256`.

**Interfaces:** CI runs offline-deterministic pytest, Ruff, mypy as supported, plus manifest check. No live registry validation forced inside CI.

- [ ] Inspect baseline on `uv run --frozen ruff check`, `uv run --frozen mypy scripts`, `uv run --frozen pytest tests`.
- [ ] Update docs that incorrectly say repo is Markdown-only and stale links; ensure old authority text is unchanged.
- [ ] Add CI workflow and correct reviewctl statics for Python repo.
- [ ] Run verification and regenerate manifest from tracked versioned files; check `git diff --check`.
- [ ] Commit scoped changes in logical groups, push fast-forward to PR #12 only after gates pass, reply in threads with evidence, resolve threads when verified.
- [ ] Recheck PR head, CI, review status and requirements; merge only if every gate is validated and user authorization covers merging.

## Execution ledger

Use `.superpowers/sdd/pr12-20261123/progress.md` for decisions and per-task command receipts; avoid exposing unrelated local directories.
