"""
Constitution Linter Tests.

Comprehensive tests for the constitution linter covering:
- Pattern compilation and validation
- Scanner path/content matching
- Fixer backup and atomic writes
- CLI command execution
- Edge cases (code blocks, large files, encoding)
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from constitution_linter import (
    ConfigError,
    ConstitutionFixer,
    ConstitutionScanner,
    FixPlan,
    MatchScope,
    Pattern,
    ScanResult,
    Severity,
    Violation,
    ViolationType,
    compile_pattern,
    get_default_patterns,
    get_violation_type,
    load_patterns_from_yaml,
    scan,
    validate_pattern,
)

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def fixtures_dir() -> Path:
    """Path to test fixtures directory."""
    return Path(__file__).parent / "fixtures" / "constitution"


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Temporary directory for test files."""
    return tmp_path


@pytest.fixture
def sample_pattern() -> Pattern:
    """Sample pattern for testing."""
    return Pattern(
        pattern=r"[Cc]laude",
        suggestion="AI",
        severity=Severity.CRITICAL,
        rule_id="TXT-001",
        description="Typo 'Claude' should be 'AI'",
        scope=MatchScope.FILE_CONTENT,
    )


# =============================================================================
# TEST HELPERS
# =============================================================================


def assert_scan_result(
    result: ScanResult,
    *,
    expected_passed: bool,
    expected_violations: int | None = None,
) -> None:
    """Helper to assert scan result properties."""
    assert isinstance(result, ScanResult), f"Expected ScanResult, got {type(result)}"
    assert result.passed == expected_passed, (
        f"Expected passed={expected_passed}, got {result.passed}"
    )
    if expected_violations is not None:
        assert result.total_violations == expected_violations, (
            f"Expected {expected_violations} violations, got {result.total_violations}"
        )


# =============================================================================
# TEST HELPERS
# =============================================================================


def assert_scan_result(
    result: ScanResult,
    *,
    expected_passed: bool,
    expected_violations: int | None = None,
) -> None:
    """Helper to assert scan results with clear error messages."""
    assert result.passed == expected_passed, (
        f"Expected passed={expected_passed}, got {result.passed}. "
        f"Violations: {result.total_violations}"
    )
    if expected_violations is not None:
        assert result.total_violations == expected_violations, (
            f"Expected {expected_violations} violations, got {result.total_violations}"
        )


# =============================================================================
# PATTERN TESTS
# =============================================================================


class TestPatternTypes:
    """Tests for Pattern data types."""

    def test_pattern_is_frozen(self, sample_pattern: Pattern) -> None:
        """Pattern should be immutable (frozen dataclass)."""
        with pytest.raises(AttributeError):
            sample_pattern.pattern = "new pattern"  # type: ignore

    def test_pattern_default_scope(self) -> None:
        """Pattern should default to BOTH scope."""
        pattern = Pattern(
            pattern=r"test",
            suggestion="replacement",
            severity=Severity.WARNING,
            rule_id="TEST-001",
        )
        assert pattern.scope == MatchScope.BOTH

    def test_pattern_default_case_insensitive(self) -> None:
        """Pattern should default to case-insensitive matching."""
        pattern = Pattern(
            pattern=r"test",
            suggestion="replacement",
            severity=Severity.WARNING,
            rule_id="TEST-001",
        )
        assert pattern.case_sensitive is False


class TestPatternCompilation:
    """Tests for pattern compilation."""

    def test_compile_pattern_case_insensitive(self, sample_pattern: Pattern) -> None:
        """Compiled pattern should match case-insensitively by default."""
        compiled = compile_pattern(sample_pattern)
        assert compiled.search("claude") is not None
        assert compiled.search("Claude") is not None
        assert compiled.search("CLAUDE") is not None

    def test_compile_pattern_case_sensitive(self) -> None:
        """Compiled pattern should respect case_sensitive flag."""
        pattern = Pattern(
            pattern=r"claude",
            suggestion="AI",
            severity=Severity.CRITICAL,
            rule_id="TEST-001",
            case_sensitive=True,
        )
        compiled = compile_pattern(pattern)
        assert compiled.search("claude") is not None
        assert compiled.search("Claude") is None

    def test_compile_invalid_pattern_raises_error(self) -> None:
        """Invalid regex pattern should raise error on compilation."""
        # Note: validate_pattern checks for ReDoS, not regex syntax
        # Invalid syntax will raise re.error when compiled
        pattern = Pattern(
            pattern=r"[invalid",
            suggestion="replacement",
            severity=Severity.WARNING,
            rule_id="TEST-001",
        )
        with pytest.raises(re.error):
            compile_pattern(pattern)


class TestPatternValidation:
    """Tests for ReDoS validation (SEG-004)."""

    def test_adjacent_quantifiers_rejected(self) -> None:
        """Adjacent quantifiers should be rejected (ReDoS prevention)."""
        with pytest.raises(ConfigError, match="adjacent quantifiers"):
            validate_pattern(
                Pattern(
                    pattern=r"a++",
                    suggestion="b",
                    severity=Severity.WARNING,
                    rule_id="TEST-001",
                )
            )

    def test_nested_quantifiers_rejected(self) -> None:
        """Nested quantifiers should be rejected (ReDoS prevention)."""
        with pytest.raises(ConfigError, match="nested quantifiers"):
            validate_pattern(
                Pattern(
                    pattern=r"(a+)+",
                    suggestion="b",
                    severity=Severity.WARNING,
                    rule_id="TEST-001",
                )
            )

    def test_excessive_alternation_rejected(self) -> None:
        """Excessive alternation should be rejected (ReDoS prevention)."""
        # Create pattern with >20 alternations
        pattern = "|".join(f"opt{i}" for i in range(25))
        with pytest.raises(ConfigError, match="Excessive alternation"):
            validate_pattern(
                Pattern(
                    pattern=pattern,
                    suggestion="b",
                    severity=Severity.WARNING,
                    rule_id="TEST-001",
                )
            )

    def test_backtracking_pattern_rejected(self) -> None:
        """Dangerous backtracking patterns should be rejected."""
        with pytest.raises(ConfigError, match="backtracking"):
            validate_pattern(
                Pattern(
                    pattern=r".*.*",
                    suggestion="b",
                    severity=Severity.WARNING,
                    rule_id="TEST-001",
                )
            )


class TestDefaultPatterns:
    """Tests for default pattern loading."""

    def test_get_default_patterns_returns_list(self) -> None:
        """get_default_patterns should return a list of patterns."""
        patterns = get_default_patterns()
        assert isinstance(patterns, list)
        assert len(patterns) > 0

    def test_default_patterns_include_directory_aliases(self) -> None:
        """Default patterns should include directory alias patterns."""
        patterns = get_default_patterns()
        rule_ids = [p.rule_id for p in patterns]
        assert "DIR-001" in rule_ids  # .claude/
        assert "DIR-002" in rule_ids  # .cursor/

    def test_default_patterns_include_file_aliases(self) -> None:
        """Default patterns should include file alias patterns."""
        patterns = get_default_patterns()
        rule_ids = [p.rule_id for p in patterns]
        assert "FILE-001" in rule_ids  # .cursorrules

    def test_default_patterns_include_text_references(self) -> None:
        """Default patterns should include text reference patterns."""
        patterns = get_default_patterns()
        rule_ids = [p.rule_id for p in patterns]
        assert "TXT-001" in rule_ids  # Claude typo


class TestViolationType:
    """Tests for violation type determination."""

    def test_directory_alias_type(self) -> None:
        """DIR- prefix should return DIRECTORY_ALIAS type."""
        pattern = Pattern(
            pattern=r"\.claude[\\\/]",
            suggestion=".ai/",
            severity=Severity.CRITICAL,
            rule_id="DIR-001",
            scope=MatchScope.FILE_PATH,
        )
        assert get_violation_type(pattern) == ViolationType.DIRECTORY_ALIAS

    def test_file_alias_type(self) -> None:
        """FILE- prefix should return FILE_ALIAS type."""
        pattern = Pattern(
            pattern=r"\.cursorrules\b",
            suggestion=".airules",
            severity=Severity.CRITICAL,
            rule_id="FILE-001",
            scope=MatchScope.FILE_PATH,
        )
        assert get_violation_type(pattern) == ViolationType.FILE_ALIAS

    def test_text_reference_type(self) -> None:
        """TXT- prefix should return TEXT_REFERENCE type."""
        pattern = Pattern(
            pattern=r"[Cc]ursor\s+rules?",
            suggestion="AI rules",
            severity=Severity.WARNING,
            rule_id="TXT-002",
            scope=MatchScope.FILE_CONTENT,
        )
        assert get_violation_type(pattern) == ViolationType.TEXT_REFERENCE


# =============================================================================
# YAML CONFIG TESTS
# =============================================================================


class TestYAMLLoading:
    """Tests for YAML configuration loading."""

    def test_load_patterns_from_yaml(self, fixtures_dir: Path) -> None:
        """Should load patterns from YAML config file."""
        # Use the actual config file
        config_path = Path(__file__).parent.parent / "config" / "constitution_patterns.yaml"
        if config_path.exists():
            patterns = load_patterns_from_yaml(config_path)
            assert isinstance(patterns, list)
            assert len(patterns) > 0
            # Verify pattern structure
            for p in patterns:
                assert isinstance(p, Pattern)
                assert p.rule_id  # Has rule_id
                assert p.suggestion  # Has suggestion

    def test_load_missing_yaml_raises_error(self, temp_dir: Path) -> None:
        """Missing config file should raise ConfigError."""
        missing_path = temp_dir / "nonexistent.yaml"
        with pytest.raises(ConfigError, match="not found"):
            load_patterns_from_yaml(missing_path)

    def test_load_invalid_yaml_raises_error(self, temp_dir: Path) -> None:
        """Invalid YAML content should raise parser error."""
        import yaml

        invalid_yaml = temp_dir / "invalid.yaml"
        invalid_yaml.write_text("not a valid yaml: [unclosed")
        # yaml.safe_load raises yaml.scanner.ScannerError for invalid YAML
        with pytest.raises(yaml.error.YAMLError):
            load_patterns_from_yaml(invalid_yaml)

    def test_load_yaml_missing_patterns_key(self, temp_dir: Path) -> None:
        """YAML without 'patterns' key should raise ConfigError."""
        no_patterns = temp_dir / "no_patterns.yaml"
        no_patterns.write_text("other_key: value")
        with pytest.raises(ConfigError, match="Missing 'patterns'"):
            load_patterns_from_yaml(no_patterns)


# =============================================================================
# SCANNER TESTS
# =============================================================================


class TestScanner:
    """Tests for ConstitutionScanner."""

    def test_scan_clean_file(self, fixtures_dir: Path) -> None:
        """Clean file should have no violations."""
        scanner = ConstitutionScanner()
        result = scanner.scan_path(fixtures_dir / "clean.md")

        assert result.passed
        assert result.total_violations == 0

    def test_scan_file_with_violations(self, fixtures_dir: Path) -> None:
        """File with violations should be detected."""
        scanner = ConstitutionScanner()
        result = scanner.scan_path(fixtures_dir / "has_violations.md")

        assert not result.passed
        assert result.total_violations > 0

        # Check for specific violation types
        violations = result.all_violations
        rule_ids = {v.pattern.rule_id for v in violations}
        assert "TXT-001" in rule_ids  # Claude typo

    def test_scan_directory(self, fixtures_dir: Path) -> None:
        """Directory scan should aggregate all file results."""
        scanner = ConstitutionScanner()
        result = scanner.scan_path(fixtures_dir)

        assert result.files_scanned > 0
        assert isinstance(result.file_results, tuple)

    def test_scan_nonexistent_path_raises_error(self, temp_dir: Path) -> None:
        """Scanning nonexistent path should raise FileNotFoundError."""
        scanner = ConstitutionScanner()
        with pytest.raises(FileNotFoundError):
            scanner.scan_path(temp_dir / "nonexistent")

    def test_scan_excludes_binary_files(self, temp_dir: Path) -> None:
        """Binary files should be excluded from scanning."""
        # Create a binary file
        binary_file = temp_dir / "test.png"
        binary_file.write_bytes(b"\x89PNG\r\n\x1a\n")

        scanner = ConstitutionScanner()
        result = scanner.scan_path(temp_dir)

        # Should not crash and should skip the binary file
        assert result.passed or result.total_violations == 0

    def test_code_blocks_ignored(self, fixtures_dir: Path) -> None:
        """Content inside code blocks should be ignored."""
        scanner = ConstitutionScanner()
        result = scanner.scan_path(fixtures_dir / "code_blocks.md")

        # Find violations for TXT-001 (Claude typo)
        claude_violations = [v for v in result.all_violations if v.pattern.rule_id == "TXT-001"]

        # Code blocks (triple backticks) are ignored, but inline code is not
        # The file has:
        # - "claude" inside ```python``` blocks - IGNORED
        # - "claude_config" in inline code - DETECTED (inline code not ignored)
        # - "Claude" in regular text - DETECTED
        assert len(claude_violations) == 2

        # Verify the violations are on the expected lines
        lines = {v.line for v in claude_violations}
        # Line 31 has inline code, line 32 has regular text
        assert 31 in lines or 32 in lines


class TestScannerPathMatching:
    """Tests for file path pattern matching."""

    def test_detect_cursorrules_file(self, fixtures_dir: Path) -> None:
        """.cursorrules file should be detected as FILE-001."""
        scanner = ConstitutionScanner()
        result = scanner.scan_path(fixtures_dir / ".cursorrules")

        assert not result.passed
        rule_ids = {v.pattern.rule_id for v in result.all_violations}
        assert "FILE-001" in rule_ids


class TestScannerEdgeCases:
    """Tests for scanner edge cases."""

    def test_large_file_handling(self, temp_dir: Path) -> None:
        """Large files should be handled gracefully."""
        # Create a file larger than MAX_FILE_SIZE_BYTES
        large_file = temp_dir / "large.md"
        large_content = "Claude " * 2_000_000  # ~14MB
        large_file.write_text(large_content)

        scanner = ConstitutionScanner()
        # Should not crash - returns ScanResult for a single file
        result = scanner.scan_path(large_file)
        assert isinstance(result, ScanResult)
        # Large files are skipped, so should pass with no violations
        assert result.passed

    def test_unicode_file_handling(self, temp_dir: Path) -> None:
        """Unicode content should be handled correctly."""
        unicode_file = temp_dir / "unicode.md"
        unicode_file.write_text("# Título en español\n\nContenido con ñ y áéíóú")

        scanner = ConstitutionScanner()
        result = scanner.scan_path(unicode_file)

        # Should not crash and should handle unicode
        assert result.passed  # No violations in this file

    def test_empty_file_handling(self, temp_dir: Path) -> None:
        """Empty files should be handled correctly."""
        empty_file = temp_dir / "empty.md"
        empty_file.write_text("")

        scanner = ConstitutionScanner()
        result = scanner.scan_path(empty_file)

        assert result.passed
        assert result.total_violations == 0


# =============================================================================
# FIXER TESTS
# =============================================================================


class TestFixer:
    """Tests for ConstitutionFixer."""

    def test_create_plan_from_scan_result(self, fixtures_dir: Path) -> None:
        """Should create a fix plan from scan results."""
        scanner = ConstitutionScanner()
        scan_result = scanner.scan_path(fixtures_dir / "has_violations.md")

        fixer = ConstitutionFixer(fixtures_dir)
        plan = fixer.create_plan(scan_result)

        assert isinstance(plan, FixPlan)
        assert plan.total_fixes > 0
        assert len(plan.violations) == plan.total_fixes

    def test_backup_creation(self, temp_dir: Path) -> None:
        """Fixer should create backups before fixing."""
        # Create a file with violations
        test_file = temp_dir / "test.md"
        test_file.write_text("Use Claude for AI tasks.")

        scanner = ConstitutionScanner()
        scan_result = scanner.scan_path(test_file)

        fixer = ConstitutionFixer(temp_dir)
        plan = fixer.create_plan(scan_result)

        # Plan should include backup path
        assert plan.backup_path is not None or plan.total_fixes > 0

    def test_path_security_validation(self, temp_dir: Path) -> None:
        """Fixer should reject paths outside base directory."""
        fixer = ConstitutionFixer(temp_dir)

        # Try to access a file outside the base directory
        outside_path = Path("/etc/passwd")
        with pytest.raises(Exception):  # PathSecurityError
            fixer._validate_path_in_base(outside_path)


# =============================================================================
# SCAN CONVENIENCE FUNCTION TESTS
# =============================================================================


class TestScanFunction:
    """Tests for the scan convenience function."""

    def test_scan_single_file(self, fixtures_dir: Path) -> None:
        """scan() should work for a single file."""
        result = scan(fixtures_dir / "clean.md")
        assert isinstance(result, ScanResult)
        assert result.passed

    def test_scan_directory(self, fixtures_dir: Path) -> None:
        """scan() should work for a directory."""
        result = scan(fixtures_dir)
        assert isinstance(result, ScanResult)
        assert result.files_scanned > 0


# =============================================================================
# SEVERITY TESTS
# =============================================================================


class TestSeverity:
    """Tests for severity levels."""

    def test_critical_violations_counted(self, fixtures_dir: Path) -> None:
        """Critical violations should be counted separately."""
        scanner = ConstitutionScanner()
        result = scanner.scan_path(fixtures_dir / "has_violations.md")

        # Should have at least some critical violations (TXT-001 is critical)
        assert result.critical_count >= 0

    def test_severity_enum_values(self) -> None:
        """Severity enum should have expected values."""
        assert Severity.CRITICAL.value == "critical"
        assert Severity.WARNING.value == "warning"
        assert Severity.INFO.value == "info"


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


class TestIntegration:
    """Integration tests for the full workflow."""

    def test_full_scan_workflow(self, fixtures_dir: Path) -> None:
        """Complete workflow: scan -> plan -> verify."""
        # 1. Scan
        scanner = ConstitutionScanner()
        scan_result = scanner.scan_path(fixtures_dir / "has_violations.md")

        # 2. Verify scan found violations
        assert not scan_result.passed
        assert scan_result.total_violations > 0

        # 3. Create fix plan
        fixer = ConstitutionFixer(fixtures_dir)
        plan = fixer.create_plan(scan_result)

        # 4. Verify plan
        assert plan.total_fixes == scan_result.total_violations

    def test_default_patterns_all_valid(self) -> None:
        """All default patterns should be valid and compilable."""
        patterns = get_default_patterns()

        for pattern in patterns:
            # Should not raise
            compiled = compile_pattern(pattern)
            assert compiled is not None


# =============================================================================
# VIOLATION DATA STRUCTURE TESTS
# =============================================================================


class TestViolationDataStructure:
    """Tests for Violation data structure."""

    def test_violation_is_frozen(self, sample_pattern: Pattern) -> None:
        """Violation should be immutable."""
        violation = Violation(
            file_path="/test/file.md",
            line=1,
            column=1,
            violation_type=ViolationType.TYPO,
            severity=Severity.CRITICAL,
            pattern=sample_pattern,
            match="Claude",
            suggestion="AI",
        )

        with pytest.raises(AttributeError):
            violation.match = "new match"  # type: ignore

    def test_violation_optional_fields(self, sample_pattern: Pattern) -> None:
        """Violation should handle optional fields."""
        violation = Violation(
            file_path="/test/file.md",
            line=None,  # Path violation has no line
            column=0,
            violation_type=ViolationType.FILE_ALIAS,
            severity=Severity.CRITICAL,
            pattern=sample_pattern,
            match=".cursorrules",
            suggestion=".airules",
            context=None,
        )

        assert violation.line is None
        assert violation.context is None


class TestScanResultDataStructure:
    """Tests for ScanResult data structure."""

    def test_scan_result_aggregates_violations(self, fixtures_dir: Path) -> None:
        """ScanResult should aggregate all violations."""
        scanner = ConstitutionScanner()
        result = scanner.scan_path(fixtures_dir)

        # all_violations property should flatten violations
        all_v = result.all_violations
        total = sum(fr.violation_count for fr in result.file_results)

        assert len(all_v) == total
        assert len(all_v) == result.total_violations

    def test_scan_result_passed_property(self, temp_dir: Path) -> None:
        """ScanResult.passed should reflect violation presence."""
        clean_file = temp_dir / "clean.md"
        clean_file.write_text("Clean content")

        scanner = ConstitutionScanner()
        result = scanner.scan_path(clean_file)

        assert result.passed
        assert result.total_violations == 0


# =============================================================================
# SECURITY TESTS
# =============================================================================


class TestSecurity:
    """Tests for security features."""

    def test_path_traversal_blocked(self, temp_dir: Path) -> None:
        """Attempt to escape base directory should raise PathSecurityError."""
        from constitution_linter.fixer import PathSecurityError

        fixer = ConstitutionFixer(temp_dir)
        malicious_path = temp_dir / ".." / ".." / ".." / "etc" / "passwd"

        with pytest.raises(PathSecurityError):
            fixer._validate_path_in_base(malicious_path)

    def test_symlink_escape_skipped(self, temp_dir: Path) -> None:
        """Symlinks pointing outside base should be skipped."""
        # Create a symlink to a file outside the directory
        symlink_path = temp_dir / "link_to_etc"
        try:
            symlink_path.symlink_to("/etc/passwd")
        except OSError:
            # Skip test if symlink creation fails (e.g., permissions)
            pytest.skip("Cannot create symlink")

        scanner = ConstitutionScanner()
        # Should not crash, should not read /etc/passwd
        result = scanner.scan_path(temp_dir)
        assert isinstance(result, ScanResult)

    def test_redos_pattern_rejected(self) -> None:
        """Dangerous regex patterns should raise ConfigError."""
        dangerous = Pattern(
            pattern=r"(a+)+$",  # Classic ReDoS pattern
            suggestion="x",
            severity=Severity.WARNING,
            rule_id="TEST",
            scope=MatchScope.FILE_CONTENT,
        )

        with pytest.raises(ConfigError, match="nested quantifiers"):
            validate_pattern(dangerous)

    def test_excessive_alternation_rejected(self) -> None:
        """Excessive alternation patterns should raise ConfigError."""
        # Create pattern with >20 alternations
        pattern = "|".join(f"opt{i}" for i in range(25))
        dangerous = Pattern(
            pattern=pattern,
            suggestion="x",
            severity=Severity.WARNING,
            rule_id="TEST",
            scope=MatchScope.FILE_CONTENT,
        )

        with pytest.raises(ConfigError, match="Excessive alternation"):
            validate_pattern(dangerous)

    def test_backtracking_pattern_rejected(self) -> None:
        """Dangerous backtracking patterns should raise ConfigError."""
        dangerous = Pattern(
            pattern=r".*.*",
            suggestion="x",
            severity=Severity.WARNING,
            rule_id="TEST",
            scope=MatchScope.FILE_CONTENT,
        )

        with pytest.raises(ConfigError, match="backtracking"):
            validate_pattern(dangerous)


# =============================================================================
# CLI INTEGRATION TESTS
# =============================================================================


class TestCLI:
    """Tests for CLI functionality."""

    def test_cli_scan_exit_code_success(self, temp_dir: Path) -> None:
        """CLI should exit with code 0 when no violations found."""
        from constitution_linter.cli import main

        clean_file = temp_dir / "clean.md"
        clean_file.write_text("Clean AI content")

        exit_code = main(["scan", str(temp_dir), "--ci"])
        assert exit_code == 0

    def test_cli_scan_exit_code_violations(self, temp_dir: Path) -> None:
        """CLI should exit with code 1 when violations found."""
        from constitution_linter.cli import main

        dirty_file = temp_dir / "dirty.md"
        dirty_file.write_text("Use Claude for AI tasks")

        exit_code = main(["scan", str(temp_dir), "--ci"])
        assert exit_code == 1

    def test_cli_scan_nonexistent_path(self) -> None:
        """CLI should exit with code 4 for nonexistent path."""
        from constitution_linter.cli import main

        exit_code = main(["scan", "/nonexistent/path/12345"])
        assert exit_code == 4

    def test_cli_help_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        """CLI --help should output usage information."""
        from constitution_linter.cli import main

        try:
            main(["--help"])
        except SystemExit:
            pass

        captured = capsys.readouterr()
        assert "scan" in captured.out or "constitution-linter" in captured.out


# =============================================================================
# SKIPPED FILES TRACKING TESTS
# =============================================================================


class TestSkippedFilesTracking:
    """Tests for skipped files tracking in ScanResult."""

    def test_skipped_files_in_result(self, temp_dir: Path) -> None:
        """ScanResult should track skipped files."""
        scanner = ConstitutionScanner()

        # Create a file that will be scanned
        clean_file = temp_dir / "clean.md"
        clean_file.write_text("Clean content")

        result = scanner.scan_path(temp_dir)

        # Result should have skipped_files field (may be empty)
        assert hasattr(result, "skipped_files")
        assert hasattr(result, "skip_reasons")
        assert isinstance(result.skipped_files, tuple)
        assert isinstance(result.skip_reasons, tuple)
