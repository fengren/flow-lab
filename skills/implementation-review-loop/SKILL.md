---
name: implementation-review-loop
description: Use this skill when the user asks to implement, fix, continue, review, validate, or commit code changes. It turns open-ended coding work into a closed loop: clarify acceptance criteria, make scoped changes, run focused verification, review risks, and report what changed. Trigger especially on phrases like "实现", "修复", "继续完成", "review", "检查代码", "如果没问题就提交", "评估风险点", or when a task mixes coding and validation.
---

# Implementation Review Loop

Use this workflow to keep implementation tasks from ending at "code changed" without verification.

## Workflow

1. Restate the goal in one sentence.
2. Write 3-6 concrete acceptance criteria before editing.
3. Inspect the smallest relevant code surface first.
4. Make scoped changes only.
5. Run the narrowest meaningful verification.
6. Review for regressions, edge cases, and missing tests.
7. Report changed files, verification, residual risk, and next action.

## Acceptance Criteria

Prefer criteria that can be checked:

- User-visible behavior changed as requested.
- Existing behavior outside the scope is preserved.
- Errors, empty states, retries, permissions, or boundary inputs are handled.
- Tests, builds, screenshots, logs, or command outputs confirm the result.
- No unrelated files or generated personal data are committed.

## Code Review Pass

Before finishing, explicitly check:

- Contract changes: API shape, database schema, env vars, CLI flags, event names.
- Hidden coupling: shared helpers, global state, caches, feature flags, auth state.
- Failure modes: null values, missing config, timeouts, retries, race conditions.
- Compatibility: browser/device, framework version, dependency behavior.
- Test gaps: what was verified and what remains unverified.

## Final Response

Use this shape:

```text
Done.

Changed:
- ...

Verified:
- ...

Residual risk:
- ...
```

If nothing was changed, say so directly and explain why.
