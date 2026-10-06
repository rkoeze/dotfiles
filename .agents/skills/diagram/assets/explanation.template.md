# <Topic>: <main takeaway>

## Question and scope

**Question:** <the actual question this set of views answers>

**Audience and scope:** <audience, included slice, excluded scope>

**Inspected revision:** <commit or unknown>; working tree <clean/dirty/unknown>.
<Identify relevant local modifications when present.>

## Main view

<One sentence explaining what this diagram makes clear.>

![<Meaningful alt text describing the main flow>](overview.svg)

<Embed only an existing, successfully rendered, current image. If rendering is
unavailable, link the .d2 source and state that no validated image is provided.>

<Walk through the main path in a short paragraph. Cite code anchors using
repository-relative paths, symbols, and exact line ranges.>

## Focused view

<Delete this section unless a second view answers a distinct, useful question.>

## Evidence and qualifications

| Diagram elements and claim | Code anchors | Qualification |
| --- | --- | --- |
| <node or edge: concise statement> | <path:start-end, symbol> | <condition or limitation> |

**Unknowns:** <unresolved questions and why they matter, or none in this scope>

**Omissions:** <deliberately excluded detail, not a blanket completeness claim>

## Verification

- Evidence review: <which source anchors and diagram elements were checked>.
- D2: <actual version and validation/export results, or not available>.
- Semantic review: <which implementation paths/claims were rechecked>.
- Visual review: <image and tool actually used, or not performed and why>.
- Repository tests: <exact relevant checks run, or not run>.

## Maintenance

<Describe which changes to entry points, wiring, configuration, schema, or behavior
should trigger a recheck. Reread the code anchors and compare the evidence table
with the diagrams. If D2 is available, validate and rerender from this directory:>

```sh
d2 validate overview.d2
d2 overview.d2 overview.svg
```

<Review the final image when possible. Do not link stale exports.>
