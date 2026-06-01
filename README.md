# Flow Lab

Flow Lab is a local session analytics tool for AI coding agents. It parses local agent logs, extracts high-level activity signals, and generates a standalone HTML dashboard for reviewing work patterns, activity, token usage, language signals, and reusable skill opportunities.

The tool is designed for private, local analysis first. Generated dashboards can contain derived session content, prompt excerpts, local paths, project names, token totals, and other personal workflow metadata, so generated reports should not be committed to a public repository.

## Features

- Parse local Codex and Claude Code session logs.
- Generate a standalone HTML dashboard.
- Show yearly activity as a GitHub-style matrix.
- Switch the matrix between conversation count and token consumption.
- Click matrix cells to inspect the exact daily values.
- Summarize total sessions, effective prompts, token usage, tool calls, sources, projects, and inferred task categories.
- Infer development language distribution from session text signals.
- Surface workflow optimization suggestions and candidate skills.
- Apply best-effort redaction for common secret patterns before rendering excerpts.

## Quick Start

Run from the repository root:

```bash
python3 scripts/build_session_dashboard.py --output session_workflow_dashboard.html
```

Or run the skill-local script:

```bash
python3 skills/session-dashboard/scripts/build_session_dashboard.py --output session_workflow_dashboard.html
```

Then open the generated `session_workflow_dashboard.html` locally in a browser.

## Supported Sources

Implemented adapters:

- Codex: `~/.codex/sessions/**/*.jsonl`
- Claude Code: `~/.claude/projects/**/*.jsonl`

Documented extension targets:

- Cursor
- OpenCode
- Trae
- VS Code agent extensions such as Cline, Roo, and Continue

See [agent-log-sources.md](skills/session-dashboard/references/agent-log-sources.md) for adapter notes and expected parser contracts.

## Privacy Notes

Flow Lab reads local session logs and produces a local HTML report. The generated report is intentionally ignored by Git because it may contain sensitive workflow metadata.

Before sharing any generated dashboard:

- Review prompt excerpts and project names.
- Check local paths, hostnames, URLs, and internal service names.
- Confirm token usage and activity patterns are acceptable to disclose.
- Treat built-in redaction as a helper, not a complete data-loss-prevention system.

## Skill Package

The reusable Codex skill lives in:

```text
skills/session-dashboard/
```

The skill describes when to use the dashboard generator, how to parse agent logs, how token totals are computed, and how to add provider adapters.

## Development

The project currently uses only the Python standard library.

Run a smoke test:

```bash
python3 skills/session-dashboard/scripts/build_session_dashboard.py --output /tmp/session-dashboard.html
```

The output file is a local artifact and should not be committed.
