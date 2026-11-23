"""
Constitution Linter CLI.

Command-line interface for scanning and fixing model neutrality violations.
"""

from __future__ import annotations

import argparse
import functools
import logging
import re
import shutil
import subprocess  # nosec B404 - controlled Git commands, no shell invocation
import sys
import tempfile
from bisect import bisect_left
from pathlib import Path
from typing import TYPE_CHECKING, Final, TypeVar, cast

from .fixer import ConstitutionFixer, PathSecurityError
from .reporter import Reporter
from .scanner import ConstitutionScanner
from .types import MAX_CONTEXT_LENGTH, ViolationType

if TYPE_CHECKING:
    from collections.abc import Callable

    from .types import FixPlan, FixResult, ScanResult

# =============================================================================
# LOGGING SETUP
# =============================================================================

logger = logging.getLogger(__name__)

# =============================================================================
# EXIT CODES
# =============================================================================

EXIT_SUCCESS = 0
EXIT_VIOLATIONS_FOUND = 1
EXIT_DRY_RUN = 2  # LOG-007: Documented - indicates dry run with violations
EXIT_VALIDATION_ERROR = 3
EXIT_EXECUTION_ERROR = 4

# =============================================================================
# CONFIGURATION CONSTANTS (SMELL-003)
# =============================================================================

# Maximum violations to include in commit message
MAX_COMMIT_VIOLATIONS: Final[int] = 10


# =============================================================================
# ERROR HANDLING DECORATOR (SMELL-002)
# =============================================================================

F = TypeVar("F", bound="Callable[[argparse.Namespace], int]")


def handle_scan_errors[F: "Callable[[argparse.Namespace], int]"](func: F) -> F:
    """
    Decorator to handle common scan errors.

    SMELL-002: Deduplicates FileNotFoundError handling across commands.
    Also handles path security validation (SEG-007).
    """

    @functools.wraps(func)
    def wrapper(args: argparse.Namespace) -> int:
        try:
            return func(args)
        except FileNotFoundError as e:
            print(f"Error: Path not found: {e}", file=sys.stderr)
            return EXIT_EXECUTION_ERROR
        except PathSecurityError as e:
            print(f"Security error: {e}", file=sys.stderr)
            return EXIT_EXECUTION_ERROR
        except PermissionError as e:
            print(f"Permission denied: {e}", file=sys.stderr)
            return EXIT_EXECUTION_ERROR

    return wrapper  # type: ignore


# =============================================================================
# PATH VALIDATION (SEG-007)
# =============================================================================


def validate_and_resolve_path(path_str: str) -> Path:
    """
    Validate and resolve a path, ensuring it doesn't escape.

    SEG-007: Prevents path traversal via CLI arguments.

    Args:
        path_str: Path string from CLI argument

    Returns:
        Resolved Path object

    Raises:
        PathSecurityError: If path contains suspicious patterns
        FileNotFoundError: If path doesn't exist
    """
    # Check for obvious path traversal attempts
    suspicious_patterns = ["../", "..\\", "/etc/", "/root/", "~"]
    for pattern in suspicious_patterns:
        if pattern in path_str:
            logger.warning("Suspicious path pattern detected: %s", path_str)

    path = Path(path_str).resolve()

    if not path.exists():
        raise FileNotFoundError(f"Path not found: {path}")

    return path


# =============================================================================
# COMMIT MESSAGE SANITIZATION (SEG-003)
# =============================================================================


def sanitize_commit_message(message: str) -> str:
    """
    Sanitize commit message to prevent command injection.

    SEG-003: Removes Git special characters and control sequences.

    Args:
        message: Raw commit message

    Returns:
        Sanitized message safe for git commit
    """
    # Remove control characters
    sanitized = re.sub(r"[\x00-\x1f\x7f]", "", message)

    # Remove Git command separators
    sanitized = re.sub(r"--[a-z-]+", "", sanitized)

    # Limit length
    max_length = 500
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length] + "..."

    return sanitized.strip()


# =============================================================================
# SCAN COMMAND
# =============================================================================


@handle_scan_errors
def cmd_scan(args: argparse.Namespace) -> int:
    """Execute scan command."""
    path = validate_and_resolve_path(args.path)
    scanner = ConstitutionScanner()
    reporter = Reporter(use_color=not args.no_color)

    result = scanner.scan_path(path)

    # Output results
    output = reporter.report_scan(result, format=args.format)
    print(output)

    # CI mode: exit with appropriate code
    if args.ci:
        if result.passed:
            return EXIT_SUCCESS
        return EXIT_VIOLATIONS_FOUND

    # Non-CI mode: show summary
    if not result.passed:
        return EXIT_VIOLATIONS_FOUND

    return EXIT_SUCCESS


# =============================================================================
# PLAN COMMAND
# =============================================================================


@handle_scan_errors
def cmd_plan(args: argparse.Namespace) -> int:
    """Execute plan command (generate fix plan)."""
    path = validate_and_resolve_path(args.path)
    scanner = ConstitutionScanner()
    fixer = ConstitutionFixer(path)
    reporter = Reporter(use_color=not args.no_color)

    result = scanner.scan_path(path)

    if result.passed:
        print("No violations found. Nothing to fix.")
        return EXIT_SUCCESS

    # Create fix plan
    plan = fixer.create_plan(result, review_required=args.review)

    # Output plan
    output = reporter.report_plan(plan, format=args.format)
    print(output)

    # Save to file if requested
    if args.output:
        from .reporter import to_json

        output_path = Path(args.output)
        output_path.write_text(to_json(plan), encoding="utf-8")
        print(f"\nPlan saved to: {output_path}")

    return EXIT_SUCCESS


# =============================================================================
# FIX COMMAND
# =============================================================================


@handle_scan_errors
def cmd_fix(args: argparse.Namespace) -> int:
    """Execute fix command (apply fixes)."""
    if Path(args.path).is_symlink():
        print(f"Refusing symlink input: {args.path}", file=sys.stderr)
        return EXIT_EXECUTION_ERROR
    path = validate_and_resolve_path(args.path)
    scanner = ConstitutionScanner()
    fixer = ConstitutionFixer(path)
    reporter = Reporter(use_color=not args.no_color)

    result = scanner.scan_path(path)

    if result.passed:
        print("No violations found. Nothing to fix.")
        return EXIT_SUCCESS

    # Create and apply fix plan
    plan = fixer.create_plan(result)

    # Show diff preview
    if args.dry_run:
        print("=== DRY RUN - No changes will be made ===\n")
        try:
            diff = fixer.generate_diff(plan)
        except (ValueError, PathSecurityError, OSError) as exc:
            print(f"Cannot preview changes: {exc}", file=sys.stderr)
            return EXIT_EXECUTION_ERROR
        print(diff)
        # LOG-007: Exit code 2 is intentional for dry run with changes
        return EXIT_DRY_RUN

    # Apply fixes
    fix_result = fixer.apply_plan(
        plan,
        dry_run=args.dry_run,
        create_backup=args.backup,
        interactive=args.interactive,
    )

    # Report results
    output = reporter.report_fix(fix_result, format=args.format)
    print(output)

    if not fix_result.success:
        return EXIT_EXECUTION_ERROR

    return EXIT_SUCCESS


# =============================================================================
# RUN-ALL COMMAND (SMELL-005: Refactored into smaller functions)
# =============================================================================


def _run_scan_step(
    path: Path, scanner: ConstitutionScanner, reporter: Reporter
) -> tuple[ScanResult, int] | None:
    """Run scan step and return result or None if passed."""
    print("Step 1: Scanning for violations...")
    result = scanner.scan_path(path)

    if result.passed:
        print("✅ No violations found. Nothing to do.")
        return None

    print(f"Found {result.total_violations} violations")
    print(reporter.report_scan(result, format="text"))
    return result, EXIT_SUCCESS


def _run_plan_step(fixer: ConstitutionFixer, result: ScanResult, reporter: Reporter) -> FixPlan:
    """Run plan step and return the plan."""
    print("\nStep 2: Creating fix plan...")
    plan = fixer.create_plan(result)
    print(reporter.report_plan(plan, format="text"))
    return plan


def _run_fix_step(
    fixer: ConstitutionFixer,
    plan: FixPlan,
    args: argparse.Namespace,
    reporter: Reporter,
) -> FixResult:
    """Run fix step and return the paths actually changed."""
    print("\nStep 3: Applying fixes...")
    fix_result = fixer.apply_plan(
        plan,
        dry_run=args.dry_run,
        create_backup=args.backup,
        interactive=args.interactive,
    )
    print(reporter.report_fix(fix_result, format="text"))

    return fix_result


def _run_commit_step(path: Path, plan: FixPlan, fix_result: FixResult) -> int:
    """Commit changes to existing tracked files, never unrelated local additions."""
    if not fix_result.files_modified:
        return EXIT_SUCCESS

    commit_lines = ["fix(constitution): apply model neutrality fixes", ""]
    for violation in plan.violations[:MAX_COMMIT_VIOLATIONS]:
        line = f"- {violation.pattern.rule_id}: {violation.match} → {violation.suggestion}"
        commit_lines.append(sanitize_commit_message(line))
    commit_msg = "\n".join(commit_lines)

    print("\nStep 4: Creating git commit...")
    try:
        cwd = path if path.is_dir() else path.parent
        git_executable = shutil.which("git")
        if git_executable is None:
            raise FileNotFoundError("Git executable not found")
        root = Path(
            subprocess.check_output(  # nosec B603 - controlled argv, no shell
                [git_executable, "rev-parse", "--show-toplevel"], cwd=cwd, text=True
            ).strip()
        ).resolve()

        # Only files in both HEAD and the index are eligible: staged removals
        # remain removed, and index-only additions never join the auto-commit.
        head_probe = subprocess.run(  # nosec B603 - fixed Git argv, no shell
            [git_executable, "rev-parse", "--verify", "--quiet", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        if head_probe.returncode == 0:
            head_files = (
                subprocess.check_output(  # nosec B603 - fixed Git argv
                    [git_executable, "ls-tree", "-r", "-z", "--name-only", "HEAD"], cwd=root
                )
                .decode("utf-8", errors="surrogateescape")
                .split("\0")
            )
        else:
            unborn = subprocess.run(  # nosec B603 - fixed Git argv
                [git_executable, "symbolic-ref", "--quiet", "HEAD"],
                cwd=root,
                capture_output=True,
                check=False,
            )
            if unborn.returncode != 0:
                raise subprocess.CalledProcessError(
                    head_probe.returncode,
                    [git_executable, "rev-parse", "HEAD"],
                    stderr=head_probe.stderr,
                )
            head_files = []

        index_files = set(
            subprocess.check_output(  # nosec B603 - fixed Git argv
                [git_executable, "ls-files", "--cached", "-z"], cwd=root
            )
            .decode("utf-8", errors="surrogateescape")
            .split("\0")
        )
        modified_paths = {Path(name).resolve() for name in fix_result.files_modified}
        scanned_files = {Path(v.file_path).resolve() for v in plan.violations}
        renames = [
            (Path(src).resolve(), Path(dst).resolve()) for src, dst in fix_result.path_renames
        ]
        # Eligibility is determined by original sources only, never final destinations.
        rename_sources = {source for source, _ in renames}
        content_sources = {
            Path(v.file_path).resolve()
            for v in plan.violations
            if v.violation_type not in (ViolationType.DIRECTORY_ALIAS, ViolationType.FILE_ALIAS)
            and Path(v.file_path).resolve() in modified_paths
        }

        paths_to_commit: set[str] = set()
        for name in head_files:
            if not name or name not in index_files:
                continue
            original = root / name
            if original not in content_sources and not any(
                original == source or original.is_relative_to(source) for source in rename_sources
            ):
                continue

            final = original
            for source, destination in renames:
                if final == source or final.is_relative_to(source):
                    final = destination / final.relative_to(source)

            # A previously deleted, unscanned descendant is outside this fix.
            # Do not stage that pre-existing deletion or treat it as a rename failure.
            if not final.is_file() and not final.is_symlink():
                if not final.exists() and original not in scanned_files:
                    continue
                raise ValueError(f"Tracked fix target is not a file: {final}")
            paths_to_commit.add(original.relative_to(root).as_posix())
            paths_to_commit.add(final.relative_to(root).as_posix())

        if not paths_to_commit:
            print("No tracked fixes to commit; untracked files remain untracked.")
            return EXIT_SUCCESS

        # NUL-delimited literal leaf pathspecs avoid shell globbing, path
        # ambiguity and OS argument-size limits on large directory renames.
        pathspecs = b"".join(
            f":(literal){name}".encode("utf-8", errors="surrogateescape") + b"\0"
            for name in sorted(paths_to_commit)
        )
        pathspec_args = ["--pathspec-from-file=-", "--pathspec-file-nul"]
        # Dry-run first: a rejected destination must not leave the index half staged.
        subprocess.run(  # nosec B603 - fixed Git argv and literal stdin
            [git_executable, "add", "--dry-run", "-A", *pathspec_args],
            input=pathspecs,
            check=True,
            cwd=root,
            capture_output=True,
        )
        subprocess.run(  # nosec B603 - fixed Git argv and literal stdin
            [git_executable, "add", "-A", *pathspec_args],
            input=pathspecs,
            check=True,
            cwd=root,
            capture_output=True,
        )
        # No-op fix: Git has no diff for these paths once staged. Do not make
        # an empty commit or treat this as a failed operation.
        index_changed = set(
            subprocess.check_output(  # nosec B603 - fixed Git argv, no shell
                [git_executable, "diff", "--cached", "--name-only", "-z", "HEAD"], cwd=root
            )
            .decode("utf-8", "surrogateescape")
            .split("\0")
        )
        if not (index_changed & paths_to_commit):
            print("No tracked differences remain after fixing.")
            return EXIT_SUCCESS

        # --only excludes unrelated user changes already staged in the index.
        subprocess.run(  # nosec B603 - fixed Git argv and literal stdin
            [git_executable, "commit", "--only", "-m", commit_msg, *pathspec_args],
            input=pathspecs,
            check=True,
            cwd=root,
            capture_output=True,
        )
        print("✅ Commit created successfully")
        return EXIT_SUCCESS
    except (subprocess.CalledProcessError, OSError, ValueError) as exc:
        print(f"❌ Git commit failed: {getattr(exc, 'stderr', None) or exc}", file=sys.stderr)
        return EXIT_EXECUTION_ERROR


def _preflight_commit_destinations(path: Path, plan: FixPlan, fixer: ConstitutionFixer) -> int:
    """Validate all tracked rename destinations before changing files or index.

    One canonical rename sequence is shared with the fixer and commit step.
    Only existing HEAD-and-index leaf sources are eligible for auto-commit.
    """
    git_executable = shutil.which("git")
    if git_executable is None:
        print("Git executable not found", file=sys.stderr)
        return EXIT_EXECUTION_ERROR
    cwd = path if path.is_dir() else path.parent
    try:
        root = Path(
            subprocess.check_output(  # nosec B603 - fixed Git argv, no shell
                [git_executable, "rev-parse", "--show-toplevel"], cwd=cwd, text=True
            ).strip()
        ).resolve()
        head_probe = subprocess.run(  # nosec B603 - fixed Git argv
            [git_executable, "rev-parse", "--verify", "--quiet", "HEAD"],
            cwd=root,
            capture_output=True,
            check=False,
        )
        if head_probe.returncode == 0:
            head_paths = set(
                subprocess.check_output(  # nosec B603 - fixed Git argv
                    [git_executable, "ls-tree", "-r", "-z", "--name-only", "HEAD"], cwd=root
                )
                .decode("utf-8", "surrogateescape")
                .split("\0")
            )
        else:
            unborn = subprocess.run(  # nosec B603 - fixed Git argv
                [git_executable, "symbolic-ref", "--quiet", "HEAD"],
                cwd=root,
                capture_output=True,
                check=False,
            )
            if unborn.returncode:
                print("Unable to inspect Git HEAD", file=sys.stderr)
                return EXIT_EXECUTION_ERROR
            head_paths = set()
        index_paths = set(
            subprocess.check_output(  # nosec B603 - fixed Git argv
                [git_executable, "ls-files", "--cached", "-z"], cwd=root
            )
            .decode("utf-8", "surrogateescape")
            .split("\0")
        )
        ordered_renames = fixer.planned_path_renames(plan)
        staged_paths = (
            set(
                subprocess.check_output(  # nosec B603 - fixed Git argv
                    [git_executable, "diff", "--cached", "--name-only", "-z", "HEAD"],
                    cwd=root,
                )
                .decode("utf-8", "surrogateescape")
                .split("\0")
            )
            if head_paths
            else index_paths
        )
        content_sources = {
            Path(v.file_path).absolute() for v in plan.violations if v.line is not None
        }
        # Never overwrite a staged change, even when the fix is a no-op.
        for staged_name in staged_paths:
            # git rm --cached leaves a local file deliberately untracked.
            # Its contents may be fixed without reintroducing it into Git.
            if staged_name not in index_paths:
                continue
            staged_path = root / staged_name
            if staged_path in content_sources or any(
                staged_path == src or staged_path.is_relative_to(src) for src, _ in ordered_renames
            ):
                print(
                    f"Refusing commit: staged changes in fix source: {staged_name}",
                    file=sys.stderr,
                )
                return EXIT_EXECUTION_ERROR

        # Ignore patterns edited by this same plan can alter path eligibility
        # after a rename. Manual staging is required for this ambiguous case.
        if ordered_renames and any(
            v.line is not None and Path(v.file_path).name == ".gitignore" for v in plan.violations
        ):
            print(
                "Refusing commit: plan edits .gitignore while renaming paths",
                file=sys.stderr,
            )
            return EXIT_EXECUTION_ERROR

        # A rename may otherwise commit unrelated unstaged edits from a
        # tracked leaf. Leave preexisting deletions alone (they are absent).
        unstaged_paths = set(
            subprocess.check_output(  # nosec B603 - fixed Git argv
                [git_executable, "diff", "--name-only", "-z"], cwd=root
            )
            .decode("utf-8", "surrogateescape")
            .split("\0")
        )
        for name in unstaged_paths:
            if name not in index_paths:
                continue
            leaf = root / name
            if not leaf.exists() and not leaf.is_symlink():
                continue
            if any(leaf == src or leaf.is_relative_to(src) for src, _ in ordered_renames):
                print(
                    f"Refusing commit: unstaged edits in rename source: {name}",
                    file=sys.stderr,
                )
                return EXIT_EXECUTION_ERROR
            if leaf in content_sources and name in head_paths:
                # Simulate reported fixes in a disposable file. If the result
                # differs from the index, other unstaged edits would be
                # swept into the commit. A restoration to HEAD is a safe no-op.
                violations = [
                    v
                    for v in plan.violations
                    if v.line is not None and Path(v.file_path).absolute() == leaf
                ]
                with tempfile.TemporaryDirectory(prefix="constitution-preflight-") as temp_dir:
                    candidate = Path(temp_dir) / "candidate.md"
                    shutil.copy2(leaf, candidate)
                    simulation = ConstitutionFixer(Path(temp_dir))
                    simulation._apply_content_fix(
                        candidate, violations, dry_run=False, interactive=False
                    )
                    indexed = subprocess.check_output(  # nosec B603 - fixed Git argv
                        [git_executable, "show", f":{name}"], cwd=root
                    )
                    if candidate.read_bytes() != indexed:
                        print(
                            f"Refusing commit: unrelated unstaged edits in content source: {name}",
                            file=sys.stderr,
                        )
                        return EXIT_EXECUTION_ERROR

        # HEAD paths also protect user-staged deletions of old destinations.
        occupied = head_paths | index_paths
        occupied_sorted = sorted(occupied)
        eligible = head_paths & index_paths
        destinations: set[str] = set()
        active_directory_sources: set[Path] = set()
        for original_name in eligible:
            if not original_name:
                continue
            original = root / original_name
            if not any(
                original == src or original.is_relative_to(src) for src, _ in ordered_renames
            ):
                continue
            # Previous unrelated deletions do not belong in this auto-commit.
            if not original.exists() and not original.is_symlink():
                continue
            if original.is_symlink() or not original.is_file():
                print(
                    f"Refusing commit: tracked rename source is not a regular file: {original}",
                    file=sys.stderr,
                )
                return EXIT_EXECUTION_ERROR

            for src, _ in ordered_renames:
                if src.is_dir() and original.is_relative_to(src):
                    active_directory_sources.add(src)
            final = original
            for src, dst in ordered_renames:
                if final == src or final.is_relative_to(src):
                    final = dst / final.relative_to(src)
            if final == original:
                continue
            try:
                final_name = final.relative_to(root).as_posix()
            except ValueError:
                print(f"Refusing commit: path escapes Git repository: {final}", file=sys.stderr)
                return EXIT_EXECUTION_ERROR
            # A staged addition or old tracked destination must never be overwritten,
            # even when absent from the working tree.
            ancestors = {
                "/".join(final_name.split("/")[:i]) for i in range(1, len(final_name.split("/")))
            }
            prefix = final_name + "/"
            descendant_index = bisect_left(occupied_sorted, prefix)
            descendant = descendant_index < len(occupied_sorted) and occupied_sorted[
                descendant_index
            ].startswith(prefix)
            if final_name in occupied or ancestors & occupied or descendant:
                print(
                    f"Refusing commit: rename destination collides with Git path: {final_name}",
                    file=sys.stderr,
                )
                return EXIT_EXECUTION_ERROR
            destinations.add(final_name)

        # Internal .gitignore rules move with a directory and can change
        # path eligibility after the rename. In auto-commit mode, fail closed.
        for directory in active_directory_sources:
            if any(p.is_file() for p in directory.rglob(".gitignore")):
                print(
                    f"Refusing commit: directory rename moves .gitignore: {directory}",
                    file=sys.stderr,
                )
                return EXIT_EXECUTION_ERROR

        if destinations:
            stdin_paths = b"".join(
                name.encode("utf-8", "surrogateescape") + b"\0" for name in sorted(destinations)
            )
            ignored = subprocess.run(  # nosec B603 - single batched read-only check
                [git_executable, "check-ignore", "--no-index", "--stdin", "-z"],
                input=stdin_paths,
                cwd=root,
                capture_output=True,
                check=False,
            )
            if ignored.returncode == 0:
                values = ignored.stdout.decode("utf-8", "surrogateescape")
                print(
                    f"Refusing commit: ignored rename destinations: {values!r}",
                    file=sys.stderr,
                )
                return EXIT_EXECUTION_ERROR
            if ignored.returncode != 1:
                print(f"Git ignore check failed: {ignored.stderr!r}", file=sys.stderr)
                return EXIT_EXECUTION_ERROR
    except (OSError, subprocess.CalledProcessError, ValueError, PathSecurityError) as exc:
        print(f"Commit preflight failed: {exc}", file=sys.stderr)
        return EXIT_EXECUTION_ERROR
    return EXIT_SUCCESS


@handle_scan_errors
def cmd_run_all(args: argparse.Namespace) -> int:
    """Execute complete workflow (scan, plan, fix, commit)."""
    if args.format != "text":
        print(
            "Error: run-all --format is not supported for non-text output.",
            file=sys.stderr,
        )
        return EXIT_VALIDATION_ERROR
    if Path(args.path).is_symlink():
        print(f"Refusing symlink input: {args.path}", file=sys.stderr)
        return EXIT_EXECUTION_ERROR
    path = validate_and_resolve_path(args.path)
    scanner = ConstitutionScanner()
    fixer = ConstitutionFixer(path)
    reporter = Reporter(use_color=not args.no_color)

    print("=== Constitution Linter: Full Workflow ===\n")

    # Step 1: Scan
    scan_result = _run_scan_step(path, scanner, reporter)
    if scan_result is None:
        return EXIT_SUCCESS
    result, _ = scan_result

    # Step 2: Plan
    plan = _run_plan_step(fixer, result, reporter)

    # Commit preflight must precede every content edit and path rename.
    if args.commit and not args.dry_run:
        preflight_code = _preflight_commit_destinations(path, plan, fixer)
        if preflight_code != EXIT_SUCCESS:
            return preflight_code

    # Step 3: Review (if interactive)
    if args.interactive:
        response = input("\nProceed with fixes? [y/N] ")
        if response.lower() != "y":
            print("Aborted.")
            return EXIT_SUCCESS

    # Step 4: Fix
    fix_result = _run_fix_step(fixer, plan, args, reporter)
    if not fix_result.success:
        return EXIT_EXECUTION_ERROR

    # Step 5: Commit (if requested)
    if args.commit and not args.dry_run:
        return _run_commit_step(path, plan, fix_result)

    return EXIT_SUCCESS


# =============================================================================
# ARGUMENT PARSING
# =============================================================================


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        prog="constitution-linter",
        description="Linter for Agentic Code Constitution violations (Law VII, Article 2)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan current directory
  constitution-linter scan

  # Scan with JSON output for CI
  constitution-linter scan --ci --format json

  # Preview fixes without applying
  constitution-linter fix --dry-run

  # Apply fixes with backup
  constitution-linter fix --backup

  # Full workflow with commit
  constitution-linter run-all --commit

Exit Codes:
  0 - Success (no violations)
  1 - Violations found
  2 - Dry run completed (violations would be fixed)
  3 - Validation error
  4 - Execution error
        """,
    )

    # Global options
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "table"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Scan command
    scan_parser = subparsers.add_parser("scan", help="Scan for violations")
    scan_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to scan (default: current directory)",
    )
    scan_parser.add_argument(
        "--ci",
        action="store_true",
        help="CI mode: exit with code 1 if violations found",
    )
    scan_parser.set_defaults(func=cmd_scan)

    # Plan command
    plan_parser = subparsers.add_parser("plan", help="Generate fix plan")
    plan_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to scan (default: current directory)",
    )
    plan_parser.add_argument(
        "--output",
        "-o",
        help="Save plan to JSON file",
    )
    plan_parser.add_argument(
        "--review",
        action="store_true",
        help="Mark all fixes as needing review",
    )
    plan_parser.set_defaults(func=cmd_plan)

    # Fix command
    fix_parser = subparsers.add_parser("fix", help="Apply fixes")
    fix_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to fix (default: current directory)",
    )
    fix_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying",
    )
    fix_parser.add_argument(
        "--backup",
        action="store_true",
        help="Create backup before modifying",
    )
    fix_parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Prompt for each fix",
    )
    fix_parser.set_defaults(func=cmd_fix)

    # Run-all command
    run_all_parser = subparsers.add_parser(
        "run-all", help="Run complete workflow (scan, plan, fix, commit)"
    )
    run_all_parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to process (default: current directory)",
    )
    run_all_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying",
    )
    run_all_parser.add_argument(
        "--backup",
        action="store_true",
        help="Create backup before modifying",
    )
    run_all_parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Prompt before applying fixes",
    )
    run_all_parser.add_argument(
        "--commit",
        action="store_true",
        help="Create git commit after fixes",
    )
    run_all_parser.set_defaults(func=cmd_run_all)

    # Match the documented CLI: output flags also work after a subcommand.
    for command_parser in (scan_parser, plan_parser, fix_parser, run_all_parser):
        command_parser.add_argument(
            "--format", choices=["text", "json", "table"], default=argparse.SUPPRESS
        )
        command_parser.add_argument("--no-color", action="store_true", default=argparse.SUPPRESS)
        command_parser.add_argument(
            "--verbose", "-v", action="store_true", default=argparse.SUPPRESS
        )

    return parser


def main(argv: list[str] | None = None) -> int:
    """
    Main entry point for CLI.

    Args:
        argv: Command-line arguments (default: sys.argv[1:])

    Returns:
        Exit code
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    # Setup logging
    if getattr(args, "verbose", False):
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)

    if args.command is None:
        parser.print_help()
        return EXIT_SUCCESS

    return cast("int", args.func(args))


__all__ = [
    "main",
    "create_parser",
    "cmd_scan",
    "cmd_plan",
    "cmd_fix",
    "cmd_run_all",
    "sanitize_commit_message",
    "validate_and_resolve_path",
    "EXIT_SUCCESS",
    "EXIT_VIOLATIONS_FOUND",
    "EXIT_DRY_RUN",
    "EXIT_VALIDATION_ERROR",
    "EXIT_EXECUTION_ERROR",
    "MAX_COMMIT_VIOLATIONS",
    "MAX_CONTEXT_LENGTH",
]
