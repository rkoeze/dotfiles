---
name: hunk
description: Invoke this when the user explicitly asks to prepare Hunk for use via /hunk. Locate and load Hunk's bundled agent skill, and explain how to start a review later. Do not open the Hunk TUI or start a review.
---

# Prepare Hunk

This skill prepares the current agent session to work with Hunk. It does **not** start or perform a review.

1. Run `hunk skill path` to locate the review skill bundled with the installed Hunk version.
2. Read the file at that path in full. Use that guidance for any later Hunk review request in this session. Resolve the path again on a future invocation so it stays aligned with Hunk upgrades.
3. Tell the user Hunk is ready. When they want to begin, **they** can run `hunk diff` in their own terminal and keep the window open, then ask the agent to work with that live session.

Do not run `hunk diff`, `hunk show`, or another interactive Hunk command. Do not run `hunk session` commands, inspect a diff, navigate, or leave comments as part of preparation. Wait for an explicit request to begin review work.
