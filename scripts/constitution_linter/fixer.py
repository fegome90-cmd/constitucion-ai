"""
Constitution Linter Fixer.

Applies fixes for model neutrality violations with backup support.
F-003: Backup strategy with retention policy.
"""

from __future__ import annotations

import logging
import os
import secrets
import shutil
import tarfile
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Final

from .patterns import compile_pattern
from .types import (
    MAX_FILE_SIZE_BYTES,
    FixPlan,
    FixResult,
    ScanResult,
    Violation,
    ViolationType,
)

logger = logging.getLogger(__name__)

# =============================================================================
# BACKUP CONFIGURATION (F-003)
# =============================================================================

BACKUP_DIR: Final[str] = ".backups/constitution_linter"
BACKUP_RETENTION_DAYS: Final[int] = 7
BACKUP_FORMAT: Final[str] = "tar.gz"


class PathSecurityError(Exception):
    """Raised when a path violates security constraints."""

    pass


# =============================================================================
# FIXER CLASS
# =============================================================================


class ConstitutionFixer:
    """Applies fixes for model neutrality violations."""

    def __init__(self, base_path: Path) -> None:
        """
        Initialize fixer.

        Args:
            base_path: Base directory for backups and fixes
        """
        self.base_path = base_path.resolve()
        self.backup_dir = self.base_path / BACKUP_DIR
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def _validate_path_in_base(self, path: Path) -> None:
        """
        Validate that path is within base directory.

        SEG-001, SEG-002: Prevent path traversal attacks.

        Args:
            path: Path to validate

        Raises:
            PathSecurityError: If path escapes base directory
        """
        try:
            resolved = path.resolve()
            resolved.relative_to(self.base_path)
        except ValueError as err:
            raise PathSecurityError(
                f"Path '{path}' is outside base directory '{self.base_path}'"
            ) from err

    def create_plan(self, scan_result: ScanResult, review_required: bool = False) -> FixPlan:
        """
        Create a fix plan from scan results.

        Args:
            scan_result: Scan results to create plan from
            review_required: If True, mark all fixes as needing review

        Returns:
            FixPlan with all fixes to apply
        """
        violations = scan_result.all_violations

        # Separate safe fixes from those needing review
        safe_fixes: list[Violation] = []
        needs_review: list[Violation] = []

        for v in violations:
            # Directory aliases are always safe (file system level)
            if (
                v.violation_type == ViolationType.DIRECTORY_ALIAS
                or v.violation_type == ViolationType.FILE_ALIAS
                or v.violation_type == ViolationType.TYPO
            ):
                safe_fixes.append(v)
            # Text references might need review if they could be in examples
            elif v.violation_type == ViolationType.TEXT_REFERENCE:
                if review_required or self._in_example_context(v):
                    needs_review.append(v)
                else:
                    safe_fixes.append(v)
            else:
                needs_review.append(v)

        return FixPlan(
            violations=tuple(safe_fixes + needs_review),
            backup_path=None,  # Set when backup is created
            created_at=datetime.now().isoformat(),
            total_fixes=len(violations),
            safe_fixes=len(safe_fixes),
            needs_review=len(needs_review),
        )

    @staticmethod
    def _in_example_context(violation: Violation) -> bool:
        """
        Check if violation might be in an example/documentation context.

        SMELL-006: Made static since it doesn't use self.
        """
        if not violation.context:
            return False

        # Check for common documentation markers
        doc_markers = ["ejemplo:", "example:", "e.g.", "i.e.", "por ejemplo"]
        context_lower = violation.context.lower()

        return any(marker in context_lower for marker in doc_markers)

    def create_backup(self, files: list[Path]) -> Path | None:
        """
        Create timestamped backup before modifications.

        F-003: Creates tar.gz backup with retention policy.
        SEG-001: Validates all paths are within base directory.
        NIT-004: Uses random suffix to prevent timestamp collisions.

        Args:
            files: List of files to backup

        Returns:
            Path to backup file, or None if no files to backup

        Raises:
            PathSecurityError: If any file is outside base directory
        """
        if not files:
            return None

        # Validate all paths first
        for file_path in files:
            self._validate_path_in_base(file_path)

        # NIT-004: Add random suffix to prevent collisions
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = secrets.token_hex(4)
        backup_path = self.backup_dir / f"backup_{timestamp}_{random_suffix}.tar.gz"

        with tarfile.open(backup_path, "w:gz") as tar:
            for file_path in files:
                if file_path.exists():
                    # SEG-001: Store with relative path for cleaner extraction
                    try:
                        arcname = str(file_path.relative_to(self.base_path))
                    except ValueError:
                        # Should not happen due to validation above, but be safe
                        logger.warning("Skipping file outside base: %s", file_path)
                        continue
                    tar.add(file_path, arcname=arcname)

        return backup_path

    def cleanup_old_backups(self) -> int:
        """
        Remove backups older than retention period.

        F-003: Cleanup based on BACKUP_RETENTION_DAYS.

        Returns:
            Number of backups removed
        """
        cutoff = datetime.now() - timedelta(days=BACKUP_RETENTION_DAYS)
        removed = 0

        for backup in self.backup_dir.glob("backup_*.tar.gz"):
            # Parse timestamp from filename (handle both old and new format)
            try:
                # New format: backup_20260315_120000_abc12345.tar.gz
                # Old format: backup_20260315_120000.tar.gz
                filename = backup.stem.replace("backup_", "")
                # Remove random suffix if present
                parts = filename.rsplit("_", 1)
                timestamp_str = parts[0] if len(parts) > 1 else filename
                backup_time = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")

                if backup_time < cutoff:
                    backup.unlink()
                    removed += 1
            except ValueError:
                # Skip files with unexpected names
                continue

        return removed

    def apply_plan(
        self,
        plan: FixPlan,
        dry_run: bool = False,
        create_backup: bool = True,
        interactive: bool = False,
    ) -> FixResult:
        """
        Apply a fix plan to files.

        Args:
            plan: Fix plan to apply
            dry_run: If True, only show what would be changed
            create_backup: If True, create backup before modifying
            interactive: If True, prompt for each fix

        Returns:
            FixResult with applied changes
        """
        if not plan.violations:
            return FixResult(
                plan=plan,
                files_modified=(),
                success=True,
                error_message=None,
            )

        # Group violations by file
        by_file: dict[str, list[Violation]] = {}
        for v in plan.violations:
            if v.file_path not in by_file:
                by_file[v.file_path] = []
            by_file[v.file_path].append(v)

        files_to_modify = [Path(fp) for fp in by_file]

        # LOG-002: Create backup and update plan with backup path
        updated_plan = plan
        if create_backup and not dry_run:
            backup_path = self.create_backup(files_to_modify)
            if backup_path:
                # Create updated plan with backup path (FixPlan is frozen, so create new)
                updated_plan = FixPlan(
                    violations=plan.violations,
                    backup_path=str(backup_path),
                    created_at=plan.created_at,
                    total_fixes=plan.total_fixes,
                    safe_fixes=plan.safe_fixes,
                    needs_review=plan.needs_review,
                )

        modified_files: list[str] = []

        for file_path_str, violations in by_file.items():
            file_path = Path(file_path_str)

            if not file_path.exists():
                continue

            try:
                if violations[0].violation_type in (
                    ViolationType.DIRECTORY_ALIAS,
                    ViolationType.FILE_ALIAS,
                ):
                    # File/directory rename
                    if self._apply_path_fix(file_path, violations, dry_run):
                        modified_files.append(file_path_str)
                else:
                    # Content fix
                    if self._apply_content_fix(file_path, violations, dry_run, interactive):
                        modified_files.append(file_path_str)
            except PathSecurityError as e:
                return FixResult(
                    plan=updated_plan,
                    files_modified=tuple(modified_files),
                    success=False,
                    error_message=f"Security error: {e}",
                )
            except Exception as e:
                return FixResult(
                    plan=updated_plan,
                    files_modified=tuple(modified_files),
                    success=False,
                    error_message=f"Error fixing {file_path}: {e}",
                )

        return FixResult(
            plan=updated_plan,
            files_modified=tuple(modified_files),
            success=True,
            error_message=None,
        )

    def _apply_path_fix(self, file_path: Path, violations: list[Violation], dry_run: bool) -> bool:
        """
        Apply path-based fix (rename file/directory).

        SEG-002: Validates paths to prevent arbitrary file writes.
        LOG-003: Returns True for successful dry run.
        LOG-005: Checks for file collisions before rename.
        """
        if not violations:
            return False

        # Use first violation's suggestion
        new_name = violations[0].suggestion
        new_path = file_path.parent / new_name

        # SEG-002: Validate both paths are within base directory
        self._validate_path_in_base(file_path)
        self._validate_path_in_base(new_path)

        if dry_run:
            print(f"Would rename: {file_path} -> {new_path}")
            return True  # LOG-003: Return True for successful dry run

        # LOG-005: Check for collision before rename
        if new_path.exists():
            logger.warning(
                "Cannot rename %s to %s: destination already exists",
                file_path,
                new_path,
            )
            return False

        file_path.rename(new_path)
        return True

    def _apply_content_fix(
        self,
        file_path: Path,
        violations: list[Violation],
        dry_run: bool,
        interactive: bool,
    ) -> bool:
        """
        Apply content-based fix (replace text in file).

        SEG-006: Uses atomic write pattern (temp file + rename).
        LOG-006: Checks file size before reading.
        """
        # SEG-002: Validate path is within base directory
        self._validate_path_in_base(file_path)

        # LOG-006: Check file size before reading
        try:
            file_size = file_path.stat().st_size
            if file_size > MAX_FILE_SIZE_BYTES:
                logger.warning("Skipping large file (%d bytes): %s", file_size, file_path)
                return False
        except OSError as e:
            logger.warning("Cannot stat file %s: %s", file_path, e)
            return False

        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return False

        modified = False

        for v in violations:
            compiled = compile_pattern(v.pattern)

            if interactive:
                print(f"\n{file_path}:{v.line}")
                print(f"  Found: {v.match}")
                print(f"  Replace with: {v.suggestion}")
                response = input("Apply? [y/N] ")
                if response.lower() != "y":
                    continue

            content = compiled.sub(v.suggestion, content)
            modified = True

        if dry_run:
            if modified:
                print(f"Would modify: {file_path}")
            return modified

        if modified:
            # SEG-006: Atomic write - write to temp file, then rename
            try:
                # Create temp file in same directory for atomic rename
                fd, temp_path = tempfile.mkstemp(
                    dir=file_path.parent,
                    prefix=f".{file_path.name}.",
                    suffix=".tmp",
                )
                try:
                    with os.fdopen(fd, "w", encoding="utf-8") as f:
                        f.write(content)
                    # Atomic rename
                    shutil.move(temp_path, file_path)
                except Exception:
                    # Clean up temp file on error
                    Path(temp_path).unlink(missing_ok=True)
                    raise
            except OSError as e:
                logger.error("Failed to write file %s: %s", file_path, e)
                return False
            return True

        return False

    def generate_diff(self, plan: FixPlan) -> str:
        """
        Generate a unified diff preview of all changes.

        Args:
            plan: Fix plan to generate diff for

        Returns:
            Unified diff string
        """
        diff_lines: list[str] = []

        # Group violations by file
        by_file: dict[str, list[Violation]] = {}
        for v in plan.violations:
            if v.file_path not in by_file:
                by_file[v.file_path] = []
            by_file[v.file_path].append(v)

        for file_path_str, violations in sorted(by_file.items()):
            file_path = Path(file_path_str)

            if violations[0].violation_type in (
                ViolationType.DIRECTORY_ALIAS,
                ViolationType.FILE_ALIAS,
            ):
                # Path rename diff
                new_name = violations[0].suggestion
                diff_lines.append(f"--- {file_path_str}")
                diff_lines.append(f"+++ {file_path.parent / new_name}")
                diff_lines.append("Path rename (file will be moved)")
            else:
                # Content diff
                try:
                    content = file_path.read_text(encoding="utf-8")
                except (FileNotFoundError, UnicodeDecodeError):
                    continue

                lines = content.split("\n")
                diff_lines.append(f"--- {file_path_str}")
                diff_lines.append(f"+++ {file_path_str}")

                for v in sorted(violations, key=lambda x: x.line or 0):
                    if v.line and v.line <= len(lines):
                        old_line = lines[v.line - 1]
                        new_line = compile_pattern(v.pattern).sub(v.suggestion, old_line)
                        if old_line != new_line:
                            diff_lines.append(f"@@ -{v.line} +{v.line} @@")
                            diff_lines.append(f"-{old_line}")
                            diff_lines.append(f"+{new_line}")

        return "\n".join(diff_lines)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def create_fix_plan(scan_result: ScanResult, base_path: Path) -> FixPlan:
    """Create a fix plan from scan results."""
    fixer = ConstitutionFixer(base_path)
    return fixer.create_plan(scan_result)


def apply_fixes(plan: FixPlan, base_path: Path, dry_run: bool = False) -> FixResult:
    """Apply a fix plan."""
    fixer = ConstitutionFixer(base_path)
    return fixer.apply_plan(plan, dry_run=dry_run)


__all__ = [
    "ConstitutionFixer",
    "PathSecurityError",
    "create_fix_plan",
    "apply_fixes",
    "BACKUP_DIR",
    "BACKUP_RETENTION_DAYS",
    "MAX_FILE_SIZE_BYTES",
]
