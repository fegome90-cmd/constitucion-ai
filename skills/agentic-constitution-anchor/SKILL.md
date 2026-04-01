---
name: agentic-constitution-anchor
description: "Use when the user explicitly wants to create or review artifacts under the Agentic Constitution, anchor work to a canonical constitution, or avoid source/target repository path mixing during cross-repo generation while keeping all generation and review scoped to the current target repository."
license: Apache-2.0
metadata:
  author: gentleman-programming
  version: "1.0"
---

# agentic-constitution-anchor

## When to Use

Use this skill only when the user explicitly wants to:

- generate a new artifact under the Agentic Constitution;
- review an existing artifact with constitutional criteria;
- apply a canonical constitution without mixing the source repository and the target repository.

Do not auto-activate this skill. Manual invocation only.

## Activation Contract

This skill operates under a temporary governance contract for a single invocation:

1. Activation is manual and explicit.
2. The canonical constitution source is separate from the target repository.
3. The target repository is the current `cwd`.
4. This skill does not persist governance state between invocations.
5. This skill cannot infer that the constitution source repo is also the target repo.

Runtime sequence:

1. Resolve `target_repo_root` as the current `cwd`.
2. Resolve `constitution_source` using strict precedence:
   1. explicit source supplied by the user;
   2. verified local `constitucion-ai` checkout;
   3. verified remote canonical source;
   4. otherwise `BLOCK`.
3. Load only the minimum constitutional subset required for the task.
4. Execute `generate` or `review` within the declared jurisdiction.
5. Expire the governance contract when the invocation ends.

## Modes

| Mode | Purpose | Effective role | Allowed surface | Primary output |
|---|---|---|---|---|
| `generate` | Create a new artifact under constitutional governance | `editor` | write limited to the current target repo | scoped artifact or proposal + constitutional rationale |
| `review` | Evaluate an existing artifact against constitutional rules | `reviewer` | review limited to the current target repo | structured verdict + evidence + laws applied + next actions |

## Critical Patterns

| Pattern | Rule |
|---|---|
| Source vs Target | `constitution_source` and `target_repo_root` are never treated as the same surface by default |
| Canonical precedence | Resolve by explicit → local verified → remote verified → block |
| Relative outputs only | Any generated working path must be relative to the target repo |
| Temporary governance | The constitution applies only during the current invocation |
| Minimal law injection | Apply only the constitutional subset needed for the task |
| No ornamental machinery | Do not add scripts, caches, or side systems when `SKILL.md` + references are sufficient |

## Blocking Rules

Block immediately if any of these are true:

- the target repository cannot be identified with confidence;
- the canonical source cannot be verified;
- source and target paths are being mixed in the same generated output;
- the user asks `generate` or `review` to operate on two target repos at once;
- the requested action exceeds the declared jurisdiction or requires sensitive capabilities outside normal `editor` / `reviewer` scope.

## Output Contract

For `generate`, return:

- the artifact or proposal scoped to the target repo;
- a short constitutional rationale;
- the laws applied or intentionally not applied;
- any blocking condition if generation cannot proceed safely.

For `review`, return the structured verdict below:

```markdown
## Constitutional Review Verdict

**Verdict:** ALLOW | WARN | REQUIRE_APPROVAL | BLOCK
**Mode:** review
**Target Repo Root:** <current cwd>
**Canonical Source Resolution:** <explicit | local-verified | remote-verified>
**Artifact Reviewed:** <path or artifact name>

### Laws Applied
- Ley I, Art. X — <short reason>
- Ley IV, Art. X — <short reason>
- Ley XII, Art. X — <short reason>

### Findings
| Severity | Law / Article | Evidence | Impact | Required Action |
|---|---|---|---|---|
| ... | ... | ... | ... | ... |

### Summary
<2-5 sentence decision summary>

### Next Actions
1. ...
2. ...
```

Evidence must stay concrete, cite the artifact, and distinguish design issues, jurisdiction issues, and missing-evidence issues.

## Resources

- `references/constitution-source-contract.md` — canonical source identity, verification, and boundary rules
- `references/constitutional-law-map.md` — operational law subset for `generate` and `review`
- `assets/generate-template.md` — request scaffold for constitutional generation
- `assets/review-template.md` — verdict scaffold for constitutional review
