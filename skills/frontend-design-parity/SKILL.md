---
name: frontend-design-parity
description: Use this skill whenever the user asks to build, adjust, compare, or review frontend UI against a design, screenshot, product expectation, or visual target. Trigger on "对照设计稿", "样式差异", "UI", "布局", "移动端", "截图验证", "文字溢出", "按钮/icon/字号/颜色", or when frontend work needs browser verification.
---

# Frontend Design Parity

Use this workflow to close frontend tasks with visual evidence, not just code changes.

## Workflow

1. Identify the target surface: page, component, viewport, state, and interaction.
2. List visual acceptance criteria before editing.
3. Match existing design system and component patterns.
4. Implement the smallest scoped UI change.
5. Verify in browser with screenshots for desktop and mobile when relevant.
6. Check text wrapping, overflow, spacing, hover/focus/disabled/loading states.
7. Report screenshots or exact browser checks.

## Visual Checklist

Check these before finalizing:

- Layout: alignment, density, responsive breakpoints, no overlapping text.
- Typography: hierarchy, readable sizes, no viewport-scaled font surprises.
- Controls: icons for tool actions, familiar interaction patterns, stable dimensions.
- Content: empty/loading/error states and long labels.
- Accessibility: semantic controls, keyboard focus, contrast, labels.
- Consistency: local colors, radius, spacing, component conventions.

## Browser Verification

Use the local browser for:

- Desktop screenshot.
- Mobile or narrow viewport screenshot.
- Interactions that affect layout.
- Canvas/3D/image rendering when present.

## Final Response

Include:

- What changed.
- Which viewport/states were checked.
- Any remaining mismatch or design assumption.
