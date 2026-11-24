# Constitutional Law Map

## Purpose

Provide the minimum operational law subset for `agentic-constitution-anchor` so the skill applies the constitution proportionally instead of injecting the entire document every time.

## Primary Law Subset

| Law | Articles to reach for first | Why it matters to this skill |
|---|---|---|
| Ley I — cambio legítimo | Art. 1, 3, 4, 6 | Requires explicit intent, prior validation, evidence, and coherence between plan, execution, and review |
| Ley II — lectura previa y no duplicación | Art. 1, 2, 3, 4 | Forces reading before creation and blocks unnecessary duplication |
| Ley III — arquitectura base | Art. 3, 5, 7 | Prevents ornamental overengineering and keeps scope aligned with usage |
| Ley IV — control de versiones y aislamiento | Art. 2, 3, 4, 7 | Requires identifiable branch, isolated worktree, traceability, and workspace hygiene |
| Ley VI — fuente de verdad | Art. 1, 2, 3, 4, 6 | Establishes canonical source identity and reconciliation obligations |
| Ley VIII — seguridad agéntica | Art. 1, 2, 3, 4, 14 | Applies least privilege, explicit access, closed-fail behavior, capability separation, and human approval for sensitive actions |
| Ley XII — roles y jurisdicción | Art. 1, 2, 3, 6 | Defines capability model and the ALLOW/WARN/REQUIRE_APPROVAL/BLOCK verdict space |
| Ley XIII — primacía conceptual | Art. 1, 3, 5, 6 | Keeps implementation subordinate to justified technical reasoning |

## Mode Slicing

### `generate`

Default constitutional slice:

- Ley I
- Ley II
- Ley III
- Ley IV
- Ley VI
- Ley XII

Escalate Ley VIII only when the requested artifact touches sensitive surfaces or elevated permissions.

### `review`

Default constitutional slice:

- Ley I
- Ley II
- Ley IV
- Ley VI
- Ley VIII
- Ley XII

Use Ley III when the artifact introduces unnecessary architectural machinery. Use Ley XIII when the artifact jumps to implementation without technical justification.

## Practical Review Lens

When emitting a review verdict, check these questions in order:

1. Is the intent explicit and is validation defined? (Ley I)
2. Was the existing context read and reused instead of duplicated? (Ley II)
3. Are source and target surfaces cleanly separated? (Ley VI + Ley XII)
4. Is the execution isolated, traceable, and hygienic? (Ley IV)
5. Does the requested act stay within role/capability boundaries? (Ley VIII + Ley XII)
6. Is the solution proportionate instead of ornamental? (Ley III)

## v1 Verdict Expectations

- `ALLOW` when the artifact is scoped, justified, verifiable, and jurisdiction-safe.
- `WARN` when the artifact is directionally correct but still leaves debt or ambiguity.
- `REQUIRE_APPROVAL` when the action crosses into sensitive or governed surfaces.
- `BLOCK` when the target is ambiguous, the source is unverified, or the constitutional boundary is broken.
