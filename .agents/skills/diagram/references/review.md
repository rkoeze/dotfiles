# Review and evaluation

## Semantic review

Ask these questions against the actual code, not just the existing explanation.

- Does every visible component, grouping, boundary, callout, and edge have a
  defensible implementation basis or an explicit uncertainty label?
- Are all edge endpoints explicitly declared and consistent with the README evidence table? Are there
  phantom nodes, duplicate names differing only by case, or orphaned components?
- Does the view keep a coherent abstraction level and distinguish code structure
  from processes/deployment and runtime control flow from data flow?
- Are conditions, configuration, errors, and scheduling constraints accurate?
  Does a simplifying omission change the conclusion?
- Are "synchronous", "durable", "committed", "authorized", "retried", and similar
  guarantees supported, or merely suggested by a function/library name?
- Does the sequence assert only known ordering? Could a worker begin before the
  producer responds? Does the picture falsely impose a total order?
- Are test-only adapters, mocks, example configs, and stale docs represented as
  such, rather than as live production components?
- Can the reader explain the principal outcome using the picture's labels alone?

## Visual review

Open the final exported image. Check a normal viewing scale and closer detail.
Confirm that main-path labels are legible, text is not clipped, branches are
unambiguous, arrows reach the intended nodes, and boundaries are identifiable.
Check that the important path does not disappear among incidental dependencies.
Ensure callouts do not look like connected components or alter the reading order.

Readable diagrams usually have short labels, ample space, limited nesting, and
few crossings. Split views before producing a giant image with tiny text. Verify
that grayscale/text labels still convey any essential distinctions. For a sequence,
check actor ordering and message order, not only the left-to-right arrangement.

After an edit, rerender and inspect again. Report what tool/artifact was inspected.
If no visual inspection was possible, say so explicitly.

## Evaluation prompts for the skill owner

Use a repository you know. Keep the model and tool environment fixed. Run each
case more than once; compare facts and usefulness rather than exact coordinates.

| Prompt | What to look for |
| --- | --- |
| `Explain this repository to a new maintainer with a diagram.` | Chooses and discloses useful scope; does not dump every file. |
| `Diagram how [operation] reaches persistence.` | Traces actual entry/wiring/write and states the takeaway. |
| `Diagram [failure case or feature flag].` | Shows real conditions; does not invent retries or alternate paths. |
| `Update these diagrams after the refactor.` | Rechecks sources and relationships, not just labels or timestamps. |
| `Diagram this library's public API execution.` | Does not force a web-service architecture onto a library. |
| `Explain this function in prose; do not create diagrams.` | Does not activate this skill unnecessarily. |

Adversarial checks: misleading README, test-only service, misspelled D2 endpoint,
feature-gated implementation, consumer/response race, unavailable compiler, and
unavailable image viewer. Check that errors are disclosed rather than hidden.

## Suggested scorecard

Score separately, from 0 (unacceptable) to 2 (meets expectations): source fidelity,
important conditions, abstraction, explanatory value, visual readability, and
maintainability. An unsupported guarantee or unlabeled fabricated relationship is
a correctness failure regardless of the aggregate score.

Measure syntax repairs and render failures separately from semantic failures.
Rendering successfully is not a passing evaluation by itself. A successful render does not evaluate the agent's ability to understand an
unfamiliar real repository.
