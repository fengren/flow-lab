---
name: service-forwarding-architecture
description: Use this skill when designing or reviewing service forwarding, reverse proxy, OpenResty/Nginx routing, dynamic registration, external service exposure, control-plane/data-plane boundaries, tenant routing, auth at the edge, or traffic policy. Trigger on "外部转发", "OpenResty", "动态注册发现", "控制面", "数据面", "代理", "路由", "网关", or "鉴权管控".
---

# Service Forwarding Architecture

Use this workflow to keep forwarding designs explicit and reviewable.

## Architecture Split

Separate:

- Control plane: config, registration, policy, tenant/project ownership.
- Data plane: request routing, proxying, retries, headers, streaming, timeouts.
- Identity plane: authentication, authorization, token propagation, audit.
- Observability: logs, metrics, traces, request ids, error taxonomy.

## Review Questions

- Who is allowed to create or change a route?
- How is route config validated before traffic reaches it?
- What headers are trusted, rewritten, or stripped?
- Where does auth happen: before proxy, after proxy, or both?
- What are timeout, retry, body size, and streaming rules?
- How are tenant/project boundaries enforced?
- What is the rollback path for bad config?

## Implementation Guidance

- Keep route config typed and validated.
- Avoid embedding secrets in route definitions.
- Add audit logs for config changes.
- Log request ids and target service ids without leaking tokens.
- Prefer explicit deny-by-default behavior.

## Final Response

Include a short diagram or bullet flow when helpful:

`client -> edge auth -> route policy -> upstream -> response`
