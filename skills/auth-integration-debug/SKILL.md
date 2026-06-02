---
name: auth-integration-debug
description: Use this skill when debugging login, OAuth, callback, QR code login, cookies, sessions, SSO, Feishu/Lark auth, WeChat auth, third-party integrations, or permission failures. Trigger on "登录不行", "扫码登录", "OAuth", "callback", "cookie", "鉴权", "飞书登录", "权限", "401/403", or external-service auth problems.
---

# Auth Integration Debug

Use this workflow to avoid random auth trial-and-error.

## First Split

Classify the failure:

- Configuration: app id, secret, redirect URI, scopes, domain allowlist, IP whitelist.
- Browser/session: cookies, SameSite, storage, profile, cross-origin redirects.
- Backend: callback handler, token exchange, user binding, org/tenant lookup.
- Permission: missing scope, role, app approval, environment mismatch.
- Network: proxy, blocked callback, TLS, timeout, external API status.

## Debug Flow

1. Capture the exact failing step and error.
2. Map the intended auth flow from entry to callback to session creation.
3. Check config values without exposing secrets.
4. Inspect logs around request id, user id, trace id, redirect URI, and status code.
5. Reproduce with a clean session if cookies may be stale.
6. Fix the smallest incorrect layer.
7. Verify end-to-end login and a protected action after login.

## Safety

- Never print full secrets, tokens, cookies, authorization codes, or refresh tokens.
- Redact app secrets and access tokens in reports.
- Do not commit `.env` or generated credential files.

## Final Response

Report:

- Failure layer.
- Root cause.
- Changed files/config.
- Verification performed.
- Remaining external-console action, if any.
