---
name: session-dashboard
description: Generate an HTML dashboard from local Code Agent session logs. Use when the user asks to analyze, summarize, visualize, or dashboard their AI coding sessions across Codex, Claude Code, Cursor, OpenCode, Trae, or other code agents; includes workflow patterns, activity matrix, token totals, project/category distribution, and skill recommendations.
---

# Session Dashboard

Create a local HTML dashboard from AI coding agent session logs.

## When To Use

Use this skill when the user asks to:

- 统计、整理、分析 AI coding session / 会话记录
- 生成 session dashboard / 数据看板 / HTML 看板
- 分析工作方式、工作流、开发模式、效率、活跃度
- 统计 Codex、Claude、Cursor、OpenCode、Trae 等 Code Agent 的使用情况
- 统计 token 总消耗、活跃矩阵、项目分布、任务类别、触发词、工具调用
- 从 session 中推断开发语言占比

## Quick Start

Run the bundled script from the skill directory:

```bash
python3 scripts/build_session_dashboard.py --output session_workflow_dashboard.html
```

The script reads local logs and writes a standalone HTML file.

Default implemented adapters:

- Codex: `~/.codex/sessions/**/*.jsonl`
- Claude Code: `~/.claude/projects/**/*.jsonl`

Best-effort discovery targets for future adapters:

- Cursor: `~/.cursor/ai-tracking/ai-code-tracking.db`, `~/Library/Application Support/Cursor/**`
- OpenCode: `~/.config/opencode/**`
- Trae: `~/.trae/**`, `~/Library/Application Support/Trae/**`

If a requested agent is not supported yet, inspect its local storage format first, then add a parser function without changing the dashboard contract.

## Output

The dashboard should include:

- Overall KPIs: sessions, effective prompts, token total, source split, tool calls
- GitHub-like yearly activity matrix
- Matrix mode toggle: prompt count and token consumption
- Clickable matrix cells showing per-day prompt count and token count
- Category, project, source, phrase, and tool distributions
- Work optimization recommendations
- Candidate skills to extract
- Representative prompt excerpts with redaction

Do not embed full raw transcripts in the HTML.

## Parsing Rules

Use only local session content unless the user explicitly asks to scan code repositories.

Noise filtering:

- Ignore environment blocks, AGENTS/CLAUDE injected instructions, context continuation summaries, title-generation prompts, tool result payloads, and explicit `test`/`continue` commands.
- Keep real user requirements, bug reports, design feedback, and review requests.

Token accounting:

- Do not separate cache tokens unless requested.
- Claude: sum `message.usage.*_tokens` once per unique assistant message id.
- Codex: use the last cumulative `token_count.total_token_usage.total_tokens` per session, not every snapshot.

Security:

- Redact obvious API keys, tokens, passwords, AK/SK, and long opaque secrets.
- Do not quote full secret-bearing prompts in the final response.

## Language Inference

If asked for development language distribution based only on sessions:

- Use text signals from prompts, file extensions, commands, frameworks, and tool outputs.
- Examples: `.py`, `pytest`, Django -> Python; `.go`, `go test` -> Go; `.vue`, Vite -> Vue/TypeScript; `cargo`, `.rs` -> Rust.
- Label the metric as inferred from session text, not code volume.
- Prefer two views: language signal count and primary language per session.

## Extending Agent Support

Add one parser per provider:

```python
def parse_cursor() -> list[Session]:
    ...
```

Each parser should produce the common `Session` shape:

- `source`
- `session_id`
- `cwd`
- `started_at`
- `user_messages`
- `assistant_messages`
- `tool_calls`
- `token_total`
- `line_count`

Then include it in `build_data()`:

```python
sessions = parse_codex() + parse_claude() + parse_cursor()
```

If storage is SQLite, use Python stdlib `sqlite3`; do not add dependencies unless necessary.

## Final Response

After running the script, report:

- Output HTML path
- Which providers were parsed
- Session count, effective prompt count, token total
- Any providers requested but not supported or not found

