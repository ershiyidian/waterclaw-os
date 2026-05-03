---
name: waterclaw-usv-dispatch-review
description: Use this skill when reviewing or preparing high-risk WaterClaw USV dispatch actions.
---

# USV Dispatch Review

Dispatch is a task-level, high-risk action. The LLM may plan and review; it must not directly control motors, avoidance, or E-STOP.

Before requesting approval:

1. Confirm the USV role, battery, link status, and current mission.
2. Check weather, visibility, and rainfall because these affect the operating window.
3. Use `plan_usv_mission` to produce a route-level plan and ETA.
4. State the mission objective, target, route constraint, and rollback plan.
5. Call `request_dispatch_approval` with exact args and reason.

Approval rules:

- Approval binds to an args hash and expires quickly.
- Changing `usv`, `mission`, or `target` requires a new approval.
- Never reuse approval tokens or imply approval exists when it has not been returned by WaterClaw.
