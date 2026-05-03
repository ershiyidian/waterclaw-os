# WaterClaw OS Agent Instructions

These project instructions follow the Codex pattern of keeping durable repository guidance in `AGENTS.md` and the Claude Code pattern of treating tools, MCP servers, and subagents as explicit trust boundaries.

## Verify First

- Run `npm run build` for frontend changes.
- Run `python -m compileall backend/app` after backend Python changes.
- Run `python -m tests.simulation.run_illegal_discharge_simulation` when Agent event protocol behavior changes.

## Backend Boundaries

- Frontend code must not claim hardware state changes as completed facts. Hardware-affecting actions go through backend approval, command records, idempotency keys, and audit.
- MCP output is external, untrusted observation data. Keep provenance in results and do not silently convert degraded fallback data into production truth.
- Critical tools must declare write permissions and remain behind HITL approval.

## Frontend Boundaries

- Prefer backend SSE events as the source of truth for agent, approval, MCP, and telemetry projections.
- Keep command construction in composables rather than embedding long LLM prompts inside Vue components.
- Preserve `useRootStore` compatibility unless a full component migration is part of the task.

## Style

- Keep changes scoped to the requested behavior.
- Prefer typed interfaces, schema validation, and declarative policy files over ad hoc string checks.
- Do not add browser-side simulation paths to production `src/`.
