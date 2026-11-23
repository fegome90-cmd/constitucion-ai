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
    assert (tmp_path / ".claude" / "leaf" / "private.txt").read_text() == "secret local data\n"
    assert not (tmp_path / ".ai").exists()


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
    # This lane explicitly verifies the two provisioned runtimes, not all ten.
    assert "pytest tests/ -q" not in integration
    for name in (
        "test_scaffold_exports_self_contained_python_starter",
        "test_scaffold_exports_self_contained_java_starter",
        "test_apply_kit_delivers_a_working_python_project",
        "test_apply_kit_delivers_a_working_java_project",
    ):
        assert name in integration
    assert "command -v mvn" in integration
    assert "command -v uv" in integration
    assert all(
        step.get("name") != "Set up Java 21" for step in jobs["python-and-integrity"]["steps"]
    )
    assert any(
        step.get("name") == "Set up Java 21" for step in jobs["starter-integration"]["steps"]
    )


def test_commit_skips_prior_unstaged_deleted_descendant(tmp_path: Path) -> None:
    """A file deleted before scanning is not part of the rename to auto-commit."""
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test Runner")
    alias = tmp_path / ".claude"
    alias.mkdir()
    kept = alias / "kept.md"
    deleted = alias / "deleted.md"
    kept.write_text("keep me\n")
    deleted.write_text("delete me\n")
    _git(tmp_path, "add", "--", ".claude")
    _git(tmp_path, "commit", "-qm", "baseline")
    deleted.unlink()

    assert main(["run-all", str(tmp_path), "--commit"]) == 0
    assert (tmp_path / ".ai" / "kept.md").read_text() == "keep me\n"
    committed = _git(tmp_path, "show", "--no-renames", "--pretty=", "--name-only", "HEAD")
    assert committed.splitlines() == [".ai/kept.md", ".claude/kept.md"]
    assert _git(tmp_path, "diff", "--name-only") == ".claude/deleted.md"
    assert _git(tmp_path, "diff", "--cached", "--name-only") == ""


def test_commit_requires_modified_source_not_preexisting_destination(tmp_path: Path) -> None:
    """A HEAD-tracked destination must not authorize an untracked source."""
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test Runner")
    previous = tmp_path / ".ai"
    previous.mkdir()
    (previous / "note.txt").write_text("versioned baseline\n")
    _git(tmp_path, "add", "--", ".ai/note.txt")
    _git(tmp_path, "commit", "-qm", "baseline")
    original_head = _git(tmp_path, "rev-parse", "HEAD")
    (previous / "note.txt").unlink()
    previous.rmdir()
    alias = tmp_path / ".claude"
    alias.mkdir()
    (alias / "note.txt").write_text("untracked private contents\n")

    assert main(["run-all", str(tmp_path), "--commit"]) == 0
    assert _git(tmp_path, "rev-parse", "HEAD") == original_head
    assert _git(tmp_path, "show", "HEAD:.ai/note.txt") == "versioned baseline"
    assert _git(tmp_path, "diff", "--cached", "--name-only") == ""
    assert (tmp_path / ".ai" / "note.txt").read_text() == "untracked private contents\n"


def test_relative_public_api_alias_is_renamed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    target = Path(".cursorrules")
    target.write_text("neutral\n")
    scan = ConstitutionScanner().scan_path(target)
    assert scan.total_violations >= 1
    fixer = ConstitutionFixer(tmp_path)
    result = fixer.apply_plan(fixer.create_plan(scan), create_backup=False)
    assert result.success, result.error_message
    assert not target.exists()
    assert Path(".airules").read_text() == "neutral\n"


def test_end_anchored_regex_matches_crlf_body(tmp_path: Path) -> None:
    from constitution_linter import MatchScope, Pattern, Severity

    target = tmp_path / "rules.md"
    target.write_bytes(b"Claude\r\n")
    pattern = Pattern(
        pattern=r"Claude$",
        suggestion="AI",
        severity=Severity.WARNING,
        rule_id="TXT-END",
        scope=MatchScope.FILE_CONTENT,
    )
    scan = ConstitutionScanner(patterns=[pattern]).scan_path(target)
    assert scan.total_violations == 1
    fixer = ConstitutionFixer(tmp_path)
    result = fixer.apply_plan(fixer.create_plan(scan), create_backup=False)
    assert result.success, result.error_message
    assert target.read_bytes() == b"AI\r\n"


def test_run_all_explicitly_rejects_unsupported_json_format(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = tmp_path / "note.md"
    target.write_text("Claude\n")
    assert main(["run-all", str(tmp_path), "--format", "json"]) == 3
    message = capsys.readouterr()
    assert "format" in message.err.lower()
    assert "not supported" in message.err.lower()
    assert target.read_text() == "Claude\n"


def test_commit_ignored_destination_preserves_original_and_index(tmp_path: Path) -> None:
    """Ignored .ai destination must block run-all before any move or staging."""
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test Runner")
    (tmp_path / ".gitignore").write_text(".ai/\n")
    old = tmp_path / ".claude"
    old.mkdir()
    (old / "keep.md").write_text("neutral\n")
    _git(tmp_path, "add", "--", ".gitignore", ".claude/keep.md")
    _git(tmp_path, "commit", "-qm", "baseline")
    head_before = _git(tmp_path, "rev-parse", "HEAD")

    assert main(["run-all", str(tmp_path), "--commit"]) == 4
    assert (old / "keep.md").read_text() == "neutral\n"
    assert not (tmp_path / ".ai").exists()
    assert _git(tmp_path, "rev-parse", "HEAD") == head_before
    assert _git(tmp_path, "diff", "--cached", "--name-only") == ""


def test_changed_file_alias_symlink_does_not_rename_referent(tmp_path: Path) -> None:
    """The fixer must validate symlinks at their lexical scanned path."""
    old = tmp_path / ".cursorrules"
    old.write_text("normal\n")
    fixer = ConstitutionFixer(tmp_path)
    plan = fixer.create_plan(ConstitutionScanner().scan_path(old))
    victim = tmp_path / "victim.txt"
    victim.write_text("preserve me\n")
    old.unlink()
    old.symlink_to(victim)

    result = fixer.apply_plan(plan, create_backup=False)
    assert not result.success
    assert old.is_symlink()
    assert victim.read_text() == "preserve me\n"
    assert not (tmp_path / ".airules").exists()


def test_file_alias_suffix_must_not_be_rewritten(tmp_path: Path) -> None:
    target = tmp_path / ".cursorrules.local"
    target.write_text("neutral\n")
    assert ConstitutionScanner().scan_path(target).passed
    assert main(["fix", str(target)]) == 0
    assert target.read_text() == "neutral\n"
    assert not (tmp_path / ".airules").exists()


def test_file_alias_directory_name_is_not_file_hit(tmp_path: Path) -> None:
    directory = tmp_path / ".cursorrules"
    directory.mkdir()
    (directory / "note.md").write_text("neutral\n")
    scan = ConstitutionScanner().scan_path(tmp_path)
    assert scan.passed, scan.all_violations


def test_custom_both_scope_path_hit_does_not_abort_content_fix(tmp_path: Path) -> None:
    from constitution_linter import MatchScope, Pattern, Severity

    target = tmp_path / "Claude.md"
    target.write_text("Claude\n")
    pattern = Pattern(
        pattern="Claude",
        suggestion="AI",
        severity=Severity.WARNING,
        rule_id="TXT-BOTH",
        scope=MatchScope.BOTH,
    )
    scanner = ConstitutionScanner(patterns=[pattern])
    scan = scanner.scan_path(target)
    assert any(v.line is None for v in scan.all_violations)
    assert any(v.line is not None for v in scan.all_violations)
    fixer = ConstitutionFixer(tmp_path)
    plan = fixer.create_plan(scan)
    assert plan.needs_review >= 1
    result = fixer.apply_plan(plan, create_backup=False)
    assert result.success, result.error_message
    assert target.read_text() == "AI\n"
    assert target.name == "Claude.md"


def test_large_rename_commit_stages_only_tracked_leaves(tmp_path: Path) -> None:
    """Batch commits use exact file paths and preserve unrelated additions."""
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test Runner")
    directory = tmp_path / ".claude"
    directory.mkdir()
    for i in range(80):
        (directory / f"config-{i:03d}.md").write_text(f"config {i}\n")
    _git(tmp_path, "add", "--", ".claude")
    _git(tmp_path, "commit", "-qm", "baseline")
    (directory / "private.txt").write_text("untracked private\n")
    assert main(["run-all", str(tmp_path), "--commit"]) == 0
    assert len(_git(tmp_path, "ls-files").splitlines()) == 80
    assert (tmp_path / ".ai" / "private.txt").read_text() == "untracked private\n"
    assert _git(tmp_path, "status", "--porcelain") == "?? .ai/private.txt"


def test_staged_rename_destination_is_not_overwritten(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test Runner")
    source = tmp_path / ".cursorrules"
    source.write_text("baseline source\n")
    _git(tmp_path, "add", "--", ".cursorrules")
    _git(tmp_path, "commit", "-qm", "baseline")
    previous_head = _git(tmp_path, "rev-parse", "HEAD")
    destination = tmp_path / ".airules"
    destination.write_text("precious staged change\n")
    _git(tmp_path, "add", "--", ".airules")
    destination.unlink()

    assert main(["run-all", str(tmp_path), "--commit"]) == 4
    assert source.read_text() == "baseline source\n"
    assert not destination.exists()
    assert _git(tmp_path, "show", ":.airules") == "precious staged change"
    assert _git(tmp_path, "diff", "--cached", "--name-only") == ".airules"
    assert _git(tmp_path, "rev-parse", "HEAD") == previous_head


def test_nested_ignored_final_destination_rejected_before_rename(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test Runner")
    source = tmp_path / ".claude"
    source.mkdir()
    (source / ".cursorrules").write_text("neutral\n")
    (tmp_path / ".gitignore").write_text("/.ai/.airules\n")
    _git(tmp_path, "add", "--", ".claude/.cursorrules", ".gitignore")
    _git(tmp_path, "commit", "-qm", "baseline")

    assert main(["run-all", str(tmp_path), "--commit"]) == 4
    assert (source / ".cursorrules").is_file()
    assert not (tmp_path / ".ai").exists()
    assert _git(tmp_path, "diff", "--cached", "--name-only") == ""


def test_direct_symlink_fix_and_run_all_rejected_before_following(tmp_path: Path) -> None:
    target = tmp_path / "original.md"
    target.write_text("Claude in original\n")
    link = tmp_path / "link.md"
    link.symlink_to(target)
    assert main(["fix", str(link)]) != 0
    assert target.read_text() == "Claude in original\n"
    assert link.is_symlink()
    assert main(["run-all", str(link), "--commit"]) != 0
    assert target.read_text() == "Claude in original\n"


def test_backslash_is_not_path_separator_on_posix(tmp_path: Path) -> None:
    import os

    if os.name == "nt":
        return
    target = tmp_path / "notes\\.cursorrules"
    target.write_text("neutral\n")
    assert ConstitutionScanner().scan_path(target).passed
    assert main(["fix", str(target)]) == 0
    assert target.read_text() == "neutral\n"
    assert not (tmp_path / ".airules").exists()


def test_untracked_ignored_alias_does_not_block_tracked_content_commit(
    tmp_path: Path,
) -> None:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test Runner")
    tracked = tmp_path / "tracked.md"
    tracked.write_text("Claude\n")
    (tmp_path / ".gitignore").write_text(".ai/\n")
    _git(tmp_path, "add", "--", "tracked.md", ".gitignore")
    _git(tmp_path, "commit", "-qm", "baseline")
    # Tracked source is clean; only the unrelated alias directory is untracked.
    alias = tmp_path / ".claude"
    alias.mkdir()
    (alias / "untracked.md").write_text("neutral\n")

    assert main(["run-all", str(tmp_path), "--commit"]) == 0
    assert tracked.read_text() == "AI\n"
    assert _git(tmp_path, "show", "--pretty=", "--name-only", "HEAD") == "tracked.md"
    assert (tmp_path / ".ai" / "untracked.md").read_text() == "neutral\n"
    assert _git(tmp_path, "diff", "--cached", "--name-only") == ""


def test_commit_with_no_resulting_diff_is_success(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test Runner")
    target = tmp_path / "note.md"
    target.write_text("AI\n")
    _git(tmp_path, "add", "--", "note.md")
    _git(tmp_path, "commit", "-qm", "baseline")
    old_head = _git(tmp_path, "rev-parse", "HEAD")
    target.write_text("Claude\n")
    assert main(["run-all", str(tmp_path), "--commit"]) == 0
    assert target.read_text() == "AI\n"
    assert _git(tmp_path, "rev-parse", "HEAD") == old_head
    assert _git(tmp_path, "status", "--porcelain") == ""


def test_commit_preserves_staged_draft_in_the_same_source(tmp_path: Path) -> None:
    """Even a no-op fix must not discard previously staged same-file content."""
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test Runner")
    target = tmp_path / "note.md"
    target.write_text("AI\n")
    _git(tmp_path, "add", "--", "note.md")
    _git(tmp_path, "commit", "-qm", "baseline")
    head_before = _git(tmp_path, "rev-parse", "HEAD")
    target.write_text("staged draft\n")
    _git(tmp_path, "add", "--", "note.md")
    target.write_text("Claude\n")

    assert main(["run-all", str(tmp_path), "--commit"]) == 4
    assert target.read_text() == "Claude\n"
    assert _git(tmp_path, "show", ":note.md") == "staged draft"
    assert _git(tmp_path, "rev-parse", "HEAD") == head_before


def test_commit_rejects_tracked_ancestor_of_rename_target(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test Runner")
    alias = tmp_path / ".claude"
    alias.mkdir()
    (alias / "a.md").write_text("neutral\n")
    (tmp_path / ".ai").write_text("an unrelated tracked file\n")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-qm", "baseline")
    (tmp_path / ".ai").unlink()

    assert main(["run-all", str(tmp_path), "--commit"]) == 4
    assert (alias / "a.md").read_text() == "neutral\n"
    assert not (tmp_path / ".ai").exists()
    assert _git(tmp_path, "diff", "--cached", "--name-only") == ""


def test_commit_rejects_tracked_descendant_of_rename_target(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test Runner")
    alias = tmp_path / ".claude"
    alias.mkdir()
    (alias / "a.md").write_text("neutral\n")
    old = tmp_path / ".ai" / "a.md"
    old.mkdir(parents=True)
    (old / "unrelated.txt").write_text("tracked value\n")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-qm", "baseline")
    (old / "unrelated.txt").unlink()
    old.rmdir()
    (tmp_path / ".ai").rmdir()

    assert main(["run-all", str(tmp_path), "--commit"]) == 4
    assert (alias / "a.md").read_text() == "neutral\n"
    assert _git(tmp_path, "diff", "--cached", "--name-only") == ""


def test_commit_rejects_gitignore_rules_moved_with_directory(tmp_path: Path) -> None:
    """Moving a source .gitignore may ignore files only after the rename."""
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test Runner")
    source = tmp_path / ".claude"
    source.mkdir()
    (source / ".gitignore").write_text("a.md\n")
    (source / "a.md").write_text("neutral\n")
    _git(tmp_path, "add", "-f", "--", ".claude/a.md", ".claude/.gitignore")
    _git(tmp_path, "commit", "-qm", "baseline")

    assert main(["run-all", str(tmp_path), "--commit"]) == 4
    assert (source / "a.md").read_text() == "neutral\n"
    assert not (tmp_path / ".ai").exists()
    assert _git(tmp_path, "diff", "--cached", "--name-only") == ""


def test_dry_run_reports_conflicting_alias_targets(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    for name in (".claude", ".cursor"):
        directory = tmp_path / name
        directory.mkdir()
        (directory / "note.md").write_text("neutral\n")
    assert main(["fix", str(tmp_path), "--dry-run"]) == 4
    out = capsys.readouterr()
    assert "Conflicting rename destination" in out.err
    assert (tmp_path / ".claude" / "note.md").exists()
    assert (tmp_path / ".cursor" / "note.md").exists()


def test_directory_autocommit_rejects_unstaged_tracked_draft(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test Runner")
    directory = tmp_path / ".claude"
    directory.mkdir()
    target = directory / "note.md"
    target.write_text("neutral baseline\n")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-qm", "baseline")
    old_head = _git(tmp_path, "rev-parse", "HEAD")
    target.write_text("unrelated local draft\n")

    assert main(["run-all", str(tmp_path), "--commit"]) == 4
    assert target.read_text() == "unrelated local draft\n"
    assert not (tmp_path / ".ai").exists()
    assert _git(tmp_path, "rev-parse", "HEAD") == old_head
    assert _git(tmp_path, "diff", "--cached", "--name-only") == ""
    assert _git(tmp_path, "diff", "--name-only") == ".claude/note.md"


def test_dry_run_rejects_preexisting_destination(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    directory = tmp_path / ".claude"
    directory.mkdir()
    (directory / "note.md").write_text("neutral\n")
    (tmp_path / ".ai").mkdir()
    assert main(["fix", str(tmp_path), "--dry-run"]) == 4
    assert "destination" in capsys.readouterr().err.lower()
    assert (directory / "note.md").is_file()


def test_custom_directory_pattern_may_end_before_separator(tmp_path: Path) -> None:
    from constitution_linter import MatchScope, Pattern, Severity

    directory = tmp_path / ".claude"
    directory.mkdir()
    (directory / "note.md").write_text("neutral\n")
    rule = Pattern(
        pattern=r"\.claude(?=/)",
        suggestion=".ai/",
        severity=Severity.CRITICAL,
        rule_id="DIR-CUSTOM",
        scope=MatchScope.FILE_PATH,
    )
    scanner = ConstitutionScanner(patterns=[rule])
    scan = scanner.scan_path(tmp_path)
    assert scan.total_violations == 1
    fixer = ConstitutionFixer(tmp_path)
    result = fixer.apply_plan(fixer.create_plan(scan), create_backup=False)
    assert result.success, result.error_message
    assert (tmp_path / ".ai" / "note.md").read_text() == "neutral\n"


def test_invalid_regex_replacement_aborts_before_any_file_change(tmp_path: Path) -> None:
    from constitution_linter import MatchScope, Pattern, Severity

    first = tmp_path / "a.md"
    second = tmp_path / "b.md"
    first.write_text("Claude\n")
    second.write_text("Gemini\n")
    rules = [
        Pattern(
            pattern="Claude",
            suggestion="AI",
            severity=Severity.WARNING,
            rule_id="TXT-OK",
            scope=MatchScope.FILE_CONTENT,
        ),
        Pattern(
            pattern=r"(Gemini)",
            suggestion=r"\g<unknown>",
            severity=Severity.WARNING,
            rule_id="TXT-INVALID",
            scope=MatchScope.FILE_CONTENT,
        ),
    ]
    fixer = ConstitutionFixer(tmp_path)
    plan = fixer.create_plan(ConstitutionScanner(patterns=rules).scan_path(tmp_path))
    outcome = fixer.apply_plan(plan, create_backup=False)
    assert not outcome.success
    assert "replacement" in (outcome.error_message or "").lower()
    assert first.read_text() == "Claude\n"
    assert second.read_text() == "Gemini\n"

    import pytest as pytest_runtime

    with pytest_runtime.raises(ValueError, match="replacement"):
        fixer.generate_diff(plan)


def test_content_only_autocommit_rejects_unrelated_unstaged_paragraph(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test Runner")
    target = tmp_path / "note.md"
    target.write_text("Claude outside\nkeep original\n")
    _git(tmp_path, "add", "--", "note.md")
    _git(tmp_path, "commit", "-qm", "baseline")
    old_head = _git(tmp_path, "rev-parse", "HEAD")
    target.write_text("Claude outside\nprivate unstaged paragraph\n")

    assert main(["run-all", str(tmp_path), "--commit"]) == 4
    assert target.read_text() == "Claude outside\nprivate unstaged paragraph\n"
    assert _git(tmp_path, "rev-parse", "HEAD") == old_head
    assert _git(tmp_path, "diff", "--cached", "--name-only") == ""


def test_edited_gitignore_and_alias_rename_rejected_before_files_change(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test Runner")
    (tmp_path / ".gitignore").write_text("Claude*\n")
    directory = tmp_path / ".claude"
    directory.mkdir()
    (directory / "AI-notes.md").write_text("neutral\n")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-qm", "baseline")
    old_head = _git(tmp_path, "rev-parse", "HEAD")

    assert main(["run-all", str(tmp_path), "--commit"]) == 4
    assert (tmp_path / ".gitignore").read_text() == "Claude*\n"
    assert (directory / "AI-notes.md").read_text() == "neutral\n"
    assert not (tmp_path / ".ai").exists()
    assert _git(tmp_path, "diff", "--cached", "--name-only") == ""
    assert _git(tmp_path, "rev-parse", "HEAD") == old_head


def test_stale_case_changed_scan_aborts_all_content_fixes(tmp_path: Path) -> None:
    a = tmp_path / "a.md"
    b = tmp_path / "b.md"
    a.write_text("Claude\n")
    b.write_text("Claude\n")
    fixer = ConstitutionFixer(tmp_path)
    plan = fixer.create_plan(ConstitutionScanner().scan_path(tmp_path))
    b.write_text("claude\n")

    result = fixer.apply_plan(plan, create_backup=False)
    assert not result.success
    assert "stale" in (result.error_message or "").lower()
    assert a.read_text() == "Claude\n"
    assert b.read_text() == "claude\n"


def test_posix_literal_backslash_alias_directory_not_renamed(tmp_path: Path) -> None:
    import os

    if os.name == "nt":
        return
    directory = tmp_path / ".claude\\"
    directory.mkdir()
    (directory / "note.md").write_text("neutral\n")
    assert ConstitutionScanner().scan_path(tmp_path).passed
    assert main(["fix", str(tmp_path)]) == 0
    assert (directory / "note.md").read_text() == "neutral\n"
    assert not (tmp_path / ".ai").exists()


def test_custom_directory_pattern_can_consume_leading_separator(tmp_path: Path) -> None:
    import os
    import re

    from constitution_linter import MatchScope, Pattern, Severity

    directory = tmp_path / ".claude"
    directory.mkdir()
    (directory / "note.md").write_text("neutral\n")
    pattern = Pattern(
        pattern=rf"{re.escape(os.sep)}\.claude{re.escape(os.sep)}",
        suggestion=".ai/",
        severity=Severity.CRITICAL,
        rule_id="DIR-LEAD",
        scope=MatchScope.FILE_PATH,
    )
    scan = ConstitutionScanner(patterns=[pattern]).scan_path(tmp_path)
    assert scan.total_violations == 1


def test_nested_dry_run_lists_actual_rename_operation_order(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    directory = tmp_path / ".claude"
    directory.mkdir()
    (directory / ".cursorrules").write_text("neutral\n")
    assert main(["fix", str(tmp_path), "--dry-run"]) == 2
    output = capsys.readouterr().out
    child = f"--- {directory / '.cursorrules'}\n+++ {directory / '.airules'}"
    parent = f"--- {directory}\n+++ {tmp_path / '.ai'}"
    assert child in output
    assert parent in output
    assert output.index(child) < output.index(parent)


def test_interactive_autocommit_refuses_dirty_content_sources(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test Runner")
    target = tmp_path / "note.md"
    target.write_text("AI\nAI\n")
    _git(tmp_path, "add", "--", "note.md")
    _git(tmp_path, "commit", "-qm", "baseline")
    old_head = _git(tmp_path, "rev-parse", "HEAD")
    target.write_text("Claude\nClaude\n")
    responses = iter(("y", "y", "n"))
    monkeypatch.setattr("builtins.input", lambda _: next(responses))

    assert main(["run-all", str(tmp_path), "--interactive", "--commit"]) == 4
    assert target.read_text() == "Claude\nClaude\n"
    assert _git(tmp_path, "rev-parse", "HEAD") == old_head
    assert _git(tmp_path, "diff", "--cached", "--name-only") == ""


def test_noop_autocommit_rejects_unstaged_executable_mode(tmp_path: Path) -> None:
    import os

    if os.name == "nt":
        return
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test Runner")
    target = tmp_path / "note.md"
    target.write_text("AI\n")
    target.chmod(0o644)
    _git(tmp_path, "add", "--", "note.md")
    _git(tmp_path, "commit", "-qm", "baseline")
    old_head = _git(tmp_path, "rev-parse", "HEAD")
    target.write_text("Claude\n")
    target.chmod(0o755)

    assert main(["run-all", str(tmp_path), "--commit"]) == 4
    assert target.read_text() == "Claude\n"
    assert _git(tmp_path, "rev-parse", "HEAD") == old_head
    assert _git(tmp_path, "diff", "--cached", "--name-only") == ""


def test_crlf_noop_autocommit_respects_git_clean_filters(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test Runner")
    (tmp_path / ".gitattributes").write_text("*.md text eol=crlf\n")
    target = tmp_path / "note.md"
    target.write_bytes(b"AI\n")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-qm", "baseline")
    old_head = _git(tmp_path, "rev-parse", "HEAD")
    target.write_bytes(b"Claude\r\n")

    assert main(["run-all", str(tmp_path), "--commit"]) == 0
    assert target.read_bytes() == b"AI\r\n"
    assert _git(tmp_path, "rev-parse", "HEAD") == old_head
    assert _git(tmp_path, "diff", "--cached", "--name-only") == ""


def test_custom_directory_alias_with_literal_backslash_is_respected(tmp_path: Path) -> None:
    import os

    from constitution_linter import MatchScope, Pattern, Severity

    if os.name == "nt":
        return
    directory = tmp_path / "legacy\\"
    directory.mkdir()
    (directory / "note.md").write_text("neutral\n")
    rule = Pattern(
        pattern=r"legacy\\(?=/)",
        suggestion="modern",
        severity=Severity.WARNING,
        rule_id="DIR-BACKSLASH",
        scope=MatchScope.FILE_PATH,
    )
    scan = ConstitutionScanner(patterns=[rule]).scan_path(tmp_path)
    assert scan.total_violations == 1


def test_autocommit_rejects_changes_to_gitattributes_before_rename(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test Runner")
    attr = tmp_path / ".gitattributes"
    attr.write_text("*.md filter=Claude\n")
    directory = tmp_path / ".claude"
    directory.mkdir()
    (directory / "note.md").write_text("neutral\n")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-qm", "baseline")
    original_head = _git(tmp_path, "rev-parse", "HEAD")

    assert main(["run-all", str(tmp_path), "--commit"]) == 4
    assert attr.read_text() == "*.md filter=Claude\n"
    assert (directory / "note.md").read_text() == "neutral\n"
    assert not (tmp_path / ".ai").exists()
    assert _git(tmp_path, "diff", "--cached", "--name-only") == ""
    assert _git(tmp_path, "rev-parse", "HEAD") == original_head


def test_autocommit_uses_git_effective_owner_execute_mode(tmp_path: Path) -> None:
    import os

    if os.name == "nt":
        return
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test Runner")
    _git(tmp_path, "config", "core.fileMode", "true")
    target = tmp_path / "note.md"
    target.write_text("AI\n")
    target.chmod(0o755)
    _git(tmp_path, "add", "--", "note.md")
    _git(tmp_path, "commit", "-qm", "baseline")
    original_head = _git(tmp_path, "rev-parse", "HEAD")
    target.write_text("Claude\n")
    target.chmod(0o655)

    assert main(["run-all", str(tmp_path), "--commit"]) == 4
    assert target.read_text() == "Claude\n"
    assert _git(tmp_path, "rev-parse", "HEAD") == original_head
    assert _git(tmp_path, "diff", "--cached", "--name-only") == ""


def test_autocommit_respects_git_core_filemode_false(tmp_path: Path) -> None:
    import os

    if os.name == "nt":
        return
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test Runner")
    target = tmp_path / "note.md"
    target.write_text("AI\n")
    target.chmod(0o755)
    _git(tmp_path, "add", "--", "note.md")
    _git(tmp_path, "commit", "-qm", "baseline")
    _git(tmp_path, "config", "core.fileMode", "false")
    original_head = _git(tmp_path, "rev-parse", "HEAD")
    target.write_text("Claude\n")
    target.chmod(0o644)

    assert main(["run-all", str(tmp_path), "--commit"]) == 0
    assert target.read_text() == "AI\n"
    assert _git(tmp_path, "rev-parse", "HEAD") == original_head
    assert _git(tmp_path, "ls-files", "-s").startswith("100755 ")
    assert _git(tmp_path, "status", "--porcelain") == ""


def test_case_variant_gitattributes_rejected_before_rename(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test Runner")
    attrs = tmp_path / ".GITATTRIBUTES"
    attrs.write_text("*.md filter=Claude\n")
    directory = tmp_path / ".claude"
    directory.mkdir()
    (directory / "note.md").write_text("neutral\n")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-qm", "baseline")
    previous_head = _git(tmp_path, "rev-parse", "HEAD")

    assert main(["run-all", str(tmp_path), "--commit"]) == 4
    assert attrs.read_text() == "*.md filter=Claude\n"
    assert (directory / "note.md").read_text() == "neutral\n"
    assert not (tmp_path / ".ai").exists()
    assert _git(tmp_path, "diff", "--cached", "--name-only") == ""
    assert _git(tmp_path, "rev-parse", "HEAD") == previous_head


def test_untracked_only_gitattributes_may_fix_without_creating_commit(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test Runner")
    attrs = tmp_path / ".gitattributes"
    attrs.write_text("# Claude\n")
    assert main(["run-all", str(tmp_path), "--commit"]) == 0
    assert attrs.read_text() == "# AI\n"
    assert _git(tmp_path, "ls-files") == ""
    assert (
        subprocess.run(
            ["git", "-C", str(tmp_path), "rev-parse", "--verify", "HEAD"],
            check=False,
            capture_output=True,
        ).returncode
        != 0
    )


def test_untracked_attrs_alias_and_prior_deleted_tracked_leaf_do_not_block(tmp_path: Path) -> None:
    """Deleted tracked leaves are not eligible as sources for auto-commit."""
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "test@example.invalid")
    _git(tmp_path, "config", "user.name", "Test Runner")
    directory = tmp_path / ".claude"
    directory.mkdir()
    deleted = directory / "gone.md"
    deleted.write_text("previously tracked\n")
    _git(tmp_path, "add", "--", ".claude/gone.md")
    _git(tmp_path, "commit", "-qm", "baseline")
    original_head = _git(tmp_path, "rev-parse", "HEAD")
    deleted.unlink()
    (directory / "new.md").write_text("neutral local\n")
    attributes = tmp_path / ".gitattributes"
    attributes.write_text("# Claude\n")

    assert main(["run-all", str(tmp_path), "--commit"]) == 0
    assert attributes.read_text() == "# AI\n"
    assert (tmp_path / ".ai" / "new.md").read_text() == "neutral local\n"
    assert not directory.exists()
    assert _git(tmp_path, "rev-parse", "HEAD") == original_head
    assert _git(tmp_path, "diff", "--cached", "--name-only") == ""
    assert _git(tmp_path, "diff", "--name-only") == ".claude/gone.md"
    assert _git(tmp_path, "ls-files") == ".claude/gone.md"
