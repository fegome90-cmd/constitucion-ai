# Constitution Source Contract

## Purpose

Define how `agentic-constitution-anchor` identifies, verifies, and uses a canonical constitutional source without collapsing it into the target repository.

## Core Surfaces

| Surface | Meaning | Allowed use |
|---|---|---|
| `constitution_source` | Canonical constitution repository or verified remote snapshot | read-only governance source |
| `target_repo_root` | Current working repository where the task happens | write/review scope |

These surfaces are distinct by default. If they appear to be the same location, the skill must not silently accept that assumption.

## Resolution Order

Resolve `constitution_source` in this strict order:

1. **Explicit source from the user**
2. **Verified local checkout of `constitucion-ai`**
3. **Verified remote canonical source**
4. **BLOCK** if none can be verified

## Verified Source Requirements

A source is considered verified only if all of these hold:

- it contains `constitution/AGENTIC-CONSTITUTION.md`;
- its identity matches the expected constitutional project by name, structure, or declared canonical remote;
- it does not contradict the known constitutional source of truth;
- if remote, it is traceable to an explicit ref, revision, or immutable retrieval point.

## Boundary Rules

1. Never treat `constitution_source` as the default write surface.
2. Never infer that the source repo is also the target repo.
3. Any generated working path must be relative to `target_repo_root`.
4. Source-repo paths may appear only as explicit references, never as generated output destinations.
5. If the target repo cannot be identified clearly, stop in closed-fail mode.

## Closed-Fail Conditions

Return `BLOCK` when:

- the target repo root is ambiguous;
- the canonical source cannot be verified;
- source and target paths are mixed in one result;
- the request needs a second target repo;
- the action would require sensitive or governance capabilities not declared by the mode.
