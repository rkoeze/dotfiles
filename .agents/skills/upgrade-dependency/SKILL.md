---
name: upgrade-dependency
description: Upgrade a project dependency safely by identifying the current and target versions, reviewing release notes and breaking changes, updating manifests and lockfiles, fixing compatibility issues, and validating the result. Use when Codex needs to bump a library, framework, SDK, toolchain package, or transitive dependency in any ecosystem, especially when the upgrade may require code changes, config changes, migrations, or targeted testing.
---

# Upgrade Dependency

## Overview

Upgrade dependencies methodically instead of treating version bumps as blind search-and-replace. Separate version discovery, impact analysis, code changes, and validation so the upgrade is easy to reason about and easy to review.

## Workflow

1. Identify the dependency, current version, target version, and package manager.
2. Find where the dependency is declared and how it is used.
3. Review changelogs, migration guides, peer dependencies, and breaking changes.
4. Update manifests and lockfiles using the project's normal package management workflow.
5. Fix code, configuration, or build changes required by the new version.
6. Run focused validation, then broader regression checks as risk warrants.
7. Summarize the impact, residual risk, and any follow-up work.

## Gather Context

Before changing anything, confirm:

- Which package is being upgraded
- Current version and requested target version
- Whether the change is a patch, minor, major, or toolchain jump
- Which files declare or pin the dependency
- Whether there are transitive constraints, peer dependencies, or workspace-wide impacts
- Which tests, builds, or runtime paths are most likely to break

If the target version is unspecified, choose the most defensible default for the task and state it clearly.

## Evaluate Upgrade Risk

Classify the upgrade before editing code:

- Low risk: Patch or minor bump with no public API changes and minimal surface area
- Medium risk: Minor or major bump with limited usage or straightforward migration notes
- High risk: Major bump, framework upgrade, compiler/runtime/toolchain change, or dependency used across critical paths

Increase validation depth as risk increases.

## Execute The Upgrade

Perform the change in this order:

1. Update the dependency declaration using the ecosystem's standard files and conventions.
2. Regenerate or update lockfiles rather than hand-editing them unless the ecosystem explicitly requires it.
3. Review install output for peer dependency conflicts, deprecations, or post-install migration hints.
4. Update code, config, generated artifacts, or build settings required by the new version.
5. Keep the diff scoped to upgrade-related changes unless unrelated fixes are necessary to restore compatibility.

Prefer the project's existing package manager and task runner. Do not switch tools just because another workflow is familiar.

## Validate The Result

Choose validation based on impact:

- Always run the narrowest install/build/test command that proves the upgrade is coherent.
- Run dependency-specific or affected-area tests when the package has clear usage boundaries.
- Run broader test suites, type checks, lint, builds, or smoke tests for major upgrades or shared infrastructure packages.
- If the dependency affects production behavior, note rollout or monitoring checks that should follow merge/deploy.

If validation cannot be completed, say exactly what was not run and why.

## Output Format

Use this structure unless the user asks for another format:

### Upgrade Summary

State the dependency, old version, new version, and why the upgrade was made.

### Impact

Describe the important code, config, or behavior changes introduced by the upgrade.

### Validation

List what was run, what passed, and what remains unverified.

### Risks

Call out remaining uncertainty, runtime risk, or follow-up work.

## Quality Bar

Ensure the upgrade is:

- Evidence-based: Use release notes or primary docs when the change is non-trivial.
- Scoped: Avoid opportunistic refactors mixed into the upgrade diff.
- Compatible: Resolve peer deps, generated files, and config drift.
- Verified: Match test depth to upgrade risk.
- Transparent: State assumptions, skipped checks, and unresolved warnings.

## Example Triggers

Use this skill for requests like:

- "Upgrade React from 18 to 19 in this app."
- "Bump the OpenAI SDK and fix any breakages."
- "Update this Terraform provider safely."
- "Move this project to the latest Django minor."
- "Upgrade a vulnerable dependency and verify the patch."
