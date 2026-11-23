"""
Constitution Linter Scanner.

Scans files and directories for model neutrality violations.
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Final

from .patterns import compile_pattern, get_default_patterns, get_violation_type
from .types import (
    MAX_CONTEXT_LENGTH,
    MAX_FILE_SIZE_BYTES,
    FileResult,
    MatchScope,
    Pattern,
    ScanResult,
    Severity,
    Violation,
    ViolationType,
)

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)

# =============================================================================
# EXCLUSIONS
# =============================================================================

# Files that should be excluded from scanning (intentional aliases)
EXCLUDED_FILES: Final[set[str]] = {
    "ALIAS-DECLARATION.md",  # Documents intentional aliases
}

# Directories to skip entirely
SKIP_DIRS: Final[set[str]] = {
    ".git",
    ".backups",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
}

# File extensions to skip (binary files)
SKIP_EXTENSIONS: Final[set[str]] = {
    ".pyc",
    ".pyo",
    ".so",
    ".dylib",
    ".dll",
    ".exe",
    ".bin",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".pdf",
    ".zip",
    ".tar.gz",
    ".sqlite",
    ".db",
    ".wav",
    ".mp3",
}

# =============================================================================
# HELPER FUNCTIONS (SMELL-004)
# =============================================================================


def _count_by_severity(violations: tuple[Violation, ...]) -> tuple[int, int, int]:
    """
    Count violations by severity level.

    SMELL-004: Extracted duplicated counting logic.

    Returns:
        Tuple of (critical_count, warning_count, info_count)
    """
    critical = sum(1 for v in violations if v.severity == Severity.CRITICAL)
    warning = sum(1 for v in violations if v.severity == Severity.WARNING)
    info = sum(1 for v in violations if v.severity == Severity.INFO)
    return critical, warning, info


# =============================================================================
# SCANNER CLASS
# =============================================================================


class ConstitutionScanner:
    """Scanner for detecting model neutrality violations."""

    def __init__(
        self,
        patterns: list[Pattern] | None = None,
        exclude_files: set[str] | None = None,
    ) -> None:
        """
        Initialize scanner with patterns.

        Args:
            patterns: List of patterns to scan for (default: all patterns)
            exclude_files: Additional files to exclude
        """
        self.patterns = patterns or get_default_patterns()
        self.exclude_files = EXCLUDED_FILES | (exclude_files or set())

        # Pre-compile patterns
        self._compiled = {p: compile_pattern(p) for p in self.patterns}

    def scan_path(self, path: Path) -> ScanResult:
        """
        Scan a file or directory for violations.

        Args:
            path: File or directory path to scan

        Returns:
            ScanResult with all violations found
        """
        if not path.exists():
            raise FileNotFoundError(f"Path not found: {path}")

        skipped_files: list[str] = []
        skip_reasons: list[str] = []

        if path.is_file():
            file_results = [self._scan_file(path)]
        else:
            file_results, skipped_files, skip_reasons = self._scan_directory(path)

        # Aggregate results
        all_violations = tuple(v for fr in file_results for v in fr.violations)
        total_violations = len(all_violations)
        critical, warning, info = _count_by_severity(all_violations)

        return ScanResult(
            base_path=str(path),
            file_results=tuple(file_results),
            total_violations=total_violations,
            critical_count=critical,
            warning_count=warning,
            info_count=info,
            files_scanned=len(file_results),
            passed=total_violations == 0,
            skipped_files=tuple(skipped_files),
            skip_reasons=tuple(skip_reasons),
        )

    def _scan_directory(self, dir_path: Path) -> tuple[list[FileResult], list[str], list[str]]:
        """Recursively scan a directory.

        Returns:
            Tuple of (file_results, skipped_files, skip_reasons)
        """
        results: list[FileResult] = []
        skipped_files: list[str] = []
        skip_reasons: list[str] = []

        for item in dir_path.rglob("*"):
            # Skip certain directories
            if any(skip in item.parts for skip in SKIP_DIRS):
                continue

            # SEG-005: Skip symlinks to prevent directory escape
            if item.is_symlink():
                logger.debug("Skipping symlink: %s", item)
                continue

            # Skip binary files
            if item.suffix.lower() in SKIP_EXTENSIONS:
                continue

            # Skip excluded files
            if item.name in self.exclude_files:
                continue

            if item.is_file():
                try:
                    result = self._scan_file(item)
                    results.append(result)
                except UnicodeDecodeError:
                    skipped_files.append(str(item))
                    skip_reasons.append("encoding_error")
                    logger.warning("Skipping file with encoding issues: %s", item)
                except PermissionError:
                    skipped_files.append(str(item))
                    skip_reasons.append("permission_denied")
                    logger.warning("Permission denied, skipping: %s", item)
                except OSError as e:
                    skipped_files.append(str(item))
                    skip_reasons.append(f"os_error: {e}")
                    logger.warning("Error accessing file %s: %s", item, e)

        return results, skipped_files, skip_reasons

    def _scan_file(self, file_path: Path) -> FileResult:
        """Scan a single file for violations."""
        violations: list[Violation] = []
        str_path = str(file_path)

        # Check file path against patterns
        for pattern in self.patterns:
            if pattern.scope in (MatchScope.FILE_PATH, MatchScope.BOTH):
                violations.extend(self._match_path(str_path, pattern))

        # Check file content if it's a text file
        if self._is_text_file(file_path):
            # LOG-006: Check file size before reading
            try:
                file_size = file_path.stat().st_size
                if file_size > MAX_FILE_SIZE_BYTES:
                    logger.warning(
                        "Skipping large file (%d bytes): %s",
                        file_size,
                        file_path,
                    )
                    return FileResult(
                        file_path=str_path,
                        violations=tuple(violations),
                        passed=len(violations) == 0,
                    )
            except OSError as e:
                logger.warning("Cannot stat file %s: %s", file_path, e)

            try:
                content = file_path.read_text(encoding="utf-8")
                for pattern in self.patterns:
                    if pattern.scope in (MatchScope.FILE_CONTENT, MatchScope.BOTH):
                        violations.extend(self._match_content(file_path, content, pattern))
            except UnicodeDecodeError:
                # SMELL-001: Log for debugging instead of silent pass
                logger.debug("Skipping binary file: %s", file_path)

        return FileResult(
            file_path=str_path,
            violations=tuple(violations),
            passed=len(violations) == 0,
        )

    def _match_path(self, full_path: str, pattern: Pattern) -> list[Violation]:
        """Match pattern against file path."""
        violations: list[Violation] = []
        compiled = self._compiled[pattern]

        # Require a whole path component, never a suffix of an ordinary name.
        violation_type = get_violation_type(pattern)
        for match in compiled.finditer(full_path):
            # On POSIX a backslash is a filename character, not a separator.
            # Use the native path separator for both sides of alias components.
            if violation_type == ViolationType.DIRECTORY_ALIAS:
                # On POSIX a matched literal backslash belongs to the directory
                # name; it is not a separator for an alias like .claude.
                if os.sep != "\\" and match.group().endswith("\\"):
                    continue
                # A regex may consume the separator or stop just before it,
                # as with a custom lookahead pattern.
                after_match = match.end() < len(full_path) and full_path[match.end()] == os.sep
                if not (match.group().endswith(os.sep) or after_match):
                    continue
            # A file alias must match the complete basename, not .cursorrules.local
            # or a directory named .cursorrules.
            if violation_type == ViolationType.FILE_ALIAS and match.end() != len(full_path):
                continue
            if (
                violation_type in (ViolationType.DIRECTORY_ALIAS, ViolationType.FILE_ALIAS)
                and match.start() > 0
                and full_path[match.start() - 1] != os.sep
                and not match.group().startswith(os.sep)
            ):
                continue
            violations.append(
                Violation(
                    file_path=full_path,
                    line=None,
                    column=match.start(),
                    violation_type=get_violation_type(pattern),
                    severity=pattern.severity,
                    pattern=pattern,
                    match=match.group(),
                    suggestion=pattern.suggestion,
                    context=None,
                )
            )

        return violations

    def _match_content(self, file_path: Path, content: str, pattern: Pattern) -> list[Violation]:
        """Match pattern against file content."""
        violations: list[Violation] = []
        compiled = self._compiled[pattern]
        lines = content.split("\n")

        # LOG-001: Use robust code block detection
        code_block_ranges = self._find_code_block_ranges(lines)

        for i, line in enumerate(lines, start=1):
            # LOG-001: Skip lines inside code blocks
            if self._is_line_in_code_block(i - 1, code_block_ranges):
                continue

            for match in compiled.finditer(line):
                violations.append(
                    Violation(
                        file_path=str(file_path),
                        line=i,
                        column=match.start() + 1,  # 1-indexed
                        violation_type=get_violation_type(pattern),
                        severity=pattern.severity,
                        pattern=pattern,
                        match=match.group(),
                        suggestion=pattern.suggestion,
                        # SMELL-003, NIT-003: Use constant for truncation
                        context=line.strip()[:MAX_CONTEXT_LENGTH],
                    )
                )

        return violations

    def _find_code_block_ranges(self, lines: list[str]) -> list[tuple[int, int]]:
        """
        LOG-001: Find all code block ranges in markdown.

        Returns list of (start_line_idx, end_line_idx) tuples (0-indexed, exclusive).
        Properly handles:
        - Balanced code blocks
        - Language specifiers (```python)
        - Lines with ``` in the middle (not just at start)
        """
        ranges: list[tuple[int, int]] = []
        in_block = False
        block_start = -1

        for i, line in enumerate(lines):
            # Only match ``` at the START of a line (with optional whitespace)
            stripped = line.strip()
            if stripped.startswith("```"):
                if not in_block:
                    # Start of code block
                    in_block = True
                    block_start = i
                else:
                    # End of code block
                    ranges.append((block_start, i + 1))
                    in_block = False
                    block_start = -1

        # Handle unclosed code block (treat rest of file as code)
        if in_block:
            ranges.append((block_start, len(lines)))

        return ranges

    def _is_line_in_code_block(
        self, line_idx: int, code_block_ranges: list[tuple[int, int]]
    ) -> bool:
        """
        LOG-001: Check if a line index is within any code block range.
        """
        return any(start <= line_idx < end for start, end in code_block_ranges)

    def _is_text_file(self, file_path: Path) -> bool:
        """Check if a file is likely a text file."""
        # Check extension
        text_extensions = {
            ".md",
            ".txt",
            ".py",
            ".js",
            ".ts",
            ".tsx",
            ".jsx",
            ".json",
            ".yaml",
            ".yml",
            ".toml",
            ".cfg",
            ".ini",
            ".html",
            ".css",
            ".scss",
            ".sh",
            ".bash",
            ".zsh",
            ".fish",
        }
        if file_path.suffix.lower() in text_extensions:
            return True

        # Check for files without extensions (like .airules)
        if file_path.suffix == "" and file_path.name.startswith("."):
            return True

        # Check for specific filenames
        text_names = {".airules", ".aiignore", "Makefile", "Dockerfile"}
        return file_path.name in text_names


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================


def scan(
    path: Path,
    patterns: list[Pattern] | None = None,
    exclude_files: set[str] | None = None,
) -> ScanResult:
    """
    Scan a path for constitution violations.

    Args:
        path: File or directory to scan
        patterns: Patterns to use (default: all)
        exclude_files: Files to exclude

    Returns:
        ScanResult with all violations
    """
    scanner = ConstitutionScanner(patterns=patterns, exclude_files=exclude_files)
    return scanner.scan_path(path)


__all__ = [
    "ConstitutionScanner",
    "scan",
    "EXCLUDED_FILES",
    "SKIP_DIRS",
    "SKIP_EXTENSIONS",
]
