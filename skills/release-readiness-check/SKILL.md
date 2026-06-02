---
name: release-readiness-check
description: Use this skill before commits, pushes, PRs, releases, tags, GitHub Actions changes, deployment config changes, or when the user says "如果没问题就提交", "发布", "CI", "tag", "push", "上线", or "提交到 GitHub". It ensures verification, secret hygiene, and change summary happen before shipping.
---

# Release Readiness Check

Use this workflow before shipping changes.

## Checklist

1. Inspect `git status --short --ignored`.
2. Separate intended changes from ignored/local personal artifacts.
3. Run focused tests/builds/lints for the changed surface.
4. Run secret hygiene scan on files to be committed.
5. Review generated artifacts: only commit public-safe examples.
6. Summarize changes and verification.
7. Commit/push only after the above is complete or explicitly waived.

## Commit Readiness

A change is ready when:

- The diff matches the user request.
- Verification passed or limitations are documented.
- No real secrets, local reports, private dashboards, or credentials are staged.
- README/docs reflect new behavior when needed.
- Any external action still needed is clearly stated.

## Final Response

Use:

```text
Ready status: ready / not ready
Verification:
- ...
Safety:
- ...
Commit/push:
- ...
```
