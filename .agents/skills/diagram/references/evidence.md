# Evidence for diagrams

Cite the implementation behind every meaningful node, boundary, connection,
condition, and behavioral callout. Keep a compact table in the output README with
claims and repository-relative paths, symbols, and narrow 1-based line ranges.
Group elements supported by the same code where useful. Purely decorative labels
do not need citations.

Check actual wiring and call sites, not just imports or interfaces. Tests can help
identify expected behavior, but distinguish test expectations from production
code. Mark uncertain relationships `[inferred]` or `[unknown]` in the diagram and
explain the reason in the README. Do not cite unrelated code to make a guess look
supported. Record the inspected revision and whether local changes were present.

Before delivery, reread the cited source and compare it with the final D2. Confirm
each declared node and edge endpoint, label, direction, condition, and claimed
boundary. D2 may silently create shapes for misspelled endpoints. If an image was
rendered, check that it reflects the current `.d2` source. When updating diagrams,
reassess changed behavior rather than simply shifting line numbers.
