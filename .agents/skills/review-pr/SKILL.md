---
name: review-pr
description: Invoke this when the user explicitly asks to review a pull request, branch diff, or commit range (e.g. /review-pr). Returns structured feedback on architectural concerns, blocking issues, nits, and risks.
user-invocable: true
---

# Pull Request Review

Coordinate four focused review subagents and summarize their findings as
architectural concerns, blocking issues, nits, and risks.

## Step 1 — Parse the argument and resolve the diff target

The argument selects what to diff. If no diff target is given, default to
reviewing the current branch against `main` (fall back to `master` if `main`
does not exist). Otherwise, resolve the target per this table. Examples below
use `main`; substitute `master` if `main` doesn't exist.

| Argument           | Meaning                              | How to fetch the diff                  |
| ------------------ | ------------------------------------ | -------------------------------------- |
| _(none)_           | Current branch vs `main`             | `git diff main...HEAD`                 |
| `<branch>`         | Named branch vs `main`               | `git diff main...<branch>`             |
| `<base>...<head>`  | Explicit commit or branch range      | `git diff <base>...<head>`             |

If the target is ambiguous, ask the user before proceeding.

## Step 2 — Gather available review context

- Use any PR description, requirements, or design notes supplied by the user
  or available in the repository to understand the intended behavior.
- If no additional context is available, proceed with the diff and repository
  alone; do not require an issue tracker or external integration.
- Keep stated intent separate from verified behavior. Step 4 checks the change
  against this context.

## Step 3 — Map the diff

Pure orientation, no judgment yet. The goal of this step is to decide where to
spend time, not to form findings.

- Identify which packages/services changed and how the changes connect — new
  files, deleted files, cross-module touches.
- Read changed tests, migrations, config, and interface boundaries first
  because they define the intended behavior and blast radius.
- Spot the high-signal areas to scrutinize later: persistence, auth,
  permissions, background jobs, caching, external APIs, concurrency,
  migrations, and deploy-sensitive code.
- Read any AGENTS.md found on the path from each changed file up to the repo
  root, plus AGENTS.md in any package the diff imports from.

## Step 4 — Delegate the investigations

Launch four fresh-context, read-only subagents, in parallel when supported.
Each investigates only its assigned angle:

- **Wrong claims:** Check claims in comments, docs, and PR context against
  code and tests, including compatibility, caller updates, and coverage.
- **Missed call sites:** Trace changed symbols/contracts to consumers outside
  the diff, including indirect/dynamic uses still expecting old behavior.
- **Contradictions:** Find incompatible behavior or assumptions across code,
  tests, schemas, config, and acceptance criteria. Cite both sides and impact.
- **Designs that won't work as intended:** Trace execution end to end; identify
  reachable failures in invariants, integration, state, concurrency, error
  handling, or deployment—not alternative design preferences.

Give each agent the same repo/cwd, base/head commit IDs, diff command, changed
files, relevant symbols, available review context (or gaps), applicable
AGENTS.md, and the category rules/review standards below.

No edits, checkout changes, publication, recursive skill invocation, or further
subagents. Report access/ref problems instead of guessing. Return concise,
verified findings: category, source `path:line`, evidence, trigger, impact, and
how the diff introduces/exposes the issue. Separate checks run from reasoning
and coverage gaps; return `None.` if no supported findings.

## Step 5 — Summarize the subagent findings

The main reviewer summarizes only; no independent code-review pass.

- Collect all four reports; disclose failures and coverage gaps.
- Deduplicate by root cause, categorize using the rules below, and preserve
  verified citations. Omit unsupported or unrelated pre-existing issues.
- Send missing evidence or conflicting findings back to the responsible agent;
  unresolved uncertainty belongs under risks, not blockers.
- Produce one consolidated review in the format below, without agent transcripts
  or unsupported new claims.

## Category rules

These define what belongs in each output bucket.

**Architectural concerns** — design problems that materially increase
maintenance cost or make future change unsafe.

- Flag unclear ownership, duplicated business logic, hidden coupling, invalid
  layering, leaky abstractions, or poor extension points.
- Explain why the design is brittle and what kind of restructuring would reduce
  the problem.
- Do not use this bucket for stylistic cleanup or one-off correctness bugs.

**Blocking issues** — defects or omissions that should prevent merge until
fixed.

- Include correctness bugs, security problems, data loss hazards, broken
  migrations, contract violations, and obvious performance regressions on
  critical paths.
- Include missing tests when the uncovered path is critical enough that merging
  would be unsafe.
- State the failure mode, who or what is impacted, and the condition that
  triggers it.

**Nits** — low-severity polish that does not block merge.

- Include naming, readability, small consistency issues, minor test cleanup, or
  comments that would make the code easier to maintain.
- Keep these brief.
- Do not let nits crowd out more important findings.

**Risks** — credible uncertainty that is not yet proven to be a blocker.

- Include rollout concerns, edge cases worth validating, unclear deploy
  ordering, monitoring gaps, assumptions about production data, or partial test
  coverage in non-critical areas.
- Be explicit that the point is a risk, what evidence suggests it, and how to
  reduce uncertainty.
- If evidence becomes strong enough to show an actual defect, move it to
  blocking issues.

## Review standards

- Cite concrete evidence with real `file_path:line_number` references whenever
  possible; if you genuinely cannot resolve a line, name the file and symbol
  rather than guessing a number.
- Prefer source-backed findings. If a concern is mostly speculative, place it
  under risks instead of blockers.
  suggestions.
- Separate design feedback from merge blockers.
- Do not invent feedback to fill a category. If a bucket is empty, say `None.`
  explicitly.
- Order items by severity within each category.

## Output format

Open with a short summary paragraph — **no heading, no bullets, 1–3
sentences**. Sentence 1 states what the change does. Sentence 2 gives the
overall assessment. If requirements were supplied, sentence 3 (or a clause in
sentence 2) states whether the change satisfies them. Then leave a blank line
and go straight to `### Architectural concerns`.

Example opening (style only, not content):

> This branch adds a `/foo` endpoint to the bar-service and wires it into the
> shared router. The change is small and largely safe to merge, with one piece
> of the stated scope missing — see Risks.

Use these exact section headings in this order:

### Architectural concerns

- One bullet per finding with file references and concrete reasoning.
- Say `None.` if there is nothing worth calling out.

### Blocking issues

- One bullet per finding with file references, impact, and failure mode.
- Say `None.` if there is nothing merge-blocking.

### Nits

- One bullet per nit.
- Say `None.` if there are no meaningful nits.

### Risks

- One bullet per risk with evidence and the missing validation or mitigation.
- Say `None.` if there are no material risks beyond the listed findings.

Keep the closing summary short. The four categories are the primary output.
