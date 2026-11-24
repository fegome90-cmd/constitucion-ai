"""
Constitution Linter.

Detects and fixes violations of Law VII, Article 2 (Model Neutrality)
of the Agentic Code Constitution.

Usage:
    from constitution_linter import scan

    result = scan(Path("./docs"))
    print(f"Found {result.total_violations} violations")
"""

from __future__ import annotations

# Import fixer (depends on types, patterns)
from .fixer import ConstitutionFixer

# Import patterns (depends on types)
from .patterns import (
    ConfigError,
    compile_pattern,
    get_default_patterns,
    get_violation_type,
    load_patterns_from_yaml,
    validate_pattern,
)

# Import reporter (depends on types)
from .reporter import Reporter

# Import scanner (depends on types, patterns)
from .scanner import ConstitutionScanner, scan

# Import types first (no dependencies)
from .types import (
    FileResult,
    FixPlan,
    FixResult,
    MatchScope,
    Pattern,
    ScanResult,
    Severity,
    Violation,
    ViolationType,
)

__version__ = "1.0.0"

__all__ = [
    # Main API
    "scan",
    "ConstitutionScanner",
    "ConstitutionFixer",
    "Reporter",
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
    # Pattern utilities
    "get_default_patterns",
    "compile_pattern",
    "get_violation_type",
    "load_patterns_from_yaml",
    "validate_pattern",
    "ConfigError",
]
