"""
Constitution Linter Reporter.

Output formatting for scan results and fix plans.
NIT-002: Includes ASCII fallback for terminals without emoji support.
NIT-005: Includes type alias for JSON types.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Union

from .types import (
    FixPlan,
    FixResult,
    ScanResult,
    Severity,
    Violation,
)

# =============================================================================
# TYPE ALIAS (NIT-005)
# =============================================================================

# NIT-005: Proper type alias for JSON-compatible types
JsonType = Union["JsonDict", "JsonList", str, int, float, bool, None]
JsonDict = dict[str, JsonType]
JsonList = list[JsonType]


# =============================================================================
# JSON OUTPUT
# =============================================================================


def to_json(data: ScanResult | FixPlan | FixResult, indent: int = 2) -> str:
    """
    Convert result to JSON string.

    Args:
        data: Result object to convert
        indent: JSON indentation (default: 2)

    Returns:
        JSON string
    """
    return json.dumps(_to_dict(data), indent=indent, ensure_ascii=False)


def _to_dict(data: Any) -> Any:
    """NIT-005: Recursively convert dataclass to dict with proper typing."""
    if hasattr(data, "__dataclass_fields__"):
        return {k: _to_dict(v) for k, v in data.__dict__.items()}
    elif isinstance(data, tuple | list):
        return [_to_dict(item) for item in data]
    elif isinstance(data, Path):
        return str(data)
    elif hasattr(data, "value"):  # Enum
        return data.value
    return data


# =============================================================================
# ICON CONFIGURATION (NIT-002)
# =============================================================================

# Unicode icons (default)
SEVERITY_ICONS_UNICODE = {
    Severity.CRITICAL: "🔴",
    Severity.WARNING: "🟡",
    Severity.INFO: "🔵",
}

# ASCII fallback for terminals without emoji support (NIT-002)
SEVERITY_ICONS_ASCII = {
    Severity.CRITICAL: "[!]",
    Severity.WARNING: "[?]",
    Severity.INFO: "[i]",
}

STATUS_ICONS_UNICODE = {
    "success": "✅",
    "failure": "❌",
    "warning": "⚠️",
    "file": "📄",
}

STATUS_ICONS_ASCII = {
    "success": "[OK]",
    "failure": "[FAIL]",
    "warning": "[WARN]",
    "file": "[FILE]",
}

SEVERITY_COLORS = {
    Severity.CRITICAL: "\033[91m",  # Red
    Severity.WARNING: "\033[93m",  # Yellow
    Severity.INFO: "\033[94m",  # Blue
}
RESET_COLOR = "\033[0m"


def _get_icons(use_emoji: bool = True) -> tuple[dict, dict]:
    """
    NIT-002: Get appropriate icon sets based on emoji support.

    Returns:
        Tuple of (severity_icons, status_icons)
    """
    if use_emoji:
        return SEVERITY_ICONS_UNICODE, STATUS_ICONS_UNICODE
    return SEVERITY_ICONS_ASCII, STATUS_ICONS_ASCII


# =============================================================================
# HUMAN-READABLE OUTPUT
# =============================================================================


def format_scan_result(result: ScanResult, use_color: bool = True, use_emoji: bool = True) -> str:
    """
    Format scan result for terminal output.

    Args:
        result: Scan result to format
        use_color: Whether to use ANSI colors
        use_emoji: Whether to use emoji icons (NIT-002)

    Returns:
        Formatted string
    """
    lines: list[str] = []
    reset = RESET_COLOR if use_color else ""

    # NIT-002: Get appropriate icons
    severity_icons, status_icons = _get_icons(use_emoji)

    def colorize(severity: Severity, text: str) -> str:
        """Apply color to text if enabled."""
        if use_color and severity in SEVERITY_COLORS:
            return f"{SEVERITY_COLORS[severity]}{text}{reset}"
        return text

    # Header
    lines.append(f"\n{'=' * 60}")
    lines.append("Constitution Linter Scan Results")
    lines.append(f"{'=' * 60}")
    lines.append(f"Base path: {result.base_path}")
    lines.append(f"Files scanned: {result.files_scanned}")
    lines.append(f"Total violations: {result.total_violations}")
    lines.append("")

    # Summary by severity (NIT-002: use appropriate icons)
    lines.append("Summary:")
    lines.append(f"  {severity_icons[Severity.CRITICAL]} Critical: {result.critical_count}")
    lines.append(f"  {severity_icons[Severity.WARNING]} Warning: {result.warning_count}")
    lines.append(f"  {severity_icons[Severity.INFO]} Info: {result.info_count}")
    lines.append("")

    # Status
    if result.passed:
        status = f"{status_icons['success']} PASSED - No violations found"
    else:
        status = colorize(
            Severity.CRITICAL, f"{status_icons['failure']} FAILED - Violations detected"
        )
    lines.append(status)
    lines.append("")

    # Violations by file
    if result.file_results:
        lines.append(f"{'─' * 60}")
        lines.append("Violations by file:")
        lines.append(f"{'─' * 60}")

        for fr in result.file_results:
            if not fr.violations:
                continue

            lines.append(f"\n{status_icons['file']} {fr.file_path}")

            for v in fr.violations:
                icon = severity_icons.get(v.severity, "•")
                severity = colorize(v.severity, v.severity.value.upper())

                location = f"line {v.line}, col {v.column}" if v.line else "path"

                lines.append(f"  {icon} [{severity}] {location}")
                lines.append(f"      Rule: {v.pattern.rule_id}")
                lines.append(f'      Found: "{v.match}"')
                lines.append(f'      Suggestion: "{v.suggestion}"')

                if v.context:
                    lines.append(f"      Context: {v.context}")

    return "\n".join(lines)


def format_fix_plan(plan: FixPlan, use_emoji: bool = True) -> str:
    """
    Format fix plan for terminal output.

    Args:
        plan: Fix plan to format
        use_emoji: Whether to use emoji icons (NIT-002)

    Returns:
        Formatted string
    """
    lines: list[str] = []

    # NIT-002: Get appropriate icons
    _, status_icons = _get_icons(use_emoji)

    lines.append(f"\n{'=' * 60}")
    lines.append("Constitution Linter Fix Plan")
    lines.append(f"{'=' * 60}")
    lines.append(f"Created: {plan.created_at}")
    lines.append(f"Total fixes: {plan.total_fixes}")
    lines.append(f"  {status_icons['success']} Safe fixes: {plan.safe_fixes}")
    lines.append(f"  {status_icons['warning']} Needs review: {plan.needs_review}")
    lines.append("")

    if plan.backup_path:
        lines.append(f"Backup: {plan.backup_path}")

    # Group violations by file
    by_file: dict[str, list[Violation]] = {}
    for v in plan.violations:
        if v.file_path not in by_file:
            by_file[v.file_path] = []
        by_file[v.file_path].append(v)

    lines.append(f"{'─' * 60}")
    lines.append("Planned changes:")
    lines.append(f"{'─' * 60}")

    for file_path, violations in sorted(by_file.items()):
        lines.append(f"\n{status_icons['file']} {file_path}")

        for v in violations:
            icon = (
                SEVERITY_ICONS_UNICODE.get(v.severity, "•")
                if use_emoji
                else SEVERITY_ICONS_ASCII.get(v.severity, "*")
            )
            lines.append(f'  {icon} {v.pattern.rule_id}: "{v.match}" -> "{v.suggestion}"')

    return "\n".join(lines)


def format_fix_result(result: FixResult, use_emoji: bool = True) -> str:
    """
    Format fix result for terminal output.

    Args:
        result: Fix result to format
        use_emoji: Whether to use emoji icons (NIT-002)

    Returns:
        Formatted string
    """
    lines: list[str] = []

    # NIT-002: Get appropriate icons
    _, status_icons = _get_icons(use_emoji)

    lines.append(f"\n{'=' * 60}")
    lines.append("Constitution Linter Fix Results")
    lines.append(f"{'=' * 60}")

    if result.success:
        lines.append(f"{status_icons['success']} Fixes applied successfully")
    else:
        lines.append(f"{status_icons['failure']} Fixes failed")

    if result.error_message:
        lines.append(f"Error: {result.error_message}")

    lines.append(f"Files modified: {len(result.files_modified)}")

    for fp in result.files_modified:
        lines.append(f"  - {fp}")

    return "\n".join(lines)


# =============================================================================
# TABLE OUTPUT (for CI)
# =============================================================================


def format_table(result: ScanResult) -> str:
    """
    Format scan result as a table for CI output.

    Args:
        result: Scan result to format

    Returns:
        Table-formatted string
    """
    lines: list[str] = []

    # Header
    lines.append("| File | Line | Severity | Rule | Match | Suggestion |")
    lines.append("|------|------|----------|------|-------|------------|")

    for fr in result.file_results:
        for v in fr.violations:
            line = str(v.line) if v.line else "-"
            lines.append(
                f"| {Path(fr.file_path).name} | {line} | {v.severity.value} | "
                f"{v.pattern.rule_id} | `{v.match}` | `{v.suggestion}` |"
            )

    return "\n".join(lines)


# =============================================================================
# REPORT CLASS
# =============================================================================


class Reporter:
    """Generate reports in various formats."""

    def __init__(self, use_color: bool = True, use_emoji: bool = True) -> None:
        """
        Initialize reporter.

        Args:
            use_color: Whether to use ANSI colors in output
            use_emoji: Whether to use emoji icons (NIT-002)
        """
        self.use_color = use_color
        self.use_emoji = use_emoji

    def report_scan(self, result: ScanResult, format: str = "text") -> str:
        """
        Generate scan report.

        Args:
            result: Scan result
            format: Output format (text, json, table)

        Returns:
            Formatted report
        """
        if format == "json":
            return to_json(result)
        elif format == "table":
            return format_table(result)
        else:
            return format_scan_result(result, self.use_color, self.use_emoji)

    def report_plan(self, plan: FixPlan, format: str = "text") -> str:
        """
        Generate fix plan report.

        Args:
            plan: Fix plan
            format: Output format (text, json)

        Returns:
            Formatted report
        """
        if format == "json":
            return to_json(plan)
        else:
            return format_fix_plan(plan, self.use_emoji)

    def report_fix(self, result: FixResult, format: str = "text") -> str:
        """
        Generate fix result report.

        Args:
            result: Fix result
            format: Output format (text, json)

        Returns:
            Formatted report
        """
        if format == "json":
            return to_json(result)
        else:
            return format_fix_result(result, self.use_emoji)


__all__ = [
    "Reporter",
    "to_json",
    "format_scan_result",
    "format_fix_plan",
    "format_fix_result",
    "format_table",
    "JsonType",
    "JsonDict",
    "JsonList",
]
