---
name: diagram-architecture
description: Diagram a codebase's architecture and system design using D2. Use when asked to visualize components, service boundaries, dependencies, or request, event, and data flows.
---

# Diagram Architecture

Explain how the system works, not its directory tree or every function call.

## Workflow
1. Scope to the requested repository or subsystem; default to the current repository's runtime architecture. Ask only if the target is unclear.
2. Read project guidance, README, manifests, entrypoints, service wiring, storage/messaging adapters, and deployment config. Trace the main flow in code; treat docs as leads, not proof.
3. Choose one abstraction level: systems/services by default, major modules for a single application. Show responsibilities, meaningful boundaries, stores, and external integrations.
4. Aim for at most 12 nodes in one overview. Label arrows with actions and known protocols/events; distinguish synchronous calls from asynchronous messaging. Omit incidental dependencies and decorative styling.
5. Ground nodes and edges in code/config; add concise `# path:line` evidence comments. Mark uncertainty rather than inventing relationships; separate proposed designs from current behavior.
6. Save `docs/architecture.d2`, or use the requested/existing diagram location. Keep stable IDs, short labels, and minimal D2; change only diagram artifacts.

## D2
Syntax sketch only; replace these components and flows with repository evidence:
```d2
direction: right
user: User
system: Application {
  api: API
  db: Database {shape: cylinder}
  api -> db: reads/writes
}
user -> system.api: HTTPS request
```

## Validate and deliver
- Run `d2 fmt docs/architecture.d2 && d2 validate docs/architecture.d2 && d2 --layout dagre docs/architecture.d2 docs/architecture.svg`; adapt paths as needed.
- Inspect the rendered diagram when possible; simplify clutter, crossings, and unreadable labels before adding detail.
- If D2 is unavailable, deliver the source and report that validation/rendering were not run; do not install tools without approval.
- Return links to the D2/SVG artifacts, a brief explanation of boundaries and the main flow, and any uncertainties. Never claim checks you did not run.
