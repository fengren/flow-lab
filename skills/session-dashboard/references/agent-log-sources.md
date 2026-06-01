# Agent Log Sources

Use this reference when adding or debugging provider adapters.

## Implemented

### Codex

Likely paths:

- `~/.codex/sessions/**/*.jsonl`

Known useful fields:

- `session_meta.payload.cwd`
- `session_meta.payload.timestamp`
- `response_item.payload.role`
- `event_msg.payload.type == token_count`
- `event_msg.payload.info.total_token_usage.total_tokens`

Token rule: take the last cumulative token total per session.

### Claude Code

Likely paths:

- `~/.claude/projects/**/*.jsonl`

Known useful fields:

- top-level `type`
- top-level `timestamp`
- top-level `cwd`
- top-level `sessionId`
- `message.content`
- `message.usage.*_tokens`

Token rule: sum `message.usage.*_tokens` once per unique assistant message id.

## Candidate Providers

### Cursor

Observed candidate path:

- `~/.cursor/ai-tracking/ai-code-tracking.db`

Other possible paths:

- `~/.cursor/**`
- `~/Library/Application Support/Cursor/**`

Adapter approach:

1. Inspect SQLite schema with `sqlite3 <db> ".schema"`.
2. Identify conversation/session tables and message tables.
3. Map user messages, timestamps, project/workspace path, and token fields if available.

### OpenCode

Observed candidate paths:

- `~/.config/opencode/opencode.json`
- `~/.config/opencode/config.json`
- `~/.config/opencode/**`

Adapter approach:

1. Search for non-dependency JSON/JSONL/SQLite files under `~/.config/opencode`.
2. Ignore `node_modules`.
3. Add parser only after confirming where transcripts are stored.

### Trae

Candidate paths:

- `~/.trae/**`
- `~/Library/Application Support/Trae/**`
- `~/Library/Application Support/trae/**`

Adapter approach:

1. Search for JSONL/SQLite/LevelDB files.
2. Identify actual transcript records before adding parser.

### VS Code / Cline / Roo / Continue

Possible paths:

- `~/Library/Application Support/Code/User/globalStorage/**`
- `~/.continue/**`

Adapter approach:

1. Identify extension-specific storage directories.
2. Avoid parsing unrelated VS Code settings.

## Provider Contract

Every adapter returns a list of `Session` objects with:

- `source`
- `session_id`
- `cwd`
- `started_at`
- `file`
- `user_messages`
- `assistant_messages`
- `tool_calls`
- `line_count`
- `token_total`

