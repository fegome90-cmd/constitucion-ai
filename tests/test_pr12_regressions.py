"""PR #12 regressions exercised through the public CLI/fixer and Git."""

from __future__ import annotations

import json
import stat
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from constitution_linter import ConstitutionFixer, ConstitutionScanner
from constitution_linter.cli import main

if TYPE_CHECKING:
    import pytest


def test_subcommand_accepts_format_after_scan(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "clean.md").write_text("Just content", encoding="utf-8")
    assert main(["scan", "--ci", "--format", "json", str(tmp_path)]) == 0
    assert json.loads(capsys.readouterr().out)["passed"]


def test_file_input_can_be_planned_and_dry_run(tmp_path: Path) -> None:
    target = tmp_path / "note.md"
    target.write_text("Claude", encoding="utf-8")
    assert main(["plan", str(target)]) == 0
    assert main(["fix", str(target), "--dry-run"]) == 2
    assert target.read_text(encoding="utf-8") == "Claude"


def test_directory_alias_renames_one_directory_with_many_children(tmp_path: Path) -> None:
    alias = tmp_path / ".claude"
    alias.mkdir()
    (alias / "a.md").write_text("alpha", encoding="utf-8")
    (alias / "b.md").write_text("beta", encoding="utf-8")
    scanner = ConstitutionScanner()
    result = scanner.scan_path(tmp_path)
    assert sum(v.pattern.rule_id == "DIR-001" for v in result.all_violations) == 2
    fixed = ConstitutionFixer(tmp_path).apply_plan(
        ConstitutionFixer(tmp_path).create_plan(result), create_backup=False
    )
    assert fixed.success, fixed.error_message
    assert not alias.exists()
    assert (tmp_path / ".ai" / "a.md").read_text() == "alpha"
    assert (tmp_path / ".ai" / "b.md").read_text() == "beta"


def test_fix_replaces_only_reported_lines_not_fenced_content(tmp_path: Path) -> None:
    target = tmp_path / "note.md"
    target.write_text(
        "Claude outside\n\x60\x60\x60python\nClaude inside\n\x60\x60\x60\n", encoding="utf-8"
    )
    scanner = ConstitutionScanner()
    scan = scanner.scan_path(target)
    assert len([v for v in scan.all_violations if v.pattern.rule_id == "TXT-001"]) == 1
    fixer = ConstitutionFixer(tmp_path)
    result = fixer.apply_plan(fixer.create_plan(scan), create_backup=False)
    assert result.success, result.error_message
    assert target.read_text(encoding="utf-8") == (
        "AI outside\n\x60\x60\x60python\nClaude inside\n\x60\x60\x60\n"
    )


def test_fix_keeps_executable_permissions(tmp_path: Path) -> None:
    target = tmp_path / "run.sh"
    target.write_text("#!/bin/sh\necho Claude\n", encoding="utf-8")
    target.chmod(0o755)
    scanner = ConstitutionScanner()
    scan = scanner.scan_path(target)
    assert scan.total_violations >= 1
    fixer = ConstitutionFixer(tmp_path)
    result = fixer.apply_plan(fixer.create_plan(scan), create_backup=False)
    assert result.success, result.error_message
    assert stat.S_IMODE(target.stat().st_mode) == 0o755


def test_fix_handles_content_and_directory_alias_together(tmp_path: Path) -> None:
    alias = tmp_path / ".claude"
    alias.mkdir()
    (alias / "note.md").write_text("Claude outside", encoding="utf-8")
    fixer = ConstitutionFixer(tmp_path)
    plan = fixer.create_plan(ConstitutionScanner().scan_path(tmp_path))
    outcome = fixer.apply_plan(plan, create_backup=False)
    assert outcome.success, outcome.error_message
    assert (tmp_path / ".ai" / "note.md").read_text() == "AI outside"


def _git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def test_run_all_commit_preserves_unrelated_staged_files(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test Runner")
    (tmp_path / "dirty.md").write_text("Claude outside\n", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("before\n", encoding="utf-8")
    _git(tmp_path, "add", "--", "dirty.md", "notes.txt")
    _git(tmp_path, "commit", "-qm", "initial")
    (tmp_path / "notes.txt").write_text("staged unrelated\n", encoding="utf-8")
    _git(tmp_path, "add", "--", "notes.txt")

    assert main(["run-all", str(tmp_path), "--commit"]) == 0
    assert _git(tmp_path, "show", "--pretty=", "--name-only", "HEAD") == "dirty.md"
    assert _git(tmp_path, "diff", "--cached", "--name-only") == "notes.txt"


def test_manifest_contains_only_existing_tracked_files() -> None:
    root = Path(__file__).resolve().parents[1]
    manifest = (root / "MANIFEST.current.sha256").read_text().splitlines()
    paths = [line.split("  ", 1)[1] for line in manifest]
    tracked = set(
        subprocess.check_output(
            ["git", "ls-files", "--cached", "--full-name"], cwd=root, text=True
        ).splitlines()
    )
    assert set(paths) <= tracked
    assert all((root / p).is_file() for p in paths)


def test_fix_prioritizes_longer_overlapping_match(tmp_path: Path) -> None:
    target = tmp_path / "note.md"
    target.write_text("Claude rules apply\n", encoding="utf-8")
    fixer = ConstitutionFixer(tmp_path)
    result = fixer.apply_plan(
        fixer.create_plan(ConstitutionScanner().scan_path(target)), create_backup=False
    )
    assert result.success, result.error_message
    assert target.read_text(encoding="utf-8") == "AI rules apply\n"


def test_directory_collision_does_not_modify_contents(tmp_path: Path) -> None:
    alias = tmp_path / ".claude"
    alias.mkdir()
    target = alias / "note.md"
    target.write_text("Claude", encoding="utf-8")
    (tmp_path / ".ai").mkdir()
    fixer = ConstitutionFixer(tmp_path)
    result = fixer.apply_plan(
        fixer.create_plan(ConstitutionScanner().scan_path(tmp_path)), create_backup=False
    )
    assert not result.success
    assert target.read_text(encoding="utf-8") == "Claude"


def test_run_all_commit_tracks_directory_rename(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test Runner")
    alias = tmp_path / ".claude"
    alias.mkdir()
    (alias / "config.md").write_text("neutral content\n", encoding="utf-8")
    _git(tmp_path, "add", "--", ".claude")
    _git(tmp_path, "commit", "-qm", "initial")

    assert main(["run-all", str(tmp_path), "--commit"]) == 0
    assert (tmp_path / ".ai" / "config.md").is_file()
    assert not alias.exists()
    assert not _git(tmp_path, "status", "--porcelain")


def test_dry_run_previews_actual_renamed_directory(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    alias = tmp_path / ".claude"
    alias.mkdir()
    (alias / "config.md").write_text("neutral", encoding="utf-8")
    assert main(["fix", str(tmp_path), "--dry-run"]) == 2
    preview = capsys.readouterr().out
    assert f"+++ {tmp_path / '.ai'}" in preview
    assert f"+++ {alias / '.ai'}" not in preview


def test_run_all_commit_uses_literal_paths_for_glob_metacharacters(
    tmp_path: Path,
) -> None:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test Runner")
    target = tmp_path / "file[1].md"
    similar = tmp_path / "file1.md"
    target.write_text("Claude outside\n", encoding="utf-8")
    similar.write_text("original\n", encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-qm", "initial")

    # This unrelated staged change matches Git's glob interpretation of [1].
    similar.write_text("unrelated staged\n", encoding="utf-8")
    _git(tmp_path, "add", "--", "file1.md")

    assert main(["run-all", str(tmp_path), "--commit"]) == 0
    assert target.read_text(encoding="utf-8") == "AI outside\n"
    assert _git(tmp_path, "show", "--pretty=", "--name-only", "HEAD") == "file[1].md"
    assert _git(tmp_path, "diff", "--cached", "--name-only") == "file1.md"


def test_conflicting_alias_directories_rejected_before_any_edit(tmp_path: Path) -> None:
    """Two distinct sources targeting .ai must not mutate either source."""
    claude = tmp_path / ".claude"
    cursor = tmp_path / ".cursor"
    claude.mkdir()
    cursor.mkdir()
    first = claude / "note.md"
    second = cursor / "other.md"
    first.write_text("Claude outside\n", encoding="utf-8")
    second.write_text("Cursor outside\n", encoding="utf-8")

    fixer = ConstitutionFixer(tmp_path)
    result = fixer.apply_plan(
        fixer.create_plan(ConstitutionScanner().scan_path(tmp_path)),
        create_backup=False,
    )
    assert not result.success
    assert ".ai" in (result.error_message or "")
    assert first.read_text(encoding="utf-8") == "Claude outside\n"
    assert second.read_text(encoding="utf-8") == "Cursor outside\n"
    assert not (tmp_path / ".ai").exists()


def test_nested_renames_commit_final_paths_not_transient_paths(tmp_path: Path) -> None:
    """Rename both .claude/ and its child .cursorrules in one exact Git commit."""
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test Runner")
    claude = tmp_path / ".claude"
    claude.mkdir()
    (claude / ".cursorrules").write_text("neutral content\n", encoding="utf-8")
    _git(tmp_path, "add", "--", ".claude")
    _git(tmp_path, "commit", "-qm", "initial")

    assert main(["run-all", str(tmp_path), "--commit"]) == 0
    assert (tmp_path / ".ai" / ".airules").read_text() == "neutral content\n"
    assert not claude.exists()
    assert _git(tmp_path, "status", "--porcelain") == ""
    assert _git(tmp_path, "show", "--no-renames", "--pretty=", "--name-only", "HEAD") == (
        ".ai/.airules\n.claude/.cursorrules"
    )


def test_non_lf_separator_is_not_a_line_boundary(tmp_path: Path) -> None:
    """Scanner and fixer agree on unicode separator and preserve CRLF bytes."""
    target = tmp_path / "note.md"
    target.write_bytes("prefix\u2028Claude\r\nOther\r\n".encode())
    scan = ConstitutionScanner().scan_path(target)
    assert any(v.line == 1 and v.column == 8 for v in scan.all_violations)
    fixer = ConstitutionFixer(tmp_path)
    result = fixer.apply_plan(fixer.create_plan(scan), create_backup=False)
    assert result.success, result.error_message
    assert target.read_bytes() == "prefix\u2028AI\r\nOther\r\n".encode()


def test_literal_wildcard_filename_not_a_commit_glob(tmp_path: Path) -> None:
    """Literal '*' filename never incorporates unrelated staged changes."""
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test Runner")
    (tmp_path / "*.md").write_text("Claude outside\n", encoding="utf-8")
    (tmp_path / "notes.md").write_text("original\n", encoding="utf-8")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-qm", "initial")
    (tmp_path / "notes.md").write_text("staged unrelated\n", encoding="utf-8")
    _git(tmp_path, "add", "--", "notes.md")

    assert main(["run-all", str(tmp_path), "--commit"]) == 0
    assert _git(tmp_path, "show", "--pretty=", "--name-only", "HEAD") == "*.md"
    assert _git(tmp_path, "diff", "--cached", "--name-only") == "notes.md"


def test_directory_rename_commit_excludes_untracked_descendants(tmp_path: Path) -> None:
    """Commit a tracked rename without absorbing a local untracked sibling."""
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test Runner")
    alias = tmp_path / ".claude"
    alias.mkdir()
    (alias / "tracked.md").write_text("neutral content\n", encoding="utf-8")
    _git(tmp_path, "add", "--", ".claude/tracked.md")
    _git(tmp_path, "commit", "-qm", "initial")
    (alias / "private-notes.txt").write_text("personal local note\n", encoding="utf-8")

    assert main(["run-all", str(tmp_path), "--commit"]) == 0
    assert (tmp_path / ".ai" / "tracked.md").read_text() == "neutral content\n"
    assert (tmp_path / ".ai" / "private-notes.txt").read_text() == "personal local note\n"
    committed = _git(tmp_path, "show", "--no-renames", "--pretty=", "--name-only", "HEAD")
    assert committed.splitlines() == [".ai/tracked.md", ".claude/tracked.md"]
    assert "private-notes" not in committed
    assert _git(tmp_path, "ls-files") == ".ai/tracked.md"
    assert _git(tmp_path, "status", "--porcelain") == "?? .ai/private-notes.txt"


def test_untracked_directory_rename_does_not_create_commit(tmp_path: Path) -> None:
    """Missing original is never used as Git pathspec when it was untracked."""
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test Runner")
    (tmp_path / "baseline.md").write_text("clean baseline\n", encoding="utf-8")
    _git(tmp_path, "add", "--", "baseline.md")
    _git(tmp_path, "commit", "-qm", "initial")
    previous_head = _git(tmp_path, "rev-parse", "HEAD")
    alias = tmp_path / ".claude"
    alias.mkdir()
    (alias / "local.md").write_text("local content\n", encoding="utf-8")

    assert main(["run-all", str(tmp_path), "--commit"]) == 0
    assert (tmp_path / ".ai" / "local.md").read_text() == "local content\n"
    assert _git(tmp_path, "rev-parse", "HEAD") == previous_head
    assert _git(tmp_path, "status", "--porcelain") == "?? .ai/"


def test_untracked_content_fix_stays_untracked_on_auto_commit(tmp_path: Path) -> None:
    """Do not silently add a new file even if the fixer edits its content."""
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test Runner")
    (tmp_path / "baseline.md").write_text("clean\n", encoding="utf-8")
    _git(tmp_path, "add", "--", "baseline.md")
    _git(tmp_path, "commit", "-qm", "initial")
    previous_head = _git(tmp_path, "rev-parse", "HEAD")
    new_file = tmp_path / "notes.md"
    new_file.write_text("Claude note\n", encoding="utf-8")

    assert main(["run-all", str(tmp_path), "--commit"]) == 0
    assert new_file.read_text() == "AI note\n"
    assert _git(tmp_path, "rev-parse", "HEAD") == previous_head
    assert _git(tmp_path, "status", "--porcelain") == "?? notes.md"


def test_nested_rename_commit_excludes_untracked_sibling(tmp_path: Path) -> None:
    """Nested file and directory rename may not stage new siblings."""
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test Runner")
    alias = tmp_path / ".claude"
    alias.mkdir()
    (alias / ".cursorrules").write_text("neutral rules\n", encoding="utf-8")
    _git(tmp_path, "add", "--", ".claude/.cursorrules")
    _git(tmp_path, "commit", "-qm", "initial")
    (alias / "local.md").write_text("untracked private\n", encoding="utf-8")

    assert main(["run-all", str(tmp_path), "--commit"]) == 0
    assert (tmp_path / ".ai" / ".airules").read_text() == "neutral rules\n"
    assert (tmp_path / ".ai" / "local.md").read_text() == "untracked private\n"
    assert _git(tmp_path, "ls-files") == ".ai/.airules"
    assert _git(tmp_path, "status", "--porcelain") == "?? .ai/local.md"


def test_commit_refuses_directory_substituted_for_tracked_file(tmp_path: Path) -> None:
    """A tracked blob replaced with a local directory must not leak its contents."""
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test Runner")
    alias = tmp_path / ".claude"
    alias.mkdir()
    leaf = alias / "leaf"
    leaf.write_text("old tracked blob\n")
    _git(tmp_path, "add", "--", ".claude/leaf")
    _git(tmp_path, "commit", "-qm", "baseline")
    before = _git(tmp_path, "rev-parse", "HEAD")
    leaf.unlink()
    leaf.mkdir()
    (leaf / "private.txt").write_text("secret local data\n")

    assert main(["run-all", str(tmp_path), "--commit"]) == 4
    assert _git(tmp_path, "rev-parse", "HEAD") == before
    assert _git(tmp_path, "diff", "--cached", "--name-only") == ""
    assert (tmp_path / ".ai" / "leaf" / "private.txt").read_text() == "secret local data\n"


def test_commit_preserves_explicit_staged_untracking(tmp_path: Path) -> None:
    """git rm --cached is a user decision, not permission to re-add the file."""
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test Runner")
    target = tmp_path / "notes.md"
    target.write_text("original\n")
    _git(tmp_path, "add", "--", "notes.md")
    _git(tmp_path, "commit", "-qm", "baseline")
    before = _git(tmp_path, "rev-parse", "HEAD")
    _git(tmp_path, "rm", "--cached", "--", "notes.md")
    target.write_text("Claude local contents\n")

    assert main(["run-all", str(tmp_path), "--commit"]) == 0
    assert target.read_text() == "AI local contents\n"
    assert _git(tmp_path, "rev-parse", "HEAD") == before
    assert _git(tmp_path, "diff", "--cached", "--name-only") == "notes.md"
    assert _git(tmp_path, "ls-files") == ""


def test_suffix_alias_directory_is_not_renamed(tmp_path: Path) -> None:
    """Only the exact .claude component is an alias; backup.claude is not."""
    alias = tmp_path / "backup.claude"
    alias.mkdir()
    target = alias / "neutral.md"
    target.write_text("neutral content\n")
    assert ConstitutionScanner().scan_path(tmp_path).passed
    assert main(["fix", str(tmp_path)]) == 0
    assert target.is_file()
    assert not (tmp_path / ".ai").exists()


def test_scoped_file_fix_does_not_rename_its_ancestor(tmp_path: Path) -> None:
    alias = tmp_path / ".cursor"
    alias.mkdir()
    target = alias / "note.md"
    target.write_text("Claude guidance\n")
    assert main(["fix", str(target)]) == 0
    assert target.read_text() == "AI guidance\n"
    assert alias.is_dir()
    assert not (tmp_path / ".ai").exists()


def test_dry_run_includes_path_and_content_changes(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    alias = tmp_path / ".claude"
    alias.mkdir()
    target = alias / "note.md"
    target.write_text("Claude outside\n")
    assert main(["fix", str(tmp_path), "--dry-run"]) == 2
    preview = capsys.readouterr().out
    assert str(tmp_path / ".ai") in preview
    assert "-Claude outside" in preview
    assert "+AI outside" in preview
    assert target.read_text() == "Claude outside\n"


def test_backreference_replacement_uses_matched_group(tmp_path: Path) -> None:
    from constitution_linter import MatchScope, Pattern, Severity

    target = tmp_path / "note.md"
    target.write_text("Claude\n")
    pattern = Pattern(
        pattern=r"(Claude)",
        suggestion=r"fixed \1",
        severity=Severity.WARNING,
        rule_id="TXT-CUSTOM",
        scope=MatchScope.FILE_CONTENT,
    )
    fixer = ConstitutionFixer(tmp_path)
    scan = ConstitutionScanner(patterns=[pattern]).scan_path(target)
    assert scan.total_violations == 1
    outcome = fixer.apply_plan(fixer.create_plan(scan), create_backup=False)
    assert outcome.success, outcome.error_message
    assert target.read_text() == "fixed Claude\n"


def test_bare_carriage_return_line_break_is_preserved(tmp_path: Path) -> None:
    target = tmp_path / "note.md"
    target.write_bytes(b"First\rClaude\r")
    scan = ConstitutionScanner().scan_path(target)
    assert any(v.line == 2 for v in scan.all_violations)
    fixer = ConstitutionFixer(tmp_path)
    result = fixer.apply_plan(fixer.create_plan(scan), create_backup=False)
    assert result.success, result.error_message
    assert target.read_bytes() == b"First\rAI\r"


def test_unborn_git_head_does_not_fail_commit(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test Runner")
    target = tmp_path / "note.md"
    target.write_text("Claude untracked\n")
    assert main(["run-all", str(tmp_path), "--commit"]) == 0
    assert target.read_text() == "AI untracked\n"
    assert (
        subprocess.run(
            ["git", "-C", str(tmp_path), "rev-parse", "--verify", "HEAD"],
            check=False,
            capture_output=True,
        ).returncode
        != 0
    )
    assert _git(tmp_path, "ls-files") == ""


def test_ci_separates_offline_checks_from_starter_smokes() -> None:
    """A transient starter dependency outage must not reclassify core Python checks."""
    import yaml

    workflow = yaml.safe_load(
        (Path(__file__).resolve().parents[1] / ".github/workflows/ci.yml").read_text()
    )
    jobs = workflow["jobs"]
    assert "python-and-integrity" in jobs
    assert "starter-integration" in jobs
    offline = "\n".join(step.get("run", "") for step in jobs["python-and-integrity"]["steps"])
    integration = "\n".join(step.get("run", "") for step in jobs["starter-integration"]["steps"])
    assert "pytest tests/test_constitution_linter.py tests/test_pr12_regressions.py" in offline
    assert "pytest tests/ -q" not in offline
    assert "pytest tests/ -q" in integration
    assert all(
        step.get("name") != "Set up Java 21" for step in jobs["python-and-integrity"]["steps"]
    )
    assert any(
        step.get("name") == "Set up Java 21" for step in jobs["starter-integration"]["steps"]
    )
