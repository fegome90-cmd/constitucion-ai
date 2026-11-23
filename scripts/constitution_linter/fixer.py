"""
Constitution Linter Fixer.

Applies fixes for model neutrality violations with backup support.
F-003: Backup strategy with retention policy.
"""

from __future__ import annotations

import logging
import os
import re
import secrets
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
        resolved = base_path.resolve()
        self.base_path = resolved.parent if resolved.is_file() else resolved
        self.backup_dir = self.base_path / BACKUP_DIR

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
            # A path-only match without a directory/file alias requires human
            # interpretation; it is not a content span that can be autofixed.
            if v.line is None and v.violation_type not in (
                ViolationType.DIRECTORY_ALIAS,
                ViolationType.FILE_ALIAS,
            ):
                needs_review.append(v)
                continue
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
        self.backup_dir.mkdir(parents=True, exist_ok=True)

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

    def planned_path_renames(self, plan: FixPlan) -> tuple[tuple[Path, Path], ...]:
        """Canonical lexical path moves for apply and pre-commit validation."""
        renames: dict[Path, Path] = {}
        reverse: dict[Path, Path] = {}
        for violation in plan.violations:
            if violation.violation_type == ViolationType.DIRECTORY_ALIAS:
                if violation.column is None:
                    raise ValueError("Directory violation has no matched path offset")
                match_end = violation.column + len(violation.match)
                source = Path(violation.file_path[:match_end].removesuffix(os.sep)).absolute()
            elif violation.violation_type == ViolationType.FILE_ALIAS:
                source = Path(violation.file_path).absolute()
            else:
                continue
            destination = source.with_name(violation.suggestion.rstrip("/\\"))
            # Do not modify ancestors of a scoped file/subtree.
            if not source.is_relative_to(self.base_path) or not destination.is_relative_to(
                self.base_path
            ):
                continue
            if source in renames and renames[source] != destination:
                raise ValueError(f"Conflicting rename for {source}")
            prior = reverse.get(destination)
            if prior is not None and prior != source:
                raise ValueError(
                    f"Conflicting rename destination {destination}: {prior} and {source}"
                )
            renames[source] = destination
            reverse[destination] = source
        return tuple(sorted(renames.items(), key=lambda item: len(item[0].parts), reverse=True))

    def apply_plan(
        self,
        plan: FixPlan,
        dry_run: bool = False,
        create_backup: bool = True,
        interactive: bool = False,
    ) -> FixResult:
        """Apply content edits at scanned positions, then rename paths once."""
        if not plan.violations:
            return FixResult(plan=plan, files_modified=(), success=True, error_message=None)

        content_edits: dict[Path, list[Violation]] = {}
        modified: list[str] = []
        updated_plan = plan

        try:
            ordered_renames = self.planned_path_renames(plan)
            renames = dict(ordered_renames)
            for violation in plan.violations:
                if (
                    violation.violation_type
                    in (
                        ViolationType.DIRECTORY_ALIAS,
                        ViolationType.FILE_ALIAS,
                    )
                    or violation.line is None
                ):
                    continue
                content_edits.setdefault(Path(violation.file_path).absolute(), []).append(violation)

            # Validate all targets before touching any file.
            for source in content_edits:
                self._validate_path_in_base(source)
            for source, destination in renames.items():
                self._validate_path_in_base(source)
                self._validate_path_in_base(destination)
                if not source.exists() or source.is_symlink():
                    raise FileNotFoundError(f"Rename source missing or symlink: {source}")
                if destination.exists() or destination.is_symlink():
                    raise FileExistsError(f"Rename destination already exists: {destination}")

            if create_backup and not dry_run:
                sources = list(dict.fromkeys([*content_edits, *renames]))
                backup_path = self.create_backup(sources)
                if backup_path:
                    updated_plan = FixPlan(
                        violations=plan.violations,
                        backup_path=str(backup_path),
                        created_at=plan.created_at,
                        total_fixes=plan.total_fixes,
                        safe_fixes=plan.safe_fixes,
                        needs_review=plan.needs_review,
                    )

            # Edits must use original paths; the path aliases are renamed afterwards.
            original_sources = set(content_edits) | set(renames)
            for source, violations in content_edits.items():
                if self._apply_content_fix(source, violations, dry_run, interactive):
                    modified.append(str(source))

            # Deepest first, to support nested aliases without invalidating child paths.
            for source, destination in ordered_renames:
                if self._apply_path_fix(source, destination, dry_run):
                    modified.extend((str(source), str(destination)))

            # Commit only original sources and final destinations; nested renames
            # can create transient paths that no longer exist after their parent moves.
            originally_modified = {
                Path(path) for path in modified if Path(path) in original_sources
            }
            final_modified = {Path(path) for path in modified}
            for source, destination in ordered_renames:
                final_modified = {
                    destination / path.relative_to(source)
                    if path == source or path.is_relative_to(source)
                    else path
                    for path in final_modified
                }
            final_modified = {path for path in final_modified if dry_run or path.exists()}
            modified = [str(path) for path in sorted(originally_modified | final_modified)]
        except (OSError, ValueError, PathSecurityError) as exc:
            return FixResult(
                plan=updated_plan,
                files_modified=tuple(dict.fromkeys(modified)),
                success=False,
                error_message=str(exc),
            )

        return FixResult(
            plan=updated_plan,
            files_modified=tuple(dict.fromkeys(modified)),
            success=True,
            error_message=None,
            path_renames=tuple((str(src), str(dst)) for src, dst in ordered_renames),
        )

    def _apply_path_fix(self, source: Path, destination: Path, dry_run: bool) -> bool:
        """Rename one matched path component, refusing collisions."""
        self._validate_path_in_base(source)
        self._validate_path_in_base(destination)
        if destination.exists() or destination.is_symlink():
            raise FileExistsError(f"Rename destination already exists: {destination}")
        if dry_run:
            print(f"Would rename: {source} -> {destination}")
            return True
        source.rename(destination)
        return True

    def _apply_content_fix(
        self,
        file_path: Path,
        violations: list[Violation],
        dry_run: bool,
        interactive: bool,
    ) -> bool:
        """Replace only scanner-reported spans, preserving other text and file mode."""
        self._validate_path_in_base(file_path)
        if file_path.is_symlink():
            raise PathSecurityError(f"Refusing to edit symlink: {file_path}")
        if file_path.stat().st_size > MAX_FILE_SIZE_BYTES:
            return False

        # Preserve CRLF while matching the scanner's LF-only logical boundaries.
        # splitlines() incorrectly splits within a scanned U+2028 line.
        with file_path.open("r", encoding="utf-8", newline="") as stream:
            raw_text = stream.read()
        # Path.read_text in the scanner translates CR, LF and CRLF into LF.
        # Keep the original line endings while calculating the same positions.
        parts = re.split(r"(\r\n|\r|\n)", raw_text)
        lines = [
            parts[i] + (parts[i + 1] if i + 1 < len(parts) else "") for i in range(0, len(parts), 2)
        ]
        by_line: dict[int, list[Violation]] = {}
        for violation in violations:
            if violation.line is None or violation.column is None:
                raise ValueError(f"Content violation missing location: {violation}")
            by_line.setdefault(violation.line - 1, []).append(violation)

        modified = False
        for line_index, matches in by_line.items():
            if line_index >= len(lines):
                raise ValueError(f"Stale scan: line {line_index + 1} no longer exists")
            original_line = lines[line_index]
            accepted: list[tuple[int, int, Violation]] = []
            for violation in sorted(matches, key=lambda v: (v.column or 0, -len(v.match))):
                assert violation.column is not None  # checked when grouping matches
                start = violation.column - 1
                end = start + len(violation.match)
                if original_line[start:end] != violation.match:
                    raise ValueError(f"Stale scan at {file_path}:{line_index + 1}")
                if any(
                    start < prior_end and end > prior_start
                    for prior_start, prior_end, _ in accepted
                ):
                    continue
                accepted.append((start, end, violation))

            new_line = original_line
            for start, end, violation in sorted(accepted, key=lambda match: match[0], reverse=True):
                if interactive:
                    print(f"\n{file_path}:{line_index + 1}")
                    print(f"  Found: {violation.match}")
                    print(f"  Replace with: {violation.suggestion}")
                    if input("Apply? [y/N] ").lower() != "y":
                        continue
                # The scanner matches the logical line without its CR/LF terminator.
                logical_line = original_line
                if logical_line.endswith("\r\n"):
                    logical_line = logical_line[:-2]
                elif logical_line.endswith(("\r", "\n")):
                    logical_line = logical_line[:-1]
                matched = compile_pattern(violation.pattern).match(logical_line, start)
                if matched is None or matched.end() != end:
                    raise ValueError(f"Stale regex match at {file_path}:{line_index + 1}")
                try:
                    replacement = matched.expand(violation.suggestion)
                except re.error as exc:
                    raise ValueError(
                        f"Invalid replacement for {violation.pattern.rule_id}"
                    ) from exc
                new_line = new_line[:start] + replacement + new_line[end:]
            if new_line != original_line:
                lines[line_index] = new_line
                modified = True

        if not modified:
            return False
        if dry_run:
            print(f"Would modify: {file_path}")
            return True

        # Same-directory temporary write; preserve the exact Unix mode before atomic swap.
        file_mode = file_path.stat().st_mode
        fd, temp_path = tempfile.mkstemp(
            dir=file_path.parent, prefix=f".{file_path.name}.", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="") as stream:
                stream.write("".join(lines))
            os.chmod(temp_path, file_mode)
            os.replace(temp_path, file_path)
        finally:
            Path(temp_path).unlink(missing_ok=True)
        return True

    def generate_diff(self, plan: FixPlan) -> str:
        """Preview all reported path and content changes without modifying files."""
        diff_lines: list[str] = []
        by_file: dict[str, list[Violation]] = {}
        for violation in plan.violations:
            by_file.setdefault(violation.file_path, []).append(violation)

        seen_renames: set[tuple[Path, Path]] = set()
        for filename, violations in sorted(by_file.items()):
            path = Path(filename).absolute()
            path_fixes = [
                v
                for v in violations
                if v.violation_type in (ViolationType.DIRECTORY_ALIAS, ViolationType.FILE_ALIAS)
            ]
            for violation in path_fixes:
                if violation.violation_type == ViolationType.DIRECTORY_ALIAS:
                    assert violation.column is not None
                    end = violation.column + len(violation.match)
                    source_path = Path(filename[:end].rstrip("/\\")).absolute()
                else:
                    source_path = path
                destination = source_path.with_name(violation.suggestion.rstrip("/\\"))
                if (
                    not source_path.is_relative_to(self.base_path)
                    or not destination.is_relative_to(self.base_path)
                    or (source_path, destination) in seen_renames
                ):
                    continue
                seen_renames.add((source_path, destination))
                diff_lines.extend(
                    (
                        f"--- {source_path}",
                        f"+++ {destination}",
                        "Path rename (file or directory will be moved)",
                    )
                )

            content_fixes = [
                v
                for v in violations
                if v.violation_type not in (ViolationType.DIRECTORY_ALIAS, ViolationType.FILE_ALIAS)
            ]
            if not content_fixes:
                continue
            try:
                lines = path.read_text(encoding="utf-8").split("\n")
            except (FileNotFoundError, UnicodeDecodeError):
                continue

            by_line: dict[int, list[Violation]] = {}
            for violation in content_fixes:
                if violation.line is not None and violation.column is not None:
                    by_line.setdefault(violation.line - 1, []).append(violation)

            changes: list[tuple[int, str, str]] = []
            for index, matches in sorted(by_line.items()):
                if index >= len(lines):
                    continue
                before = lines[index]
                after = before
                accepted: list[tuple[int, int, Violation]] = []
                for violation in sorted(matches, key=lambda v: (v.column or 0, -len(v.match))):
                    assert violation.column is not None
                    begin = violation.column - 1
                    end = begin + len(violation.match)
                    if before[begin:end] != violation.match:
                        continue
                    if any(
                        begin < prior_end and end > prior_begin
                        for prior_begin, prior_end, _ in accepted
                    ):
                        continue
                    accepted.append((begin, end, violation))
                for begin, end, violation in sorted(
                    accepted, key=lambda item: item[0], reverse=True
                ):
                    match = compile_pattern(violation.pattern).match(before, begin)
                    if match is not None and match.end() == end:
                        after = after[:begin] + match.expand(violation.suggestion) + after[end:]
                if after != before:
                    changes.append((index + 1, before, after))

            if changes:
                diff_lines.extend((f"--- {filename}", f"+++ {filename}"))
                for index, before, after in changes:
                    diff_lines.extend((f"@@ -{index} +{index} @@", f"-{before}", f"+{after}"))
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
