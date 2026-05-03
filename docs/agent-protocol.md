# Agent Protocol

## Message

```ts
type Message =
  | { role: 'user'; content: string; timestamp: number }
  | { role: 'assistant'; content: string; severity?: Severity; timestamp: number }
  | { role: 'tool_call'; toolCallId: string; timestamp: number }
  | { role: 'mcp_resource_read'; server: string; uri: string; result: unknown; timestamp: number }
  | { role: 'approval'; approvalId: string; timestamp: number }
  | { role: 'system'; content: string; severity?: Severity; timestamp: number }
```

UI 的 Conversation、Plan、Trace 是同一份 Agent 状态的不同投影：

- Conversation 渲染 `feed` 和 `toolCalls`。
- Plan 渲染 `reactSteps`。
- Trace 渲染 `toolCalls` 的时间线。

## LLM Turn

```text
frontend AgentClient
  -> /api/agent/sessions/{session_id}/turn
  -> backend AgentRunner
  -> dynamic tool gate
  -> context builder
  -> litellm.acompletion(..., tools=[visible tools], tool_choice="auto")
  -> argument repair / validation / policy / tool execution / HITL
  -> decision log + audit
  -> SSE AgentEvent stream
```

`/api/llm/agent-turn` is a legacy debug endpoint and is not the production UI path.

Critical hardware-control tools are blocked from normal LLM turns by the dynamic tool gate. They are reached through backend control request and approval paths. The blocked-tool reasons are still injected into context so the model can explain the required approval path without hallucinating tool names.

## Event Types

Every SSE event includes an `id:` line. When OpenTelemetry is enabled, event data may include `_trace_id`.

- `state.patch`: updates agent status and current mission.
- `usage.patch`: updates token usage.
- `mcp.status`: replaces frontend MCP rack status from backend state.
- `react.step`: appends one Plan-Act-Observe summary row.
- `tool.started`: appends a ToolCall card.
- `tool.finished`: marks a ToolCall successful and attaches result.
- `tool.failed`: marks a ToolCall failed.
- `tool.awaiting_approval`: marks a ToolCall as waiting for HITL.
- `approval.required`: creates a frontend approval card.
- `approval.resolved`: clears approval UI.
- `telemetry.snapshot`: updates frontend telemetry from backend stream.
- `message.final`: appends final assistant/system text.

## Approval Endpoints

`POST /api/agent/sessions/{session_id}/approvals/{approval_id}/approve`

```json
{ "code": "operator-entered-approval-code" }
```

`POST /api/agent/sessions/{session_id}/approvals/{approval_id}/reject`

```json
{}
```

Approval records bind to `tool_name`, canonical args hash, expiry, one-time token hash, and operator identity. Critical tools are executed only after the backend consumes the approval token. The token hash is HMAC-SHA256 with `WATERCLAW_APPROVAL_PEPPER`.

## Control Requests

`POST /api/agent/sessions/{session_id}/control/request`

```json
{
  "action": "request_estop",
  "usvs": ["USV-01", "USV-02"],
  "reason": "操作员从顶部硬控制区请求 E-STOP 安全动作。"
}
```

Allowed actions:

- `rtl_usv`
- `request_estop`

The frontend must not directly mutate USV mode or claim a physical action has completed. A control request creates a backend tool call and, for critical actions, a persisted HITL approval. Hardware state may be shown as executed only after a backend command result or bus ACK event.

## Validation Boundary

Tool arguments are validated in this order:

1. Tool-call argument repair for partial or malformed JSON.
2. JSON Schema validation from the backend `SkillManifest`.
3. Semantic validation from Pydantic models.
4. Declarative policy validation from `backend/config/policy.yaml`.
5. Dynamic business policy validation from runtime context.
6. Risk classification.
7. Approval creation for critical tools.
8. Durable command creation and idempotency-key reuse for write-side tools.

Invalid or malformed arguments produce `tool.failed`, are written to audit, and do not create approval records.

## Replay And Audit

- `GET /api/agent/sessions/{session_id}/decisions` returns model input snapshots, model response, parsed tool calls, policy decisions, and tool results.
- `GET /api/agent/audit/verify` verifies the local audit hash chain.
