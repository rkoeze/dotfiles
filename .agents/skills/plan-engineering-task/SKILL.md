---
name: plan-engineering-task
description: Convert a loosely specified engineering task into a clear, actionable execution plan with assumptions, scope, workstreams, dependencies, risks, validation steps, and open questions. Use when a request is ambiguous, under-scoped, missing implementation detail, or needs to be turned into an engineer-ready plan before coding, delegation, estimation, or project kickoff.
---

# Plan Engineering Task

## Overview

Turn a vague engineering ask into a plan that another engineer or agent can execute with minimal back-and-forth. Surface uncertainty explicitly instead of hiding it behind overconfident detail.

## Workflow

1. Restate the task in concrete terms.
2. Extract known constraints, goals, and missing information.
3. Make bounded assumptions where progress is possible.
4. Decompose the work into execution-sized chunks.
5. Add dependencies, risks, and validation criteria.
6. End with open questions that would materially change the plan.

## Build The Plan

Start by converting the request into a compact problem statement:

- State the user outcome.
- State the likely system or surface area affected.
- State the success condition.

Then capture context in this order:

- Facts: Requirements stated directly by the user or already present in the repo/context.
- Assumptions: Reasonable defaults that unblock planning.
- Unknowns: Gaps that could change architecture, sequencing, or effort.
- Constraints: Timeline, tooling, compatibility, ownership, performance, security, rollout, or testing requirements.

If critical unknowns prevent a useful plan, say so plainly and ask focused follow-up questions. If the task is still plannable, proceed and label assumptions clearly.

## Decompose The Work

Break the task into workstreams that are concrete enough to execute:

- Discovery or design work needed before implementation
- Code changes by subsystem or layer
- Data, API, infra, migration, or config changes
- Test and verification work
- Deployment, rollout, and monitoring work when relevant

For each workstream, describe:

- Objective
- Key steps
- Dependencies
- Primary risks or failure modes
- Definition of done

Prefer sequence when ordering matters. Prefer parallel tracks when they are truly independent.

## Calibrate Detail

Match the plan depth to the request:

- Small task: Give a short sequence of concrete implementation steps plus validation.
- Medium task: Use grouped workstreams with assumptions and risks.
- Large or ambiguous task: Provide phases, decision points, and explicit unknowns.

Do not invent low-value precision. If sizing is requested, use rough ranges and explain the main drivers.

## Output Format

Use this structure unless the user asks for a different format:

### Objective

One short paragraph describing the intended outcome.

### Assumptions

List only assumptions that matter to execution.

### Proposed Plan

Use numbered steps or grouped workstreams. Each item should be actionable and specific.

### Risks And Dependencies

Call out blockers, sequencing constraints, and areas likely to need stakeholder input.

### Validation

Describe how to confirm the work is correct: tests, manual checks, metrics, rollout checks, or acceptance criteria.

### Open Questions

List only the unanswered questions that could change the plan.

## Quality Bar

Ensure the plan is:

- Actionable: Another engineer can start from it immediately.
- Honest: Unknowns and assumptions are visible.
- Scoped: Avoid mixing must-have work with optional nice-to-haves.
- Testable: Include a credible validation path.
- Efficient: Avoid unnecessary process overhead for small tasks.

## Example Triggers

Use this skill for requests like:

- "Turn this rough feature idea into an implementation plan."
- "We need to clean up our auth flow. What work should we do?"
- "Plan the migration from REST endpoints to GraphQL."
- "Break this incident follow-up into engineering tasks."
- "Given this repo and a vague ticket, produce an execution plan."
