#!/usr/bin/env python3
"""Build a local HTML dashboard from Codex and Claude session logs."""

from __future__ import annotations

import html
import argparse
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


HOME = Path.home()
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = Path.cwd() / "session_workflow_dashboard.html"


NOISE_EXACT = {"test", "continue", "status", "继续", "Flex", "go", "开始", "需要", "ok 开始任务", ""}
NOISE_PREFIXES = (
    "<environment_context>",
    "# AGENTS.md instructions",
    "<turn_aborted>",
    "<goal_context>",
    "# Context from my IDE setup:",
    "<ide_opened_file>",
    "Caveat: The messages below were generated",
    "This session is being continued from a previous conversation",
    "Base directory for this skill:",
    "- You are a conversation title generator.",
    "You are running as a local coding agent for a Multica workspace.",
    "[Request interrupted by user",
    "Compacted (ctrl+o to see full summary)",
)

CATEGORIES: dict[str, list[str]] = {
    "架构/产品决策": ["架构", "为什么", "是否", "需要", "设计", "PRD", "策略", "方案", "能否", "可以", "边界", "职责"],
    "实现/修复功能": ["实现", "修复", "完成", "继续完成", "添加", "支持", "接入", "优化", "调整", "修改", "开发"],
    "前端/设计稿/UI": ["页面", "前端", "设计稿", "样式", "UI", "hero", "Flexible", "Toast", "抽屉", "视频", "Pricing", "布局", "按钮"],
    "发布/CI/Git": ["commit", "提交", "github action", "CI", "版本", "PR", "发布", "tag", "merge", "push"],
    "文档/飞书/知识整理": ["文档", "docs", "飞书", "wiki", "表格", "Markdown", "整理", "会议", "审批", "知识库"],
    "数据/日志/监控": ["日志", "loki", "grafana", "GA", "analytics", "采集", "session", "token", "提示词", "看板", "监控"],
    "登录/鉴权/外部服务": ["登录", "飞书", "扫码", "鉴权", "外部", "转发", "openresty", "oauth", "服务", "callback", "cookie"],
    "审查/风险评估": ["review", "审查", "评估风险", "风险点", "检查代码", "分析代码逻辑", "本次修改", "改动", "regression"],
}

PHRASES = [
    "Review",
    "评估风险点",
    "分析",
    "检查",
    "继续完成",
    "整理代码",
    "修复",
    "调整",
    "为什么",
    "是否",
    "是否可以",
    "重新",
    "再次",
    "对照",
    "根据",
    "帮我",
    "需要",
]

SECRET_PATTERNS = [
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bLTAI[0-9A-Za-z]{16,}\b"),
    re.compile(r"(?i)\b(sk|token|secret|password|passwd|ak|as|access[_-]?key|api[_-]?key)\s*[:=]\s*['\"]?[^'\"\s]{8,}"),
    re.compile(r"\b[A-Za-z0-9_\-]{32,}\b"),
]


@dataclass
class Session:
    source: str
    session_id: str
    cwd: str
    started_at: str
    file: str
    user_messages: list[str] = field(default_factory=list)
    assistant_messages: int = 0
    tool_calls: Counter[str] = field(default_factory=Counter)
    line_count: int = 0
    token_total: int = 0

    @property
    def meaningful_messages(self) -> list[str]:
        return [m for m in (clean_prompt(x) for x in self.user_messages) if m]


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def redact(text: str) -> str:
    value = text
    for pattern in SECRET_PATTERNS:
        value = pattern.sub("[REDACTED]", value)
    return value


def normalize_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                if item.get("type") == "text":
                    parts.append(str(item.get("text", "")))
                elif item.get("type") in {"input_text", "output_text"}:
                    parts.append(str(item.get("text", "")))
                elif "content" in item:
                    parts.append(normalize_text(item.get("content")))
        return "\n".join(p for p in parts if p)
    if isinstance(value, dict):
        if "text" in value:
            return str(value.get("text", ""))
        if "content" in value:
            return normalize_text(value.get("content"))
    return ""


def clean_prompt(text: str) -> str:
    value = redact(text).strip()
    if not value or value in NOISE_EXACT:
        return ""
    if "The user interrupted the previous turn" in value:
        return ""
    match = re.search(r"My request for Codex:\s*(.*)", value, re.S)
    if match:
        value = match.group(1).strip()
    value = re.sub(r"<ide_opened_file>.*?</ide_opened_file>", " ", value, flags=re.S)
    value = re.sub(r"<[^>]{1,80}>", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    if value in NOISE_EXACT:
        return ""
    if value in {"/clear", "/compact", "/clear clear", "/compact compact", "- Respond with hello."}:
        return ""
    if re.fullmatch(r"\d{4}-\d{2}-\d{2} [A-Za-z/_]+", value):
        return ""
    if re.fullmatch(r"[/\w ._-]+ zsh \d{4}-\d{2}-\d{2} [A-Za-z/_]+", value):
        return ""
    if any(value.startswith(prefix) for prefix in NOISE_PREFIXES):
        return ""
    return value


def read_jsonl(path: Path):
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def usage_token_total(usage: dict[str, Any] | None) -> int:
    if not isinstance(usage, dict):
        return 0
    total = 0
    for key, value in usage.items():
        if key.endswith("_tokens") and isinstance(value, int):
            total += value
    return total


def parse_codex() -> list[Session]:
    sessions: list[Session] = []
    for path in sorted((HOME / ".codex" / "sessions").glob("**/*.jsonl")):
        session = Session("Codex", path.stem, "", "", str(path))
        for obj in read_jsonl(path):
            session.line_count += 1
            payload = obj.get("payload") or {}
            if obj.get("type") == "session_meta":
                session.session_id = payload.get("id") or session.session_id
                session.started_at = payload.get("timestamp") or obj.get("timestamp") or session.started_at
                session.cwd = payload.get("cwd") or session.cwd
                continue
            if obj.get("type") == "event_msg" and payload.get("type") == "token_count":
                usage = ((payload.get("info") or {}).get("total_token_usage") or {})
                total = usage.get("total_tokens")
                if isinstance(total, int):
                    session.token_total = total
                continue
            if obj.get("type") != "response_item":
                continue
            kind = payload.get("type")
            if kind == "message":
                role = payload.get("role")
                text = normalize_text(payload.get("content") or [])
                if role == "user" and text:
                    session.user_messages.append(text)
                elif role == "assistant":
                    session.assistant_messages += 1
            elif kind == "function_call":
                name = payload.get("name") or "unknown"
                namespace = payload.get("namespace")
                session.tool_calls[f"{namespace}.{name}" if namespace else name] += 1
        if session.user_messages or session.tool_calls:
            sessions.append(session)
    return sessions


def parse_claude() -> list[Session]:
    sessions: list[Session] = []
    for path in sorted((HOME / ".claude" / "projects").glob("**/*.jsonl")):
        session = Session("Claude", path.stem, "", "", str(path))
        seen_usage_ids: set[str] = set()
        for obj in read_jsonl(path):
            session.line_count += 1
            session.session_id = obj.get("sessionId") or session.session_id
            session.started_at = session.started_at or obj.get("timestamp") or ""
            session.cwd = obj.get("cwd") or session.cwd
            typ = obj.get("type")
            msg = obj.get("message") or {}
            if typ == "user":
                content = msg.get("content")
                text = ""
                if isinstance(content, list):
                    text = normalize_text([item for item in content if isinstance(item, dict) and item.get("type") == "text"])
                else:
                    text = normalize_text(content)
                if text:
                    session.user_messages.append(text)
                for item in content if isinstance(content, list) else []:
                    if isinstance(item, dict) and item.get("type") == "tool_result":
                        session.tool_calls["tool_result"] += 1
            elif typ == "assistant":
                session.assistant_messages += 1
                message_id = str(msg.get("id") or obj.get("uuid") or "")
                if message_id and message_id not in seen_usage_ids:
                    seen_usage_ids.add(message_id)
                    session.token_total += usage_token_total(msg.get("usage"))
                content = msg.get("content") or []
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "tool_use":
                            session.tool_calls[item.get("name") or "tool_use"] += 1
            elif typ in {"tool_use", "tool_result"}:
                session.tool_calls[typ] += 1
        if session.user_messages or session.tool_calls:
            sessions.append(session)
    return sessions


def classify(text: str) -> list[str]:
    low = text.lower()
    found = []
    for category, keywords in CATEGORIES.items():
        if any(keyword.lower() in low for keyword in keywords):
            found.append(category)
    return found or ["其他"]


def project_name(cwd: str) -> str:
    if not cwd:
        return "(unknown)"
    path = Path(cwd)
    parts = path.parts
    if "Workspace" in parts:
        idx = parts.index("Workspace")
        return "/".join(parts[idx + 1 : idx + 3]) or cwd
    return str(path)


def top(counter: Counter[str], n: int) -> list[dict[str, Any]]:
    return [{"name": k, "value": v} for k, v in counter.most_common(n)]


def month_day(ts: str) -> str:
    parsed = parse_time(ts)
    return parsed.strftime("%m-%d") if parsed else "unknown"


def build_activity_matrix(daily_prompts: Counter[str], daily_tokens: Counter[str], year: int) -> dict[str, Any]:
    start = datetime(year, 1, 1)
    end = datetime(year, 12, 31)
    grid_start = start - timedelta(days=(start.weekday() + 1) % 7)
    grid_end = end + timedelta(days=(5 - end.weekday()) % 7)
    max_prompts = max(daily_prompts.values() or [0])
    max_tokens = max(daily_tokens.values() or [0])

    def level(value: int, max_value: int) -> int:
        if value <= 0:
            return 0
        if max_value <= 4:
            return min(4, value)
        ratio = value / max_value
        if ratio <= 0.25:
            return 1
        if ratio <= 0.5:
            return 2
        if ratio <= 0.75:
            return 3
        return 4

    days: list[dict[str, Any]] = []
    cursor = grid_start
    while cursor <= grid_end:
        key = cursor.strftime("%Y-%m-%d")
        prompts = daily_prompts.get(key, 0) if cursor.year == year else 0
        tokens = daily_tokens.get(key, 0) if cursor.year == year else 0
        days.append(
            {
                "date": key,
                "day": (cursor.weekday() + 1) % 7,
                "week": (cursor - grid_start).days // 7,
                "prompts": prompts,
                "tokens": tokens,
                "promptLevel": level(prompts, max_prompts),
                "tokenLevel": level(tokens, max_tokens),
                "inYear": cursor.year == year,
            }
        )
        cursor += timedelta(days=1)

    months: list[dict[str, Any]] = []
    cursor = start
    seen: set[tuple[int, int]] = set()
    while cursor <= end:
        marker = (cursor.year, cursor.month)
        if marker not in seen:
            seen.add(marker)
            months.append(
                {
                    "label": cursor.strftime("%b"),
                    "week": ((cursor - grid_start).days // 7),
                }
            )
        cursor += timedelta(days=1)

    active_prompt_days = sum(1 for value in daily_prompts.values() if value > 0)
    active_token_days = sum(1 for value in daily_tokens.values() if value > 0)
    return {
        "year": year,
        "days": days,
        "months": months,
        "maxPrompts": max_prompts,
        "maxTokens": max_tokens,
        "activePromptDays": active_prompt_days,
        "activeTokenDays": active_token_days,
        "totalPrompts": sum(daily_prompts.values()),
        "totalTokens": sum(daily_tokens.values()),
        "weeks": ((grid_end - grid_start).days // 7) + 1,
    }


def build_data() -> dict[str, Any]:
    sessions = parse_codex() + parse_claude()
    all_examples: list[dict[str, str]] = []
    category_counter: Counter[str] = Counter()
    project_counter: Counter[str] = Counter()
    source_counter: Counter[str] = Counter()
    timeline: Counter[str] = Counter()
    tool_counter: Counter[str] = Counter()
    phrase_counter: Counter[str] = Counter()
    source_prompt_counter: Counter[str] = Counter()
    daily_counter: Counter[str] = Counter()
    daily_token_counter: Counter[str] = Counter()

    for session in sessions:
        parsed_started = parse_time(session.started_at)
        day_key = parsed_started.strftime("%Y-%m-%d") if parsed_started else "unknown"
        message_count = len(session.meaningful_messages)
        source_counter[session.source] += 1
        project_counter[project_name(session.cwd)] += message_count
        timeline[f"{session.source}:{month_day(session.started_at)}"] += message_count
        if parsed_started and message_count:
            daily_counter[day_key] += message_count
        if parsed_started and session.token_total:
            daily_token_counter[day_key] += session.token_total
        tool_counter.update(session.tool_calls)
        for message in session.meaningful_messages:
            source_prompt_counter[session.source] += 1
            for category in classify(message):
                category_counter[category] += 1
            for phrase in PHRASES:
                if phrase.lower() in message.lower():
                    phrase_counter[phrase] += 1
            all_examples.append(
                {
                    "source": session.source,
                    "date": month_day(session.started_at),
                    "project": project_name(session.cwd),
                    "text": message[:180],
                }
            )

    started = [parse_time(s.started_at) for s in sessions if parse_time(s.started_at)]
    activity_year = max(started).year if started else datetime.now().year
    total_lines = sum(s.line_count for s in sessions)
    total_tools = sum(sum(s.tool_calls.values()) for s in sessions)
    total_assistant = sum(s.assistant_messages for s in sessions)
    total_tokens = sum(s.token_total for s in sessions)
    meaningful = sum(len(s.meaningful_messages) for s in sessions)

    examples: list[dict[str, str]] = []
    for source in ("Claude", "Codex"):
        source_examples = [item for item in all_examples if item["source"] == source and len(item["text"]) >= 8]
        if not source_examples:
            continue
        step = max(1, len(source_examples) // 40)
        examples.extend(source_examples[::step][:40])

    skill_candidates = [
        {
            "name": "ray-implementation-review-loop",
            "priority": "P0",
            "why": "覆盖实现、修复、Review、提交前检查的最高频闭环。",
            "triggers": "实现后 review / 修复后验证 / 如果没问题就提交",
        },
        {
            "name": "ray-frontend-design-parity",
            "priority": "P0",
            "why": "前端和设计稿对齐出现频繁，且需要截图验证和细节清单。",
            "triggers": "对照设计稿 / 样式差异 / 文案 icon 字号 颜色",
        },
        {
            "name": "ray-auth-integration-debug",
            "priority": "P1",
            "why": "飞书扫码、OAuth、callback、cookie 和多组织登录反复出现。",
            "triggers": "飞书登录不行 / 扫码登录 / callback 配置",
        },
        {
            "name": "ray-session-resume",
            "priority": "P1",
            "why": "中断和继续较多，需要稳定恢复上下文，减少重复探索。",
            "triggers": "继续 / status / 继续完成",
        },
        {
            "name": "ray-service-forwarding-architecture",
            "priority": "P1",
            "why": "外部服务转发、OpenResty、控制面/数据面边界需要固定审查口径。",
            "triggers": "外部转发 / OpenResty / 动态注册发现 / 鉴权管控",
        },
        {
            "name": "ray-observability-local-stack",
            "priority": "P2",
            "why": "日志、Loki、Grafana、GA、转发日志常作为验证手段。",
            "triggers": "loki / grafana / 日志没有报错 / 看板",
        },
        {
            "name": "ray-secret-hygiene",
            "priority": "P2",
            "why": "会话里出现密钥和账号排查，应默认脱敏并检查 diff。",
            "triggers": "aksk / token / .env / secret / 账号余额异常",
        },
    ]
    recommendations = [
        {
            "title": "把临时指令升级成固定流程",
            "body": "高频任务不要只说“Review”或“继续”，改成指定流程入口，让 agent 固定检查需求覆盖、风险、验证和提交条件。",
        },
        {
            "title": "拆分三类 Review",
            "body": "行为 Review 看 bug 和边界；架构 Review 看职责、扩展性、耦合；发布 Review 看配置、CI、部署、回滚。",
        },
        {
            "title": "任务开始先写验收标准",
            "body": "让 agent 在动手前列 5 行验收标准，尤其是登录、转发、前端对齐、监控和发布任务，减少只修表面问题。",
        },
        {
            "title": "中断后先恢复上下文",
            "body": "每次“继续”先输出已完成、未完成、阻塞点、下一步命令，再执行，避免重复读代码和重复试错。",
        },
        {
            "title": "沉淀高频专用 skills",
            "body": "优先落地 implementation-review-loop、frontend-design-parity、auth-integration-debug、session-resume、secret-hygiene。",
        },
        {
            "title": "敏感信息默认进入安全流程",
            "body": "涉及 .env、AK/SK、token、账号余额、外部平台配置时，默认脱敏、检查 diff，并避免把完整值写进报告或提交。",
        },
    ]
    prompt_template = (
        "用 [固定流程名] 处理这个任务。\n"
        "目标：...\n"
        "验收标准：...\n"
        "重点风险：...\n"
        "允许修改范围：...\n"
        "最后需要运行的验证：..."
    )

    return {
        "generatedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "range": {
            "start": min(started).strftime("%Y-%m-%d") if started else "-",
            "end": max(started).strftime("%Y-%m-%d") if started else "-",
        },
        "summary": {
            "sessions": len(sessions),
            "meaningfulPrompts": meaningful,
            "assistantMessages": total_assistant,
            "toolCalls": total_tools,
            "totalTokens": total_tokens,
            "rawLines": total_lines,
            "codexSessions": source_counter.get("Codex", 0),
            "claudeSessions": source_counter.get("Claude", 0),
            "codexPrompts": source_prompt_counter.get("Codex", 0),
            "claudePrompts": source_prompt_counter.get("Claude", 0),
        },
        "sources": top(source_prompt_counter, 10),
        "categories": top(category_counter, 12),
        "projects": top(project_counter, 18),
        "tools": top(tool_counter, 16),
        "phrases": top(phrase_counter, 20),
        "timeline": [{"name": k, "value": v} for k, v in sorted(timeline.items())],
        "activityMatrix": build_activity_matrix(daily_counter, daily_token_counter, activity_year),
        "recommendations": recommendations,
        "promptTemplate": prompt_template,
        "examples": examples,
        "skills": skill_candidates,
    }


def build_mock_data() -> dict[str, Any]:
    """Build public demo data without reading local session logs."""
    year = 2026
    daily_prompts: Counter[str] = Counter()
    daily_tokens: Counter[str] = Counter()
    for month in range(1, 7):
        for day in range(1, 29):
            if (day + month) % 3 == 0 or day in {5, 12, 19, 26}:
                key = f"{year}-{month:02d}-{day:02d}"
                prompts = ((day * month) % 9) + 2
                daily_prompts[key] = prompts
                daily_tokens[key] = prompts * (18000 + month * 1300 + day * 210)
    for key, prompts in {
        "2026-02-14": 18,
        "2026-03-03": 22,
        "2026-04-18": 20,
        "2026-05-21": 26,
        "2026-06-01": 16,
    }.items():
        daily_prompts[key] = prompts
        daily_tokens[key] = prompts * 42000

    recommendations = [
        {
            "title": "把临时指令升级成固定流程",
            "body": "把 Review、继续、对照设计稿、登录排查等高频动作沉淀成明确入口，减少重复解释。",
        },
        {
            "title": "任务开始先写验收标准",
            "body": "每个任务先明确目标、修改范围、验证方式和风险点，再进入实现。",
        },
        {
            "title": "中断后先恢复上下文",
            "body": "继续任务时先汇总已完成、未完成、阻塞点和下一步命令，再执行。",
        },
        {
            "title": "区分三类 Review",
            "body": "行为 Review 看 bug，架构 Review 看职责和耦合，发布 Review 看配置、CI 和回滚。",
        },
        {
            "title": "用截图关闭前端任务",
            "body": "前端改动用桌面和移动端截图验证布局、文案、溢出和交互状态。",
        },
        {
            "title": "敏感信息默认脱敏",
            "body": "涉及 token、密钥、账号、内部域名和本地路径时，先脱敏再生成报告或提交。",
        },
    ]
    prompt_template = (
        "用 session-dashboard 固定流程处理这个任务。\n"
        "目标：生成本地 AI coding session 看板。\n"
        "输入：Codex、Claude 或其他 Code Agent 的本地会话日志。\n"
        "输出：HTML Dashboard、活跃矩阵、token 总览、工作建议。\n"
        "安全要求：只使用本地数据，生成物提交前必须脱敏。"
    )
    return {
        "generatedAt": "2026-06-01 10:00:00",
        "range": {"start": "2026-01-01", "end": "2026-06-01"},
        "summary": {
            "sessions": 128,
            "meaningfulPrompts": 864,
            "assistantMessages": 3150,
            "toolCalls": 4860,
            "totalTokens": 742_680_000,
            "rawLines": 188_400,
            "codexSessions": 52,
            "claudeSessions": 76,
            "codexPrompts": 336,
            "claudePrompts": 528,
        },
        "sources": [{"name": "Claude", "value": 528}, {"name": "Codex", "value": 336}],
        "categories": [
            {"name": "实现/修复功能", "value": 244},
            {"name": "审查/风险评估", "value": 186},
            {"name": "前端/设计稿/UI", "value": 152},
            {"name": "架构/产品决策", "value": 116},
            {"name": "数据/日志/监控", "value": 92},
            {"name": "发布/CI/Git", "value": 74},
        ],
        "projects": [
            {"name": "example/flow-lab", "value": 220},
            {"name": "example/agent-platform", "value": 178},
            {"name": "example/frontend-console", "value": 141},
            {"name": "example/auth-service", "value": 118},
            {"name": "example/observability", "value": 86},
        ],
        "tools": [
            {"name": "exec_command", "value": 1680},
            {"name": "apply_patch", "value": 438},
            {"name": "browser.screenshot", "value": 126},
            {"name": "rg", "value": 1220},
            {"name": "git", "value": 394},
        ],
        "phrases": [
            {"name": "Review", "value": 132},
            {"name": "修复", "value": 118},
            {"name": "继续完成", "value": 96},
            {"name": "对照", "value": 74},
            {"name": "是否可以", "value": 62},
            {"name": "提交", "value": 58},
        ],
        "timeline": [],
        "activityMatrix": build_activity_matrix(daily_prompts, daily_tokens, year),
        "recommendations": recommendations,
        "promptTemplate": prompt_template,
        "examples": [
            {
                "source": "Codex",
                "date": "03-03",
                "project": "example/flow-lab",
                "text": "整理本地 AI coding session，生成 HTML 数据看板，包含全年活跃矩阵和 token 总览。",
            },
            {
                "source": "Claude",
                "date": "04-18",
                "project": "example/frontend-console",
                "text": "对照设计稿检查 Dashboard 的布局、矩阵热点大小、移动端文本溢出和交互细节。",
            },
            {
                "source": "Codex",
                "date": "05-21",
                "project": "example/auth-service",
                "text": "分析登录链路的失败原因，区分配置问题、回调问题、cookie 问题和权限问题。",
            },
            {
                "source": "Claude",
                "date": "06-01",
                "project": "example/agent-platform",
                "text": "把重复出现的工作流沉淀为可复用 Skill，并补充安装、运行和扩展说明。",
            },
        ],
        "skills": [
            {
                "name": "implementation-review-loop",
                "priority": "P0",
                "why": "覆盖实现、修复、验证和提交前检查。",
                "triggers": "实现后 review / 修复后验证 / 提交前检查",
            },
            {
                "name": "frontend-design-parity",
                "priority": "P0",
                "why": "前端任务需要稳定的截图和设计稿对齐流程。",
                "triggers": "对照设计稿 / 样式差异 / 移动端检查",
            },
            {
                "name": "session-resume",
                "priority": "P1",
                "why": "中断任务后需要先恢复上下文，避免重复探索。",
                "triggers": "继续 / status / 接着做",
            },
        ],
    }


def render_dashboard(data: dict[str, Any]) -> str:
    payload = json.dumps(data, ensure_ascii=False)
    safe_payload = payload.replace("</script", "<\\/script")
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>AI Session Workflow Dashboard</title>
  <style>
    :root {{
      --bg: #f7f8fb;
      --panel: #ffffff;
      --ink: #172033;
      --muted: #667085;
      --line: #e4e7ec;
      --blue: #2563eb;
      --green: #059669;
      --amber: #d97706;
      --red: #dc2626;
      --purple: #7c3aed;
      --radius: 8px;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.45;
    }}
    header {{
      padding: 28px 32px 18px;
      border-bottom: 1px solid var(--line);
      background: #fff;
    }}
    h1 {{ margin: 0 0 8px; font-size: 28px; letter-spacing: 0; }}
    h2 {{ margin: 0 0 14px; font-size: 18px; }}
    h3 {{ margin: 0 0 8px; font-size: 15px; }}
    .sub {{ color: var(--muted); font-size: 14px; }}
    main {{ padding: 24px 32px 40px; max-width: 1480px; margin: 0 auto; }}
    .grid {{ display: grid; gap: 16px; }}
    .kpis {{ grid-template-columns: repeat(6, minmax(140px, 1fr)); }}
    .two {{ grid-template-columns: 1.15fr .85fr; }}
    .three {{ grid-template-columns: repeat(3, 1fr); }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: var(--radius);
      padding: 18px;
      min-width: 0;
    }}
    .kpi .value {{ font-size: 28px; font-weight: 750; margin-top: 6px; }}
    .kpi .label {{ color: var(--muted); font-size: 13px; }}
    .bar-row {{ display: grid; grid-template-columns: minmax(140px, 260px) 1fr 54px; gap: 10px; align-items: center; margin: 9px 0; }}
    .bar-label {{ overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #344054; font-size: 13px; }}
    .bar-track {{ height: 10px; background: #eef2ff; border-radius: 999px; overflow: hidden; }}
    .bar-fill {{ height: 100%; background: var(--blue); border-radius: inherit; }}
    .bar-value {{ text-align: right; color: var(--muted); font-variant-numeric: tabular-nums; font-size: 12px; }}
    .stack {{ display: flex; flex-direction: column; gap: 10px; }}
    .skill {{
      display: grid;
      grid-template-columns: 54px 1fr;
      gap: 12px;
      padding: 12px;
      border: 1px solid var(--line);
      border-radius: var(--radius);
      background: #fcfcfd;
    }}
    .badge {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      height: 26px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 700;
      color: #fff;
      background: var(--blue);
    }}
    .badge.P1 {{ background: var(--purple); }}
    .badge.P2 {{ background: var(--green); }}
    .skill p {{ margin: 0; color: var(--muted); font-size: 13px; }}
    .examples {{ max-height: 560px; overflow: auto; padding-right: 4px; }}
    .example {{
      padding: 12px 0;
      border-bottom: 1px solid var(--line);
    }}
    .example:last-child {{ border-bottom: 0; }}
    .meta {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 5px; color: var(--muted); font-size: 12px; }}
    .pill {{ padding: 2px 7px; background: #f2f4f7; border-radius: 999px; }}
    .text {{ font-size: 13px; color: #344054; }}
    .insights {{
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
    }}
    .insight {{
      border-left: 3px solid var(--blue);
      padding: 10px 12px;
      background: #f8fafc;
      border-radius: 6px;
      font-size: 14px;
    }}
    .insight strong {{ display: block; margin-bottom: 4px; }}
    .recommendations {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
    }}
    .recommendation {{
      border: 1px solid var(--line);
      background: #fcfcfd;
      border-radius: var(--radius);
      padding: 14px;
      min-width: 0;
    }}
    .recommendation h3 {{ font-size: 14px; margin: 0 0 6px; }}
    .recommendation p {{ margin: 0; color: var(--muted); font-size: 13px; }}
    .prompt-template {{
      margin-top: 14px;
      padding: 12px;
      border-radius: var(--radius);
      background: #111827;
      color: #f9fafb;
      white-space: pre-wrap;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 13px;
      overflow-x: auto;
    }}
    .activity-head {{
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 12px;
      margin-bottom: 12px;
    }}
    .activity-summary {{ color: var(--muted); font-size: 13px; }}
    .activity-actions {{ display: flex; gap: 6px; align-items: center; }}
    .activity-mode {{
      border: 1px solid var(--line);
      background: #fff;
      color: #344054;
      border-radius: 999px;
      padding: 5px 10px;
      font-size: 12px;
      cursor: pointer;
    }}
    .activity-mode.active {{
      background: var(--blue);
      border-color: var(--blue);
      color: #fff;
    }}
    .activity-wrap {{ overflow-x: auto; padding-bottom: 4px; }}
    .activity-grid {{
      display: grid;
      grid-template-columns: 34px repeat(var(--weeks), 15px);
      grid-template-rows: 18px repeat(7, 15px);
      gap: 4px;
      min-width: max-content;
      align-items: center;
    }}
    .month-label {{
      color: var(--muted);
      font-size: 11px;
      line-height: 12px;
      white-space: nowrap;
    }}
    .weekday-label {{
      grid-column: 1;
      color: var(--muted);
      font-size: 11px;
      line-height: 12px;
    }}
    .day-cell {{
      width: 15px;
      height: 15px;
      border-radius: 3px;
      background: #ebedf0;
      outline: 1px solid rgba(23, 32, 51, 0.04);
      cursor: pointer;
    }}
    .day-cell.out {{ opacity: 0.32; }}
    .level-0 {{ background: #ebedf0; }}
    .level-1 {{ background: #dbeafe; }}
    .level-2 {{ background: #93c5fd; }}
    .level-3 {{ background: #3b82f6; }}
    .level-4 {{ background: #1d4ed8; }}
    .activity-legend {{
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 6px;
      margin-top: 10px;
      color: var(--muted);
      font-size: 12px;
    }}
    .legend-cell {{ width: 15px; height: 15px; border-radius: 3px; }}
    .activity-detail {{
      margin-top: 10px;
      min-height: 22px;
      color: var(--muted);
      font-size: 13px;
    }}
    footer {{ padding: 0 32px 28px; color: var(--muted); font-size: 12px; max-width: 1480px; margin: 0 auto; }}
    @media (max-width: 980px) {{
      header, main, footer {{ padding-left: 18px; padding-right: 18px; }}
      .kpis, .two, .three, .insights, .recommendations {{ grid-template-columns: 1fr; }}
      .bar-row {{ grid-template-columns: minmax(90px, 140px) 1fr 42px; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>AI Session Workflow Dashboard</h1>
    <div class="sub">Codex + Claude 本地会话聚合分析 · <span id="range"></span> · 生成于 <span id="generated"></span></div>
  </header>
  <main class="grid">
    <section class="grid kpis" id="kpis"></section>
    <section class="panel">
      <h2>工作方式结论</h2>
      <div class="insights">
        <div class="insight"><strong>主模式</strong>你的协作方式是“产品/架构判断 + AI 执行 + 行为验收”，不是一次性代码生成。</div>
        <div class="insight"><strong>高频闭环</strong>目标描述 → 实现/修复 → Review 风险 → 运行验证 → 根据日志/截图/设计稿继续收敛。</div>
        <div class="insight"><strong>效率瓶颈</strong>Review 类型混在一起、任务中断后容易重复探索、登录/转发/前端对齐等排查路径重复。</div>
        <div class="insight"><strong>优化方向</strong>把“Review”“继续”“对照设计稿”“登录不行”升级成稳定 skill 入口，固定检查清单。</div>
      </div>
    </section>
    <section class="panel">
      <div class="activity-head">
        <h2 id="activity-title">全年活跃矩阵</h2>
        <div class="activity-actions">
          <button class="activity-mode active" data-mode="prompts" type="button">对话数</button>
          <button class="activity-mode" data-mode="tokens" type="button">Token 消耗</button>
        </div>
      </div>
      <div class="activity-summary" id="activity-summary"></div>
      <div class="activity-wrap">
        <div class="activity-grid" id="activity-grid"></div>
      </div>
      <div class="activity-legend">
        <span>少</span>
        <span class="legend-cell level-0"></span>
        <span class="legend-cell level-1"></span>
        <span class="legend-cell level-2"></span>
        <span class="legend-cell level-3"></span>
        <span class="legend-cell level-4"></span>
        <span>多</span>
      </div>
      <div class="activity-detail" id="activity-detail">点击任意日期查看对话数和 token 消耗。</div>
    </section>
    <section class="panel">
      <h2>工作优化建议</h2>
      <div class="recommendations" id="recommendations"></div>
      <div class="prompt-template" id="prompt-template"></div>
    </section>
    <section class="grid two">
      <div class="panel"><h2>任务类别</h2><div id="categories"></div></div>
      <div class="panel"><h2>Agent 来源</h2><div id="sources"></div></div>
    </section>
    <section class="grid two">
      <div class="panel"><h2>高频项目</h2><div id="projects"></div></div>
      <div class="panel"><h2>高频触发词</h2><div id="phrases"></div></div>
    </section>
    <section class="grid two">
      <div class="panel"><h2>工具调用 Top</h2><div id="tools"></div></div>
      <div class="panel"><h2>Skill 候选</h2><div class="stack" id="skills"></div></div>
    </section>
    <section class="panel">
      <h2>代表性需求摘录</h2>
      <div class="examples" id="examples"></div>
    </section>
  </main>
  <footer>说明：看板只使用本机可访问的会话日志；需求摘录已做基础脱敏并截断，不包含完整原始对话。</footer>
  <script id="dashboard-data" type="application/json">{safe_payload}</script>
  <script>
    const data = JSON.parse(document.getElementById('dashboard-data').textContent);
    document.getElementById('range').textContent = `${{data.range.start}} 至 ${{data.range.end}}`;
    document.getElementById('generated').textContent = data.generatedAt;

    const kpis = [
      ['会话数', data.summary.sessions],
      ['有效需求', data.summary.meaningfulPrompts],
      ['Token 总消耗', data.summary.totalTokens],
      ['Claude 需求', data.summary.claudePrompts],
      ['Codex 需求', data.summary.codexPrompts],
      ['工具调用', data.summary.toolCalls],
    ];
    document.getElementById('kpis').innerHTML = kpis.map(([label, value]) =>
      `<div class="panel kpi"><div class="label">${{label}}</div><div class="value">${{formatNumber(value)}}</div></div>`
    ).join('');

    function renderBars(id, rows, color = 'var(--blue)') {{
      const max = Math.max(1, ...rows.map(r => r.value));
      document.getElementById(id).innerHTML = rows.map(r => {{
        const width = Math.max(2, Math.round(r.value / max * 100));
        return `<div class="bar-row" title="${{escapeHtml(r.name)}}: ${{r.value}}">
          <div class="bar-label">${{escapeHtml(r.name)}}</div>
          <div class="bar-track"><div class="bar-fill" style="width:${{width}}%; background:${{color}}"></div></div>
          <div class="bar-value">${{r.value}}</div>
        </div>`;
      }}).join('');
    }}

    function escapeHtml(value) {{
      return String(value).replace(/[&<>"']/g, ch => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[ch]));
    }}

    function formatNumber(value) {{
      const number = Number(value || 0);
      if (number >= 1000000000) return `${{(number / 1000000000).toFixed(2)}}B`;
      if (number >= 1000000) return `${{(number / 1000000).toFixed(2)}}M`;
      return number.toLocaleString();
    }}

    renderBars('categories', data.categories, 'var(--blue)');
    renderBars('sources', data.sources, 'var(--green)');
    renderBars('projects', data.projects, 'var(--purple)');
    renderBars('phrases', data.phrases, 'var(--amber)');
    renderBars('tools', data.tools, 'var(--red)');

    let activityMode = 'prompts';

    function renderActivityMatrix() {{
      const matrix = data.activityMatrix;
      const grid = document.getElementById('activity-grid');
      grid.style.setProperty('--weeks', matrix.weeks);
      const isToken = activityMode === 'tokens';
      document.getElementById('activity-title').textContent = `${{matrix.year}} 全年活跃矩阵`;
      document.getElementById('activity-summary').textContent = isToken
        ? `${{matrix.activeTokenDays}} 个 token 活跃日 · ${{formatNumber(matrix.totalTokens)}} token · 单日最高 ${{formatNumber(matrix.maxTokens)}} token`
        : `${{matrix.activePromptDays}} 个对话活跃日 · ${{matrix.totalPrompts.toLocaleString()}} 条有效需求 · 单日最高 ${{matrix.maxPrompts}} 条`;
      const weekdays = [
        [1, 'Mon'],
        [3, 'Wed'],
        [5, 'Fri'],
      ];
      const monthNodes = matrix.months.map(month =>
        `<div class="month-label" style="grid-column:${{month.week + 2}}; grid-row:1">${{month.label}}</div>`
      );
      const weekdayNodes = weekdays.map(([row, label]) =>
        `<div class="weekday-label" style="grid-row:${{row + 2}}">${{label}}</div>`
      );
      const dayNodes = matrix.days.map((day, index) => {{
        const level = isToken ? day.tokenLevel : day.promptLevel;
        const value = isToken ? `${{formatNumber(day.tokens)}} token` : `${{day.prompts}} 条有效需求`;
        return `<div class="day-cell level-${{level}}${{day.inYear ? '' : ' out'}}"
          data-index="${{index}}"
          style="grid-column:${{day.week + 2}}; grid-row:${{day.day + 2}}"
          title="${{day.date}}: ${{value}}"></div>`;
      }});
      grid.innerHTML = [...monthNodes, ...weekdayNodes, ...dayNodes].join('');
      grid.querySelectorAll('.day-cell').forEach(cell => {{
        cell.addEventListener('click', () => {{
          const day = matrix.days[Number(cell.dataset.index)];
          document.getElementById('activity-detail').textContent =
            `${{day.date}}：${{day.prompts.toLocaleString()}} 条有效需求，${{formatNumber(day.tokens)}} token`;
        }});
      }});
    }}

    document.querySelectorAll('.activity-mode').forEach(button => {{
      button.addEventListener('click', () => {{
        activityMode = button.dataset.mode;
        document.querySelectorAll('.activity-mode').forEach(item => item.classList.toggle('active', item === button));
        renderActivityMatrix();
      }});
    }});

    renderActivityMatrix();

    document.getElementById('recommendations').innerHTML = data.recommendations.map(item => `
      <div class="recommendation">
        <h3>${{escapeHtml(item.title)}}</h3>
        <p>${{escapeHtml(item.body)}}</p>
      </div>
    `).join('');
    document.getElementById('prompt-template').textContent = data.promptTemplate;

    document.getElementById('skills').innerHTML = data.skills.map(s => `
      <div class="skill">
        <div><span class="badge ${{s.priority}}">${{s.priority}}</span></div>
        <div>
          <h3>${{escapeHtml(s.name)}}</h3>
          <p>${{escapeHtml(s.why)}}</p>
          <p>触发：${{escapeHtml(s.triggers)}}</p>
        </div>
      </div>
    `).join('');

    document.getElementById('examples').innerHTML = data.examples.map(e => `
      <div class="example">
        <div class="meta"><span class="pill">${{escapeHtml(e.source)}}</span><span>${{escapeHtml(e.date)}}</span><span>${{escapeHtml(e.project)}}</span></div>
        <div class="text">${{escapeHtml(e.text)}}</div>
      </div>
    `).join('');
  </script>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a local HTML dashboard from Codex and Claude session logs.")
    parser.add_argument("--output", "-o", type=Path, default=DEFAULT_OUTPUT, help="Output HTML path.")
    parser.add_argument("--mock", action="store_true", help="Use public mock data instead of reading local session logs.")
    args = parser.parse_args()
    data = build_mock_data() if args.mock else build_data()
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_dashboard(data), encoding="utf-8")
    print(json.dumps({"output": str(output), "summary": data["summary"], "range": data["range"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
