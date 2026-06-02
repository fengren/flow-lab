---
name: session-resume
description: Use this skill when the user says "继续", "接着做", "status", "恢复上下文", "从刚才继续", or after an interrupted/compacted coding session. It reconstructs state before acting so the agent does not repeat exploration or lose partially completed work.
---

# Session Resume

Use this workflow before continuing interrupted work.

## Resume Snapshot

Start by producing a compact state summary:

- Goal: what we are trying to finish.
- Done: completed edits, commands, publications, or decisions.
- Pending: remaining tasks.
- Blockers: approvals, credentials, external console changes, failing commands.
- Local state: dirty files, running processes, generated artifacts.
- Next action: the single next step.

## Checks

Run only focused checks:

- `git status --short --ignored` for repo state.
- Relevant process check if a server, browser automation, or publish command may still be running.
- Read the latest changed files if continuing edits.

## Avoid

- Re-reading the whole repo.
- Repeating already successful commands.
- Overwriting user changes.
- Treating ignored personal generated files as publishable artifacts.

## Final Response

If continuing work, keep the status short and then proceed.
If blocked, state the exact blocker and the user action needed.
