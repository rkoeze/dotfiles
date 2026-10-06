# Investigating a repository

## Begin with a question

A useful scope might be "How does an incoming webhook become a persisted event?"
or "How do the compiler's intermediate representations change between phases?"
The skill applies to libraries, CLIs, compilers, data pipelines, and infrastructure
code as well as web applications. Do not impose a client/API/database template.

For a broad request, inspect entry points and identify the highest-value path.
Write down the chosen question and the reason that path is representative.
A small, justified slice is better than an unsupported map of the entire system.

## Establish the local facts

Inspect applicable `AGENTS.md` instructions and existing docs. Use focused commands
such as `git status --short`, `git rev-parse HEAD`, `rg --files`, and `rg -n` as
appropriate. Respect ignore rules and local conventions. Read the relevant ranges
with line numbers rather than dumping large files. Read nearby context when a
search match hides guards, registration, or a different overload.

Locate manifests, public exports, executable entry points, router registrations,
framework bootstrapping, dependency injection, configuration defaults, schemas,
and tests. Record the working-tree state and relevant local modifications. Do
not execute a repository-provided script solely because its name sounds useful.
Do not inspect secret values when configuration names and types suffice.

## Trace one path end to end

For each hop, determine:

1. What triggers it and where the handler is registered.
2. Which implementation is reached, including runtime wiring and configuration.
3. What data crosses the boundary and in which direction.
4. What it changes, returns, emits, or persists.
5. What changes the path or prevents the expected outcome.

Read enough to establish the relationship; avoid expanding every helper.
An aggregate "parser" node can represent many implementation files. Cite the
composition and critical behavior that justify the aggregate.

## Evidence standards

An import proves availability or a dependency, not invocation. An interface proves
an abstraction, not which concrete implementation runs. A registration proves a
handler is configured, not that an event is emitted in every deployment. A test
mock proves neither a remote service's behavior nor the production wiring.

Configuration proves what can be selected. Checked-in deployment files describe
a deployment configuration, not necessarily what is live. Distinguish configured,
possible, and observed behavior in both labels and explanation.

Read both sides of relationships crossing processes or libraries. For a queue,
match the producer's destination and message type to the consumer's registration.
For a database, check the actual read/write, schema, and transaction ownership.
For a library callback, check where it is registered and where it is invoked.
When source is unavailable, describe only the adapter or public contract inspected.

## Common semantic traps

- `async`/`await` does not automatically imply another process or durable work.
- A publish call returning does not automatically imply persistence or delivery.
- A successful HTTP acceptance response need not imply completed processing.
- The producer's response and consumer's start may be unordered relative to each
  other; do not invent a happens-before relationship in a sequence.
- A transaction boundary requires evidence of where it starts and commits.
- Authentication and authorization are separate behaviors; do not combine them
  into a generic security box without showing what the code actually checks.
- Retries may be in a client library or broker rather than visible in a handler;
  absence in one function is not proof of absence everywhere.
- A foreign key, object reference, and network call are different relationships.
- A lock, cache, or singleton may be local to one process rather than global.
- A directory boundary is not automatically a service or deployment boundary.

## Use tests and runtime checks carefully

Tests can identify exceptions, intended contracts, and misleading edge cases.
Read setup and fixtures to understand what was mocked. A passing test supports
its exercised case, not every deployment or scheduling interleaving.

Execute only relevant, safe, authorized tests using existing tooling. Do not
install dependencies, use production credentials, or start external services
just to make a documentation claim. Record exactly what was run and its result.
Static inspection is an acceptable evidence source when represented accurately.

## Resolve uncertainty without fabricating completeness

Classify a direct implementation/configuration claim as supported when the cited
code establishes it. Mark deductions as inferred and state the premise. Mark
missing runtime wiring or external internals as unknown. Explicitly searched but
unresolved questions belong in the output, not behind plausible-looking arrows.

For negative claims, bound the assertion: "No retry was found in the inspected
handler and client configuration" is more defensible than "This system never
retries." Do not label a path unreachable without sufficient proof.

Stop when the question is answered, each visible claim has evidence or uncertainty,
and further reading would add detail rather than change the mental model.
