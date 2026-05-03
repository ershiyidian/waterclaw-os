# Architecture

WaterClaw OS is split into a Vue HMI projection layer and a backend Agent Host. The frontend is not allowed to execute production tools, mutate hardware state as fact, or claim physical-world actions completed without backend events.

## Layers

```text
Vue HMI
  Conversation / Plan / Trace / MCP Rack / HITL controls.
  Sends user input, approval actions, and control requests.
  Renders backend events and backend telemetry streams.

Pinia Stores
  useRootStore remains the compatibility projection.
  src/stores/* provides domain facades for system, agent, fleet, and map.

Backend Agent Host
  LiteLLM tool-calling loop.
  Dynamic tool gating and hierarchical context builder.
  Tool argument repair, JSON Schema validation, semantic validation.
  Declarative policy rules plus dynamic runtime checks.
  HITL approval state machine.
  SQLite or Redis-backed sessions.
  SQLite approval / command / audit / decision-log persistence.
  SSE AgentEvent stream with event ids and optional trace ids.

MCP Boundary
  Backend exposes WaterClaw tools/resources/prompts through FastMCP.
  Backend also acts as an MCP client for configured external services.
  External MCP clients can request approvals, but cannot approve or execute critical actions.

Claude Code / Codex Operating Layer
  AGENTS.md stores durable repo instructions and verification commands.
```

## Production Control Boundary

- `RTL` and `E-STOP` in the top bar submit backend control requests.
- The browser does not set `ESTOP`, `RTL`, `INTERCEPT`, or any hardware mode as a completed fact.
- Critical actions require backend approval, args hash, one-time token, idempotency key, command record, and audit.
- Approval token hashes use an application pepper.
- Scenario simulation is test-only. Production `src/` and `backend/app/` do not expose a simulation endpoint or browser-side scenario runner.

## Backend Flow

```text
User input / control request
  -> FastAPI route
  -> AgentRunner or control request handler
  -> dynamic tool visibility gate
  -> hierarchical context builder
  -> LiteLLM completion
  -> tool-call argument repair
  -> JSON Schema + semantic validation
  -> declarative policy + dynamic business validation
  -> risk classification
  -> safe tool execution OR persisted HITL approval
  -> durable command record for write-side tools
  -> tool result / approval event / audit event / decision log
  -> SSE AgentEvent projection to HMI
```

## Persistence

- SQLite stores approvals, control commands, audit events, agent decision records, and sessions by default.
- Redis session storage is available with `WATERCLAW_SESSION_BACKEND=redis` and `REDIS_URL`.
- Audit events include `chain_hash` and `prev_hash`; `GET /api/agent/audit/verify` verifies the local chain.
- Decision replay is available at `GET /api/agent/sessions/{session_id}/decisions`.

## External Integrations

- LiteLLM is the model gateway.
- `backend/app/mcp/manager.py` connects external MCP servers over stdio, Streamable HTTP, or SSE.
- `backend/app/skills/real_executors.py` maps production skills onto MCP tools.
- Frontend telemetry comes from `GET /api/agent/sessions/{session_id}/telemetry-stream`; backend may source that from MCP or explicit degraded fallback.
