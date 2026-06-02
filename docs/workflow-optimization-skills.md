# 工作流程优化建议与 Skill 提炼

这些 Skills 基于本地 session 内容里的高频模式提炼，命名不使用个人或团队前缀，方便迁移到不同 Agent 环境。

## 总体建议

1. 把“实现/修复/Review/提交”固定成闭环流程。
   不要让任务停在代码修改阶段，默认补上验收标准、验证、风险复查和提交前安全检查。

2. 把前端任务从“改样式”升级成“对齐设计并截图验证”。
   前端改动需要稳定检查桌面、移动端、文本溢出、交互状态和视觉一致性。

3. 把登录/鉴权问题分层排查。
   先区分配置、浏览器 session、后端 callback、权限、网络，再动手修。

4. 中断后先恢复上下文。
   每次“继续”先输出目标、已完成、未完成、阻塞点和下一步，避免重复探索。

5. 公开发布和 GitHub 提交默认走脱敏流程。
   真实 session dashboard、prompt 摘录、token 统计、内部 URL、AppSecret 都不能直接进入公开仓库。

6. 用日志/监控作为行为验证证据。
   对运行时问题，不只看代码，还要确认日志、指标、trace 或 analytics 是否符合预期。

## 生成的 Skills

- `implementation-review-loop`：实现、修复、Review、验证闭环。
- `frontend-design-parity`：前端设计稿对齐和截图验证。
- `auth-integration-debug`：登录、OAuth、callback、cookie、权限排查。
- `session-resume`：中断或压缩上下文后的状态恢复。
- `service-forwarding-architecture`：服务转发、代理、控制面/数据面架构审查。
- `observability-local-stack`：日志、Loki、Grafana、analytics、trace 验证。
- `secret-hygiene`：密钥、token、账号、路径、报告脱敏。
- `release-readiness-check`：提交、推送、发布前检查。

## 建议使用方式

把 `skills/<name>/` 复制到本地 agent skill 目录后，在任务中直接触发：

```text
用 implementation-review-loop 处理这个修复，最后检查风险并提交。
```

```text
用 frontend-design-parity 对照设计稿检查这个页面。
```

```text
用 secret-hygiene 检查这次准备提交的内容是否有敏感信息。
```

```text
用 session-resume 先恢复上下文，然后继续完成任务。
```
