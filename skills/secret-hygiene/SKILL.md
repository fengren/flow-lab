---
name: secret-hygiene
description: Use this skill whenever a task touches .env files, API keys, AppID/AppSecret, tokens, cookies, credentials, IP allowlists, auth headers, private URLs, generated reports, screenshots, or public commits. Trigger on "脱敏", "token", "secret", "password", "AK/SK", "AppSecret", ".env", "cookie", "白名单", "发布到 GitHub", or "公开分享".
---

# Secret Hygiene

Use this workflow to prevent accidental credential or personal-data leaks.

## Before Editing Or Publishing

Classify data:

- Secret: API key, token, password, app secret, cookie, private key.
- Sensitive metadata: internal domain, IP, local path, account id, project name.
- Personal workflow data: prompts, session reports, token usage, screenshots.

## Rules

- Do not commit secrets or real personal session dashboards.
- Prefer environment variables for one-off publishing commands.
- Redact secrets in logs and final responses.
- Add generated personal reports to `.gitignore`.
- Treat built-in redaction as best effort, not complete protection.

## Scan Patterns

Use focused scans before commit or publication:

```bash
rg -n "AKIA|LTAI|BEGIN .*PRIVATE KEY|client_secret|password|passwd|api[_-]?key|access[_-]?key|token|cookie|AppSecret"
```

Also scan for internal:

```bash
rg -n "192\\.168|10\\.|172\\.16|localhost|/Users/|internal|staging|prod"
```

## Final Response

State:

- What was scanned.
- What was excluded.
- Whether any sensitive value was found.
- What remains local only.
