"""
Constitution Linter Types.

Data types for detecting and fixing violations of Law VII, Article 2
(Model Neutrality) of the Agentic Code Constitution.

F-001: Includes FileResult for per-file scan results.
F-002: Includes MatchScope for pattern matching context.
F-005: Includes case_sensitive flag (default: False).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Final

# =============================================================================
# SHARED CONSTANTS
# =============================================================================

# Maximum file size to read (10MB) - LOG-006
MAX_FILE_SIZE_BYTES: Final[int] = 10 * 1024 * 1024

# Maximum context length for violation preview (NIT-003)
MAX_CONTEXT_LENGTH: Final[int] = 100


class Severity(Enum):
    """Violation severity levels."""

    CRITICAL = "critical"  # Must fix - violates constitution
    WARNING = "warning"  # Should fix - may be intentional
    INFO = "info"  # Consider fixing - context dependent


class ViolationType(Enum):
    """Type of model neutrality violation."""

    DIRECTORY_ALIAS = "directory_alias"  # e.g., .cursor/ instead of .ai/
    FILE_ALIAS = "file_alias"  # e.g., .cursorrules instead of .airules
    TEXT_REFERENCE = "text_reference"  # e.g., "cursor rules" in content
    TYPO = "typo"  # e.g., "Claude" instead of "AI"


class MatchScope(Enum):
    """F-002: Where to apply pattern matching."""

    FILE_PATH = "file_path"  # Match against file/directory paths only
    FILE_CONTENT = "file_content"  # Match against file contents only
    BOTH = "both"  # Match against both (default)


@dataclass(frozen=True)
class Pattern:
    """A detection pattern with its replacement suggestion."""

    pattern: str  # Regex pattern
    suggestion: str  # Replacement text
    severity: Severity
    rule_id: str
    description: str = ""
    scope: MatchScope = MatchScope.BOTH
    case_sensitive: bool = False  # F-005: Default to case-insensitive


@dataclass(frozen=True)
class Violation:
    """A single violation found in a file."""

    file_path: str
    line: int | None
    column: int | None
    violation_type: ViolationType
    severity: Severity
    pattern: Pattern
    match: str  # The actual matched text
    suggestion: str  # What to replace with (for easy access)
    context: str | None = None  # Surrounding line for preview


@dataclass(frozen=True)
class FileResult:
    """F-001: Scan result for a single file."""

    file_path: str
    violations: tuple[Violation, ...]
    passed: bool

    @property
    def violation_count(self) -> int:
        """Total number of violations in this file."""
        return len(self.violations)


@dataclass(frozen=True)
class ScanResult:
    """Complete scan result for a directory or file."""

    base_path: str
    file_results: tuple[FileResult, ...]
    total_violations: int
    critical_count: int
    warning_count: int
    info_count: int
    files_scanned: int
    passed: bool
    skipped_files: tuple[str, ...] = ()  # Files that couldn't be scanned
    skip_reasons: tuple[str, ...] = ()  # Reasons for skipping (parallel to skipped_files)

    @property
    def all_violations(self) -> tuple[Violation, ...]:
        """Flatten all violations from all files."""
        return tuple(v for fr in self.file_results for v in fr.violations)


@dataclass(frozen=True)
class FixPlan:
    """A plan for fixing violations."""

    violations: tuple[Violation, ...]  # Safe fixes first, then review-only fixes
    backup_path: str | None
    created_at: str  # ISO timestamp
    total_fixes: int
    safe_fixes: int  # Fixes that don't need review
    needs_review: int  # Fixes that need human review


@dataclass(frozen=True)
class FixResult:
    """Result of applying a fix plan."""

    plan: FixPlan
    files_modified: tuple[str, ...]
    success: bool
    error_message: str | None = None
    path_renames: tuple[tuple[str, str], ...] = ()


__all__ = [
    # Constants
    "MAX_FILE_SIZE_BYTES",
    "MAX_CONTEXT_LENGTH",
    # Types
    "Severity",
    "ViolationType",
    "MatchScope",
    "Pattern",
    "Violation",
    "FileResult",
    "ScanResult",
    "FixPlan",
    "FixResult",
]
