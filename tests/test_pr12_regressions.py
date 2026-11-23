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
