#!/usr/bin/env bash
# lint_markdownlint_changed.sh
# Runs markdownlint-cli2 on changed .md files compared to main.
# If no .md files changed, runs a minimal check (README or first .md found).
# Exit 0 = PASS, non-zero = FAIL

set -euo pipefail

MARKDOWNLINT="${MARKDOWNLINT_BIN:-markdownlint-cli2}"
BASE_BRANCH="${BASE_BRANCH:-main}"

# ── Collect changed .md files ────────────────────────────────────────────────
CHANGED=$(git diff --name-only "${BASE_BRANCH}...HEAD" -- '*.md' 2>/dev/null || true)

if [ -z "${CHANGED}" ]; then
  echo "No .md files changed on ${BASE_BRANCH}...HEAD"
  # Fallback: minimal check on any .md file to keep parser conclusive
  FALLBACK=$(git ls-files '*.md' | grep -v '.worktrees' | head -n 1 || true)
  if [ -z "${FALLBACK}" ]; then
    echo "No .md files found in repo. Skipping."
    echo "All checks passed!"
    exit 0
  fi
  echo "Running minimal check on: ${FALLBACK}"
  CHANGED="${FALLBACK}"
fi

echo "Files to lint:"
echo "${CHANGED}" | while IFS= read -r f; do echo "  - ${f}"; done
echo ""

# ── Run markdownlint-cli2 ────────────────────────────────────────────────────
# xargs handles the file list; markdownlint-cli2 accepts globs or explicit paths
echo "${CHANGED}" | tr '\n' '\0' | xargs -0 "${MARKDOWNLINT}" || {
  EXIT_CODE=$?
  echo ""
  echo "markdownlint FAILED with exit code ${EXIT_CODE}"
  exit "${EXIT_CODE}"
}

echo ""
echo "All checks passed!"
exit 0
