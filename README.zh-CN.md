# Flow Lab

Flow Lab 是一个本地 AI Coding Session 分析工具。它会读取本机 Code Agent 的会话日志，整理出工作方式、活跃度、token 消耗、任务类型、开发语言信号、工具使用情况，并生成一个可离线打开的 HTML 数据看板。

真实看板默认只在本地使用。生成的 HTML 可能包含 prompt 摘录、项目名称、本地路径、token 统计和工作习惯等敏感信息，提交或分享前必须脱敏。

## 示例预览

下面的截图由 mock 数据生成，不包含真实会话内容：

![Flow Lab dashboard preview](examples/dashboard-preview.png)

也可以直接打开示例 HTML：

```text
examples/mock-dashboard.html
```

## 适用场景

- 整理 Codex、Claude Code 等 AI coding session。
- 生成本地 HTML 数据看板。
- 查看全年度活跃矩阵，类似 GitHub 个人首页贡献图。
- 在活跃矩阵中切换“对话数”和“Token 消耗”。
- 点击矩阵日期查看当天的具体对话数和 token 消耗。
- 分析工作方式、工作流、任务类型和效率瓶颈。
- 根据 session 内容推断开发语言和技术栈占比。
- 提炼可复用的 Skills，优化后续开发模式。

## 功能

- 解析 Codex 和 Claude Code 本地会话日志。
- 生成单文件 HTML Dashboard。
- 展示年度活跃矩阵。
- 统计 session 数、有效需求数、token 总消耗、工具调用和 Agent 来源。
- 统计任务类别、项目分布、高频触发词和工具调用 Top。
- 只基于 session 内容推断开发语言信号。
- 给出工作优化建议和候选 Skill。
- 对常见密钥、token、密码和长 opaque secret 做基础脱敏。
- 支持 mock 数据模式，用于公开演示和截图。

## 快速开始

在仓库根目录运行：

```bash
python3 scripts/build_session_dashboard.py --output session_workflow_dashboard.html
```

或者运行 Skill 包内脚本：

```bash
python3 skills/session-dashboard/scripts/build_session_dashboard.py --output session_workflow_dashboard.html
```

然后用浏览器打开生成的 `session_workflow_dashboard.html`。

## 生成公开示例

mock 模式不会读取本地 session，只会使用脚本内置的公开演示数据：

```bash
python3 scripts/build_session_dashboard.py --mock --output examples/mock-dashboard.html
```

这个命令适合生成 README 截图或公开演示页面。

## 安装成 Codex Skill

Skill 包位于：

```text
skills/session-dashboard/
```

把它复制或软链接到 Codex skills 目录：

```bash
mkdir -p ~/.codex/skills
cp -R skills/session-dashboard ~/.codex/skills/session-dashboard
```

重启或新开一个 Codex 会话后，可以这样使用：

```text
使用 session-dashboard skill，整理我的 Codex 和 Claude session，生成 HTML 数据看板。
```

```text
根据本地 Code Agent 会话，分析我的工作方式、活跃矩阵、token 总消耗、开发语言占比和可提炼的 skills。
```

## 脚本参数

- `--output <path>`：指定生成的 HTML 文件路径。
- `--mock`：使用公开 mock 数据，不读取本地 session 日志。

示例：

```bash
python3 scripts/build_session_dashboard.py --mock --output /tmp/flow-lab-demo.html
```

## 当前支持的日志来源

已实现：

- Codex：`~/.codex/sessions/**/*.jsonl`
- Claude Code：`~/.claude/projects/**/*.jsonl`

计划扩展：

- Cursor
- OpenCode
- Trae
- VS Code Agent 扩展，例如 Cline、Roo、Continue

Provider 存储位置和适配器约定见：

```text
skills/session-dashboard/references/agent-log-sources.md
```

## 隐私和脱敏

Flow Lab 读取本地日志并生成本地 HTML。真实生成物不应该直接提交到公开仓库。

分享前请检查：

- prompt 摘录和项目名称。
- 本地路径、主机名、URL、内部服务名。
- token 统计和工作活跃模式。
- 是否包含 API key、access key、secret、password、cookie、账号信息等。

内置脱敏只是基础防护，不等同于完整的数据泄漏防护。

## 目录结构

```text
.
├── README.md
├── README.zh-CN.md
├── examples/
│   ├── dashboard-preview.png
│   └── mock-dashboard.html
├── scripts/
│   └── build_session_dashboard.py
└── skills/
    └── session-dashboard/
        ├── SKILL.md
        ├── references/
        │   └── agent-log-sources.md
        └── scripts/
            └── build_session_dashboard.py
```

## 扩展新的 Code Agent

每个 Agent 增加一个 parser，例如：

```python
def parse_cursor() -> list[Session]:
    ...
```

parser 需要返回统一的 `Session` 结构：

- `source`
- `session_id`
- `cwd`
- `started_at`
- `user_messages`
- `assistant_messages`
- `tool_calls`
- `token_total`
- `line_count`

如果日志存储在 SQLite 中，优先使用 Python 标准库 `sqlite3`，不要轻易引入额外依赖。

## 开发验证

真实日志 smoke test：

```bash
python3 skills/session-dashboard/scripts/build_session_dashboard.py --output /tmp/session-dashboard.html
```

mock 数据 smoke test：

```bash
python3 scripts/build_session_dashboard.py --mock --output /tmp/session-dashboard-mock.html
```
