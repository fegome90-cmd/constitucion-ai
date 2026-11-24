# Constitutional Generate Template

## Request

- **Mode:** generate
- **Target Repo Root:** `<current cwd>`
- **Canonical Source Resolution:** `<explicit | local-verified | remote-verified>`
- **Requested Artifact:** `<relative path or artifact name>`
- **Goal:** `<what should exist after this task>`

## Pre-Write Reading

- Existing files reviewed:
  - `<file>`
- Existing docs/contracts reviewed:
  - `<doc>`
- Reuse decision:
  - `<what can be extended instead of recreated>`

## Constitutional Slice

- Ley I — `<why it applies>`
- Ley II — `<why it applies>`
- Ley III — `<why it applies>`
- Ley IV — `<why it applies>`
- Ley VI — `<why it applies>`
- Ley XII — `<why it applies>`

## Constraints

- Output paths must remain relative to the target repo.
- Do not emit source-repo paths as target destinations.
- Do not add machinery that is not justified by the current scope.
- Block if target or canonical source cannot be verified.

## Proposed Output

- Artifact path(s):
  - `<relative path>`
- Validation plan:
  - `<how the result will be checked>`
- Constitutional rationale:
  - `<2-5 sentences>`
