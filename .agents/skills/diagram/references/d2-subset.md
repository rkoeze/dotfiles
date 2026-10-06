# D2 subset for repository explanations

The workflow targets a small language subset, not every D2 feature. D2 0.9.0 is a
reference baseline, not a promise of compiler compatibility. Record the installed
compiler version when available; use a repository-pinned version when available.

## Shapes, labels, and explicit declarations

```d2
direction: right

handler: "Handler\nChecks input and delegates"
store: "Record store" {
  shape: cylinder
}

handler -> store: "writes validated record"
```

Use simple lowercase IDs with underscores. Quote display labels, especially when
they include punctuation. Use `\n` inside quoted strings for short line breaks.
D2 IDs are case-insensitive: do not distinguish components only by case.

Declare every shape before using it in an edge. D2 permits implicit shape creation,
so `handler -> stroe` may compile as an unintended third shape. Manually reconcile declarations and endpoints with the README evidence table.

## Containers

```d2
app: "Application (logical grouping)" {
  handler: "HTTP handler"
  service: "Domain operation"
}

# E01
app.handler -> app.service: "calls operation"
```

Use fully qualified paths for connections outside containers. Cite `app`, `app.handler`, and `app.service` in the output README when all three make
semantic claims. Container IDs and labels are not interchangeable. Prefer two
nesting levels or fewer. Do not use package boundaries as process boundaries.

## Connections and styles

```d2
producer: "Producer"
queue: "Queue adapter"

producer -> queue: "publishes event [inferred]" {
  style.stroke-dash: 4
}
```

Use one directed connection per declaration. Avoid chained edges: each hop needs its own supporting evidence and label. Avoid bidirectional arrows when two directed arrows would
explain different operations. Use line style only as reinforcement for a textual
legend. Do not use the same dashed style ambiguously for return messages,
asynchrony, and uncertainty.

## Sequence diagrams

```d2
shape: sequence_diagram

caller: "Caller"
service: "Service"
store: "Store"

caller -> service: "1. submit(record)"
service -> store: "2. save(record)"
store -> service: "3. save returns"
service -> caller: "4. operation returns"
```

Declare all actors before messages. Message declaration order controls sequence
order. The numbered labels above are optional; do not claim order across truly
concurrent events. Use self-messages for meaningful local steps, not every helper.

Keep branches in separate scenario diagrams initially. D2 groups have special
sequence scoping rules; consult the official sequence documentation before using
them. Activation spans and nested participant paths can create unintended objects
when written incorrectly. Prefer the simple pattern above.

## Conditional flows

```d2
check: "Input valid?" {
  shape: diamond
}
accept: "Continue"
reject: "Return validation error"

check -> accept: "yes"
check -> reject: "no"
```

Every branch label is a claim. Match predicates and outcomes to the implementation.
A deliberately omitted branch belongs in the caption's scope/omissions.

## Annotations

For a short standalone callout:

```d2
takeaway: "Key point: validation precedes persistence." {
  shape: text
}
```

Behavioral callouts need evidence, just like arrows. An unconnected text object
may be positioned differently by layout engines; confirm its location visually.
A concise Markdown caption in the output README is often more predictable.

D2 also supports block text and highlighted code, for example:

```d2
explanation: |md
  **Important boundary:** accepted is not necessarily completed.
|
```

Prefer plain labels initially. Markdown and highlighted snippets add rendering
complexity. Do not include a code block unless it explains an otherwise unclear
mechanism. Avoid changing global fonts or adding decorative icons.

## Layout and rendering

Use ELK by default and inspect `d2 layout` for installed engines. Do not assume
engine-specific placement features work in every engine. Prefer changing the
abstraction or splitting a graph over intricate positional constraints.

If D2 is available, run `d2 validate <view>.d2` and
`d2 <view>.d2 <view>.svg`. Check exit status: a preexisting image may be stale after
a compiler error.

Use one diagram per file. Do not use imports, remote assets, globs, layers,
scenarios, animation, or external layout plugins in the initial pass. Broaden the
subset only for a clear explanatory need, with explicit validation and review.
Do not run untrusted D2 files without reviewing them.

## Official references

Consult only as needed for syntax or version differences; do not upload repository
content to these services.

- Syntax: https://d2lang.com/tour/shapes/
- Connections: https://d2lang.com/tour/connections/
- Containers: https://d2lang.com/tour/containers/
- Sequence diagrams: https://d2lang.com/tour/sequence-diagrams/
- Text and code: https://d2lang.com/tour/text/
- Layouts: https://d2lang.com/tour/layouts/
- Exports: https://d2lang.com/tour/exports/
- CLI: https://d2lang.com/tour/man/
- Releases: https://github.com/d2lang/d2/releases
