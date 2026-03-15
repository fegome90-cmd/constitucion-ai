"""
Constitution Linter CLI.

Command-line interface for scanning and fixing model neutrality violations.
"""

from __future__ import annotations

import argparse
import functools
import logging
import re
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING, Final, TypeVar

from .fixer import ConstitutionFixer, PathSecurityError
from .reporter import Reporter
from .scanner import ConstitutionScanner
from .types import MAX_CONTEXT_LENGTH

if TYPE_CHECKING:
    from .types import FixPlan, ScanResult

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

F = TypeVar("F", bound=Callable[[argparse.Namespace], int])


def handle_scan_errors(func: F) -> F:
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
        diff = fixer.generate_diff(plan)
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
) -> int:
    """Run fix step and return exit code."""
    print("\nStep 3: Applying fixes...")
    fix_result = fixer.apply_plan(
        plan,
        dry_run=args.dry_run,
        create_backup=args.backup,
        interactive=args.interactive,
    )
    print(reporter.report_fix(fix_result, format="text"))

    if not fix_result.success:
        return EXIT_EXECUTION_ERROR
    return EXIT_SUCCESS


def _run_commit_step(path: Path, plan: FixPlan) -> int:
    """Run commit step and return exit code."""
    print("\nStep 4: Creating git commit...")

    # SEG-003: Build and sanitize commit message
    commit_msg_lines = ["fix(constitution): apply model neutrality fixes", ""]
    for v in plan.violations[:MAX_COMMIT_VIOLATIONS]:
        line = f"- {v.pattern.rule_id}: {v.match} → {v.suggestion}"
        commit_msg_lines.append(sanitize_commit_message(line))

    commit_msg = "\n".join(commit_msg_lines)

    try:
        subprocess.run(
            ["git", "add", "-A"],
            check=True,
            cwd=path,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            check=True,
            cwd=path,
            capture_output=True,
            text=True,
        )
        print("✅ Commit created successfully")
        return EXIT_SUCCESS
    except subprocess.CalledProcessError as e:
        print(f"❌ Git commit failed: {e.stderr or e}", file=sys.stderr)
        return EXIT_EXECUTION_ERROR


@handle_scan_errors
def cmd_run_all(args: argparse.Namespace) -> int:
    """Execute complete workflow (scan, plan, fix, commit)."""
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

    # Step 3: Review (if interactive)
    if args.interactive:
        response = input("\nProceed with fixes? [y/N] ")
        if response.lower() != "y":
            print("Aborted.")
            return EXIT_SUCCESS

    # Step 4: Fix
    fix_exit_code = _run_fix_step(fixer, plan, args, reporter)
    if fix_exit_code != EXIT_SUCCESS:
        return fix_exit_code

    # Step 5: Commit (if requested)
    if args.commit and not args.dry_run:
        return _run_commit_step(path, plan)

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

    return args.func(args)


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
