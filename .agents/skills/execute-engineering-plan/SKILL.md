---
name: execute-engineering-plan
description: Execute an existing engineering implementation plan inside the current repository. Use when the user already has a plan, task breakdown, spec, or output from $plan-engineering-task and wants Codex to carry it through by inspecting the codebase, sequencing the work, making code changes, validating results, and reporting any deviations or blockers.
---

# Execute Engineering Plan

## Overview

Execute the plan that already exists instead of re-planning it. Treat the plan as the intended outcome, then adapt it to the actual repository state, fill in missing implementation detail locally, and complete the work with verification.

## Workflow

1. Restate the execution target in concrete terms.
2. Inspect the repository surfaces the plan appears to affect.
3. Translate the plan into implementation-sized actions for this codebase.
4. Execute changes in a safe order, validating after meaningful increments.
5. Report completed work, validation results, and any plan drift.

## Read The Plan

Extract these items before editing code:

- User outcome
- Required constraints and non-goals
- Ordered steps or workstreams
- Dependencies or prerequisites
- Validation expectations
- Open questions or explicit assumptions

If the plan came from `$plan-engineering-task`, preserve its scope discipline. Do not silently expand the work into adjacent cleanup unless required to complete the planned outcome.

If the plan is ambiguous but still executable, make bounded assumptions and continue. If ambiguity would cause likely rework, stop and surface the exact decision point.

## Build Local Execution Context

Inspect the codebase before choosing an implementation path.

- Find the files, modules, tests, configs, and docs the plan likely touches.
- Check whether the repository already partially implements the plan.
- Identify conflicts between the plan and the current codebase.
- Note user-made uncommitted changes in touched files and work with them rather than reverting them.

Convert the plan into a local execution sequence:

- Discovery tasks needed to unblock coding
- Implementation tasks grouped by subsystem
- Test and verification tasks
- Migration, rollout, or documentation tasks if the plan requires them

Prefer the smallest sequence that produces a working, verifiable result.

## Execute In Increments

Carry out the plan in discrete increments instead of one large edit.

For each increment:

1. State the next implementation target.
2. Edit the necessary files only.
3. Run the narrowest useful validation.
4. Confirm whether the result matches the plan before moving on.

Sequence work according to dependency order:

- Schema or contract changes before dependent code
- Core logic before integration wiring
- Integration wiring before end-to-end verification
- Tests close to the changed behavior, not deferred to the very end

When the plan includes multiple independent tracks, execute the highest-confidence path first so the user gets concrete progress quickly.

## Handle Plan Drift

Plan drift is expected. Handle it explicitly.

- If the repository already solved part of the plan, skip redundant work and say so.
- If a planned step is invalid for the current codebase, replace it with the closest correct implementation and explain the change.
- If new blockers appear, finish unaffected work first when possible, then report the blocker precisely.
- If the plan is missing a necessary step that is clearly implied by correctness, add it and label it as an execution-time adjustment.

Do not claim to have executed the plan literally if the codebase required a different sequence. Report the delta.

## Validate Against The Plan

Use the strongest validation available within the repo and environment:

- Existing unit, integration, or end-to-end tests
- Targeted test additions when coverage is missing around changed behavior
- Type checks, linters, builds, or static analysis relevant to the touched area
- Manual verification steps when automation is unavailable

Map validation back to the original plan:

- Which planned acceptance criteria are now satisfied
- Which items were partially validated
- Which items could not be validated and why

## Communicate Progress

While executing:

- Give short updates describing what part of the plan is being implemented.
- Call out new facts that materially change sequencing or scope.
- Announce edits before making them.

At completion:

- Summarize what was implemented.
- List validation actually run.
- State any remaining gaps, follow-up work, or unresolved questions.

## Default Decision Rules

- Prefer execution over re-planning.
- Prefer local evidence from the repository over assumptions from the plan.
- Prefer minimal, reversible changes over broad refactors unless the plan explicitly requires broader work.
- Prefer finishing one coherent slice with validation over spreading partial edits across many files.
- Ask for user input only when a decision would materially change architecture, product behavior, or destructive impact.
