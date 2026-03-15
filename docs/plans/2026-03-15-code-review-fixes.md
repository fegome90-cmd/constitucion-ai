# Constitution Linter Code Review Fixes Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Date:** 2026-03-15
**Status:** READY FOR EXECUTION
**Based On:** Multi-agent code review (4 agents: General, Test Coverage, Error Handling, Simplification)

---

## Priority Classification

| Priority | Count | Description |
|----------|-------|-------------|
| P0 (Critical) | 2 | Must fix - security/data loss risk |
| P1 (Important) | 5 | Should fix - quality/maintainability |
| P2 (Suggestion) | 3 | Nice to have - nitpicks |

---

## P0: Critical Issues (Must Fix)

### Task 1: Add Skipped File Tracking to ScanResult

**Problem:** Files with encoding/permission errors are silently skipped without user awareness.

**File:** `scripts/constitution_linter/types.py`
**Lines:** 85-102

**Steps:**

1. Add `skipped_files: tuple[str, ...]` field to `ScanResult` dataclass
2. Add `skip_reasons: dict[str, str]` field for context

**Verification:**

```bash
uv run mypy scripts/constitution_linter/types.py
```

---

### Task 2: Track Skipped Files in Scanner

**Problem:** Scanner catches exceptions but doesn't track which files were skipped.

**File:** `scripts/constitution_linter/scanner.py`
**Lines:** 185-196, 236-238

**Steps:**

1. Add `skipped: list[tuple[str, str]]` accumulator in `_scan_directory`
2. Append to skipped list on UnicodeDecodeError, PermissionError, OSError
3. Pass skipped files to ScanResult constructor
4. Change DEBUG logs to WARNING for skipped files

**Verification:**

```bash
uv run pytest tests/test_constitution_linter.py -v
```

---

## P1: Important Issues (Should Fix)

### Task 3: Fix Broad Exception Catch in Fixer

**Problem:** `apply_plan` catches broad `Exception` which could hide critical errors.

**File:** `scripts/constitution_linter/fixer.py`
**Lines:** 312-318

**Steps:**

1. Replace `except Exception` with specific exceptions (IOError, OSError, PermissionError)
2. Add comment explaining why broad catch was narrowed
3. Include exception type in error message

**Verification:**

```bash
uv run mypy scripts/constitution_linter/fixer.py
```

---

### Task 4: Add Suggestion Field Validation

**Problem:** Empty suggestions would delete matched content during fixes.

**File:** `scripts/constitution_linter/patterns.py`
**Lines:** 218-240

**Steps:**

1. In `_parse_pattern()`, add validation for non-empty suggestion
2. Raise ConfigError if suggestion is empty or whitespace-only

**Verification:**

```bash
uv run pytest tests/test_constitution_linter.py::TestYAMLLoading -v
```

---

### Task 5: Add Security Tests

**Problem:** Zero test coverage for security features (path traversal, ReDoS, atomic writes).

**File:** `tests/test_constitution_linter.py`

**Steps:**

1. Add `test_path_traversal_blocked` test
2. Add `test_redos_pattern_rejected` test (already exists, verify it works)
3. Add `test_symlink_escape_blocked` test

**Verification:**

```bash
uv run pytest tests/test_constitution_linter.py::TestFixer::test_path_security_validation -v
```

---

### Task 6: Standardize Logging Levels

**Problem:** Inconsistent logging levels make configuration difficult.

**File:** `scripts/constitution_linter/scanner.py`
**Lines:** 190, 193, 196, 238

**Steps:**

1. Change DEBUG to WARNING for files that cannot be scanned
2. Add docstring explaining logging policy

**Verification:**

```bash
uv run ruff check scripts/constitution_linter/scanner.py
```

---

### Task 7: Add Error Context to PathSecurityError

**Problem:** Error message doesn't include resolved path for debugging.

**File:** `scripts/constitution_linter/fixer.py`
**Lines:** 88-90

**Steps:**

1. Include resolved path in error message
2. Make error message more actionable

**Verification:**

```bash
uv run pytest tests/test_constitution_linter.py::TestFixer -v
```

---

## P2: Suggestions (Nice to Have)

### Task 8: Centralize Duplicated Constants

**Problem:** `MAX_FILE_SIZE_BYTES` and `MAX_CONTEXT_LENGTH` duplicated across files.

**Files:**

- `scripts/constitution_linter/scanner.py` (lines 72, 75)
- `scripts/constitution_linter/fixer.py` (line 44)
- `scripts/constitution_linter/cli.py` (line 49)

**Steps:**

1. Add constants to `types.py` with `__all__` export
2. Import from types in other modules
3. Remove local definitions

**Verification:**

```bash
uv run ruff check scripts/constitution_linter/
```

---

### Task 9: Remove Unused YAML Config or Integrate It

**Problem:** `constitution_patterns.yaml` is dead code - never loaded.

**File:** `config/constitution_patterns.yaml`

**Decision Required:** Either:

- **Option A:** Remove the file (Python is source of truth)
- **Option B:** Integrate with `--config` CLI flag

**Steps (Option A - Recommended):**

1. Remove `config/constitution_patterns.yaml`
2. Update README to reflect Python is source of truth
3. Keep `load_patterns_from_yaml` for future extensibility

**Verification:**

```bash
uv run pytest tests/ -v
```

---

### Task 10: Add CLI Integration Tests

**Problem:** Zero test coverage for CLI functionality.

**File:** `tests/test_constitution_linter.py`

**Steps:**

1. Add `TestCLI` class
2. Add `test_scan_exit_code_violations_found` test
3. Add `test_scan_exit_code_clean` test

**Verification:**

```bash
uv run pytest tests/test_constitution_linter.py::TestCLI -v
```

---

## Execution Order

1. **Task 1** → **Task 2** (Types must exist before Scanner can use them)
2. **Task 3** → **Task 7** (Both in fixer.py, do together)
3. **Task 4** (Independent)
4. **Task 5** (Independent)
5. **Task 6** (Independent)
6. **Task 8** (Independent)
7. **Task 9** (Requires user decision)
8. **Task 10** (Independent)

---

## Final Verification

After all tasks complete:

```bash
uv run pytest tests/ -v
uv run mypy scripts/
uv run ruff check scripts/
uv run constitution-linter scan . --ci
```

---

## Notes

- Tests are currently passing (44/44)
- Focus on P0 and P1 issues
- P2 suggestions can be deferred
- User decision needed for Task 9 (YAML config)
