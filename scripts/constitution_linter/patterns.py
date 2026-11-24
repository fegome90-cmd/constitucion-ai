"""
Constitution Linter Patterns.

Pattern definitions for detecting violations of Law VII, Article 2
(Model Neutrality) of the Agentic Code Constitution.

F-002: Includes MatchScope for pattern matching context.
F-005: Includes case_sensitive flag (default: False).
F-008: Uses yaml.safe_load() for security.
SEG-004: Includes ReDoS validation for regex patterns.
"""

from __future__ import annotations

import re
import unicodedata
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

from typing import Final

import yaml

from .types import MatchScope, Pattern, Severity, ViolationType

# =============================================================================
# CONFIG ERROR
# =============================================================================


class ConfigError(Exception):
    """Error loading or parsing configuration."""

    pass


# =============================================================================
# REGEX VALIDATION (SEG-004)
# =============================================================================


def _validate_regex_safety(pattern: str) -> None:
    """
    Validate regex pattern for potential ReDoS vulnerabilities.

    SEG-004: Detects dangerous patterns like nested quantifiers.

    Args:
        pattern: Regex pattern to validate

    Raises:
        ConfigError: If pattern contains potentially dangerous constructs
    """
    # Check for adjacent quantifiers (e.g., a++, a**, a{1,3}{1,3})
    adjacent_quantifier_pattern = re.compile(r"([+*]|\{\d+,?\d*\})\s*([+*]|\{\d+,?\d*\})")
    if adjacent_quantifier_pattern.search(pattern):
        raise ConfigError(f"Potentially dangerous adjacent quantifiers in pattern: {pattern}")

    # Check for nested quantifiers in groups (e.g., (a+)+, (a*)+, (a{1,3})+)
    # Pattern: group with quantifier followed by quantifier
    nested_in_group = re.compile(r"\)[+*]|\)\{")
    if nested_in_group.search(pattern):
        raise ConfigError(f"Potentially dangerous nested quantifiers in pattern: {pattern}")

    # Check for excessive alternation (e.g., (a|b|c|d|e|f|g|h)+)
    if pattern.count("|") > 20:
        raise ConfigError(f"Excessive alternation in pattern (potential ReDoS): {pattern}")

    # Check for backtracking patterns
    backtracking_patterns = [
        r"\.\*\.\*",  # .*.*
        r"\.\+\.\+",  # .+.+
        r"\.\*\.\+",  # .*.+
        r"\.\+\.\*",  # .+.*
    ]
    for dangerous in backtracking_patterns:
        if re.search(dangerous, pattern):
            raise ConfigError(f"Potentially dangerous backtracking pattern: {pattern}")


# =============================================================================
# DEFAULT PATTERNS (Constitution Law VII, Article 2)
# =============================================================================

# Directory aliases that should be .ai/
DIRECTORY_ALIAS_PATTERNS: Final[list[dict[str, Any]]] = [
    {
        "pattern": r"\.claude[\\\/]",
        "suggestion": ".ai/",
        "severity": "critical",
        "rule_id": "DIR-001",
        "description": "Claude directory should be .ai/",
        "scope": "file_path",
    },
    {
        "pattern": r"\.cursor[\\\/]",
        "suggestion": ".ai/",
        "severity": "critical",
        "rule_id": "DIR-002",
        "description": "Cursor directory should be .ai/",
        "scope": "file_path",
    },
    {
        "pattern": r"\.copilot[\\\/]",
        "suggestion": ".ai/",
        "severity": "critical",
        "rule_id": "DIR-003",
        "description": "Copilot directory should be .ai/",
        "scope": "file_path",
    },
    {
        "pattern": r"\.gemini[\\\/]",
        "suggestion": ".ai/",
        "severity": "critical",
        "rule_id": "DIR-004",
        "description": "Gemini directory should be .ai/",
        "scope": "file_path",
    },
]

# File aliases that should use .ai* naming
FILE_ALIAS_PATTERNS: Final[list[dict[str, Any]]] = [
    {
        "pattern": r"\.cursorrules\b",
        "suggestion": ".airules",
        "severity": "critical",
        "rule_id": "FILE-001",
        "description": "Cursor rules file should be .airules",
        "scope": "file_path",
    },
    {
        "pattern": r"\.cursorignore\b",
        "suggestion": ".aiignore",
        "severity": "critical",
        "rule_id": "FILE-002",
        "description": "Cursor ignore file should be .aiignore",
        "scope": "file_path",
    },
    {
        "pattern": r"\.claudeignore\b",
        "suggestion": ".aiignore",
        "severity": "critical",
        "rule_id": "FILE-003",
        "description": "Claude ignore file should be .aiignore",
        "scope": "file_path",
    },
]

# Text references that violate neutrality
_CLAUDE_MODEL_PATTERN = r"[Cc]laude"
TEXT_REFERENCE_PATTERNS: Final[list[dict[str, Any]]] = [
    {
        # Detection stays separate from the shared contextual exemption.
        "pattern": _CLAUDE_MODEL_PATTERN,
        "suggestion": "AI",
        "severity": "critical",
        "rule_id": "TXT-001",
        "description": "Typo 'Claude' should be 'AI'",
        "scope": "file_content",
    },
    {
        "pattern": r"[Cc]ursor\s+rules?",
        "suggestion": "AI rules",
        "severity": "warning",
        "rule_id": "TXT-002",
        "description": "Reference to 'cursor rules' should be 'AI rules'",
        "scope": "file_content",
    },
    {
        "pattern": r"[Cc]laude\s+rules?",
        "suggestion": "AI rules",
        "severity": "warning",
        "rule_id": "TXT-003",
        "description": "Reference to 'Claude rules' should be 'AI rules'",
        "scope": "file_content",
    },
    {
        "pattern": r"[Gg]emini\s+rules?",
        "suggestion": "AI rules",
        "severity": "warning",
        "rule_id": "TXT-004",
        "description": "Reference to 'Gemini rules' should be 'AI rules'",
        "scope": "file_content",
    },
]


# =============================================================================
# PATTERN LOADING
# =============================================================================


def _parse_severity(value: str) -> Severity:
    """Parse severity string to enum."""
    mapping = {
        "critical": Severity.CRITICAL,
        "warning": Severity.WARNING,
        "info": Severity.INFO,
    }
    if value.lower() not in mapping:
        raise ConfigError(f"Invalid severity: {value}")
    return mapping[value.lower()]


def _parse_scope(value: str) -> MatchScope:
    """Parse scope string to enum."""
    mapping = {
        "file_path": MatchScope.FILE_PATH,
        "file_content": MatchScope.FILE_CONTENT,
        "both": MatchScope.BOTH,
    }
    if value.lower() not in mapping:
        raise ConfigError(f"Invalid scope: {value}")
    return mapping[value.lower()]


def _parse_pattern(data: dict[str, Any], *, builtin_canonical_reference: bool = False) -> Pattern:
    """
    Parse and validate a single pattern from config.

    SEG-004: Validates regex safety before creating pattern.
    """
    required = ["pattern", "suggestion", "severity", "rule_id"]
    for key in required:
        if key not in data:
            raise ConfigError(f"Missing required field: {key}")

    # SEG-004: Validate regex safety
    _validate_regex_safety(data["pattern"])

    return Pattern(
        pattern=data["pattern"],
        suggestion=data["suggestion"],
        severity=_parse_severity(data["severity"]),
        rule_id=data["rule_id"],
        description=data.get("description", ""),
        scope=_parse_scope(data.get("scope", "both")),
        case_sensitive=data.get("case_sensitive", False),
        builtin_canonical_reference=builtin_canonical_reference,
    )


def load_patterns_from_yaml(config_path: Path) -> list[Pattern]:
    """
    Load patterns from YAML config file.

    F-008: Uses yaml.safe_load() to prevent code execution.
    SEG-004: Validates regex safety for each pattern.
    """
    if not config_path.exists():
        raise ConfigError(f"Config file not found: {config_path}")

    # CRITICAL: Always use safe_load to prevent code execution
    with open(config_path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)  # NOT yaml.load()!

    # Validate schema
    if not isinstance(raw, dict):
        raise ConfigError("Config must be a dictionary")

    if "patterns" not in raw:
        raise ConfigError("Missing 'patterns' key")

    if not isinstance(raw["patterns"], list):
        raise ConfigError("'patterns' must be a list")

    return [_parse_pattern(p) for p in raw["patterns"]]


def get_default_patterns() -> list[Pattern]:
    """Get the default pattern set for model neutrality."""
    all_patterns = DIRECTORY_ALIAS_PATTERNS + FILE_ALIAS_PATTERNS + TEXT_REFERENCE_PATTERNS
    return [
        _parse_pattern(p, builtin_canonical_reference=p["rule_id"] == "TXT-001")
        for p in all_patterns
    ]


def get_violation_type(pattern: Pattern) -> ViolationType:
    """
    Determine violation type from pattern scope and rule_id.

    LOG-004: Properly handles MatchScope.BOTH based on rule_id prefix.
    """
    # LOG-004: Handle BOTH scope by examining rule_id prefix
    if pattern.scope in (MatchScope.FILE_PATH, MatchScope.BOTH):
        if pattern.rule_id.startswith("DIR-"):
            return ViolationType.DIRECTORY_ALIAS
        elif pattern.rule_id.startswith("FILE-"):
            return ViolationType.FILE_ALIAS

    if pattern.scope in (MatchScope.FILE_CONTENT, MatchScope.BOTH) and pattern.rule_id.startswith(
        "TXT-"
    ):
        if "typo" in pattern.description.lower():
            return ViolationType.TYPO
        return ViolationType.TEXT_REFERENCE

    # Default fallback
    return ViolationType.TEXT_REFERENCE


def compile_pattern(pattern: Pattern) -> re.Pattern[str]:
    """Compile detection regex; contextual exemptions are checked separately."""
    flags = 0
    if not pattern.case_sensitive:
        flags |= re.IGNORECASE
    return re.compile(pattern.pattern, flags)


_REFERENCE_WRAPPER = re.compile(r"\*{1,3}|_{1,3}|~{2}")
_LINE_REFERENCE = re.compile(r":\d+(?::\d+)?")
_QUERY_REFERENCE = re.compile(r"\?[A-Za-z0-9_.~-]+=")
_SENTENCE_PUNCTUATION = ".,;:!?"


def _is_opening_text_delimiter(char: str) -> bool:
    return (
        char.isspace() or char in {"'", '"', "`", "<"} or unicodedata.category(char) in {"Ps", "Pi"}
    )


def _is_closing_text_delimiter(char: str) -> bool:
    return (
        char.isspace() or char in {"'", '"', "`", ">"} or unicodedata.category(char) in {"Pe", "Pf"}
    )


def _is_text_end(line: str, index: int) -> bool:
    return index == len(line) or _is_closing_text_delimiter(line[index])


def _reference_end(line: str, index: int) -> bool:
    """Recognize a complete component, reference suffix or end of prose."""
    if (
        _is_text_end(line, index)
        or line[index] in "/\\#"
        or _QUERY_REFERENCE.match(line, index) is not None
    ):
        return True
    number = _LINE_REFERENCE.match(line, index)
    if number is not None:
        index = number.end()
        if _is_text_end(line, index):
            return True
    return line[index] in _SENTENCE_PUNCTUATION and _is_text_end(line, index + 1)


def _delimited_reference(line: str, start: int, end: int) -> bool:
    left = start == 0 or _is_opening_text_delimiter(line[start - 1]) or line[start - 1] in "/\\"
    return left and _reference_end(line, end)


def _formatting_end(line: str, index: int, outer: list[re.Match[str]]) -> bool:
    """Accept adjacent closing markers only when their full chain is delimited."""
    for opener in reversed(outer):
        if not line.startswith(opener.group(), index):
            break
        index += len(opener.group())
    return _is_text_end(line, index) or (
        line[index] in _SENTENCE_PUNCTUATION and _is_text_end(line, index + 1)
    )


def _wrapped_reference(line: str, start: int, end: int) -> bool:
    """Recognize balanced formatting around a token or a phrase.

    An unmatched marker or a marker inside a compound filename does not
    qualify as a delimiter. Check the same component grammar inside the pair.
    """
    suffix = end
    number = _LINE_REFERENCE.match(line, suffix)
    if number is not None:
        suffix = number.end()
    if suffix < len(line) and line[suffix] in _SENTENCE_PUNCTUATION:
        suffix += 1
    if not (
        (start > 0 and line[start - 1] in "*_~") or (suffix < len(line) and line[suffix] in "*_~")
    ):
        return False
    stack: list[re.Match[str]] = []
    for marker in _REFERENCE_WRAPPER.finditer(line):
        left, right = marker.span()
        opens = (
            (
                left == 0
                or _is_opening_text_delimiter(line[left - 1])
                or (stack and stack[-1].end() == left)
            )
            and right < len(line)
            and not line[right].isspace()
        )
        closes = (
            left > 0
            and not line[left - 1].isspace()
            and bool(stack)
            and stack[-1].group() == marker.group()
            and _formatting_end(line, right, stack[:-1])
        )
        if closes:
            opener = stack.pop()
            if opener.end() <= start and end <= left:
                inner = line[opener.end() : left]
                if _delimited_reference(inner, start - opener.end(), end - opener.end()):
                    return True
        elif opens:
            stack.append(marker)
    return False


def is_protected_content_match(pattern: Pattern, match: re.Match[str]) -> bool:
    """Preserve only the built-in governance filename reference, not custom rules.

    Scanner and fixer use this same predicate, including stale-plan checks.
    The grammar is for text references, not arbitrary filesystem name syntax.
    """
    if not pattern.builtin_canonical_reference:
        return False
    line = match.string
    start = match.start()
    end = match.end() + len(".md")
    if line[match.end() : end].casefold() != ".md":
        return False
    return _delimited_reference(line, start, end) or _wrapped_reference(line, start, end)


def validate_pattern(pattern: Pattern) -> None:
    """
    Validate a Pattern object for safety.

    SEG-004: Call this when creating Pattern objects directly.
    Note: Patterns loaded via get_default_patterns() or load_patterns_from_yaml()
    are already validated.

    Args:
        pattern: Pattern to validate

    Raises:
        ConfigError: If pattern contains dangerous constructs
    """
    _validate_regex_safety(pattern.pattern)


__all__ = [
    "ConfigError",
    "load_patterns_from_yaml",
    "get_default_patterns",
    "get_violation_type",
    "compile_pattern",
    "is_protected_content_match",
    "validate_pattern",
    "DIRECTORY_ALIAS_PATTERNS",
    "FILE_ALIAS_PATTERNS",
    "TEXT_REFERENCE_PATTERNS",
]
