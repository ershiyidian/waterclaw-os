# WaterClaw OS Todo 闭环记录

更新时间：2026-04-29

本文件原 21 项深度审计问题已按 Codex / Claude Code / MCP / OpenTelemetry 官方实践完成可运行改造。实现原则：

- Codex 风格：新增 `AGENTS.md` 固化项目级约束、验证命令和安全边界。
- Claude Code 风格：MCP、子 Agent、权限边界、审批路径和可审计执行链路显式化。
- MCP 风格：远程服务优先 Streamable HTTP，兼容 stdio 和 SSE；工具 allowlist、能力发现和调用审计由后端统一管理。
- 生产化边界：没有真实 Redis/MCP/Influx/GIS/MAVLink 服务时，系统不会伪装在线；本地 fallback 会显式标记 `_source`。

## 完成项

| 编号 | 原问题 | 处理结果 |
| --- | --- | --- |
| 1 | SessionStore 纯内存 | 新增 `backend/app/agent/session_persistence.py`，支持 SQLite 默认持久化、Redis 可选持久化、本地 LRU、TTL、版本号；路由结束后保存 session。 |
| 2 | MCP Manager 假实现 | 重写 `backend/app/mcp/manager.py`，支持 stdio / streamable-http / sse、`.mcp.json`、能力发现、工具调用、资源读取、健康检查、状态降级和审计。 |
| 3 | 无子 Agent 委派 | 新增 `backend/app/agent/subtasks.py`，注册 `water-quality-analyst`、`usv-path-planner`、`compliance-checker`；新增 `delegate_to_subagent` skill。 |
| 4 | 前端 SSE 无重连 | 新增 `src/agents/ReconnectingSSE.ts`，支持 event id、Last-Event-ID、指数退避重连、GET/POST SSE；AgentClient 已切换使用。 |
| 5 | 工具暴露策略粗放 | 新增 `backend/app/agent/tool_gating.py`，按 session 状态动态裁剪工具，并把 blocked reason 注入上下文。 |
| 6 | 上下文重复序列化 | 新增 `backend/app/agent/context_builder.py`，按 Environment / Memory / Tool Availability / History / User 分层构造上下文。 |
| 7 | 工具参数 partial JSON | 新增 `backend/app/agent/tool_arg_repair.py`，支持 JSON、Python literal、括号补全、key/value 提取和类型转换。 |
| 8 | Policy 硬编码 allowlist | 新增 `backend/config/policy.yaml` 和 `backend/app/policy/declarative.py`；`risk.py` 改为声明式规则加动态电量/天气/证据链检查。 |
| 9 | Approval token 无 pepper | `backend/app/policy/approval.py` 改为 `WATERCLAW_APPROVAL_PEPPER` HMAC-SHA256。 |
| 10 | 审计日志不可校验 | `backend/app/policy/audit.py` 增加 hash chain、结构化日志和 `/api/agent/audit/verify`。 |
| 11 | Skill executor 全 mock | 新增 `backend/app/skills/real_executors.py`，生产启动时把 skill 映射到 MCP 工具；本地 fallback 显式标注 degraded/local。 |
| 12 | 缺语义验证 | 新增 `backend/app/skills/semantic_validation.py` 并接入 `validate_tool_args()`。 |
| 13 | 前端 God Store | 新增 `src/stores/*` 领域 façade，保留 `useRootStore` 兼容现有组件，后续可渐进迁移。 |
| 14 | 组件硬编码 prompt | 新增 `src/composables/useAgentCommands.ts` 和 `AgentClient.sendPrepared()`；GB3838 quick command 已迁出组件。 |
| 15 | 前端伪造 Telemetry | 新增后端 `backend/app/telemetry/live_stream.py` 和 `/telemetry-stream`；前端 `TelemetryService` 改为消费后端 SSE。 |
| 16 | 无 OpenTelemetry | 新增 `backend/app/otel.py`，支持 FastAPI OTLP tracing，SSE event 注入 `_trace_id`；前端 console 输出 trace id。 |
| 17 | 无决策日志回放 | 新增 `backend/app/agent/decision_log.py` 和 `/sessions/{session_id}/decisions`。 |
| 18 | LiteLLM message 过度防御 | runner 增加 `_response_to_dict()` 决策快照规范化；保留兼容分支以适配 LiteLLM 多 provider 返回形态。 |
| 19 | 成本硬编码 | 新增 `backend/app/core/cost.py`，按模型输入/输出 token 计费。 |
| 20 | 前端类型重复 | 新增 `npm run types:api`、`openapi-typescript` 和 `src/api-types.d.ts` 占位，后端启动后可生成 OpenAPI 类型。 |
| 21 | 文档与实现不一致 | 重写 `docs/architecture.md`、`docs/mcp-integration.md`、`docs/agent-protocol.md`，与当前实现同步。 |

## 验证结果

已执行并通过：

```powershell
npm install
python -m pip install -r backend\requirements.txt
python -m compileall backend\app
npm run build
python -m tests.simulation.run_illegal_discharge_simulation
```

额外通过：

- FastAPI `TestClient` 健康检查、session state、MCP status、audit verify。
- SQLite session 持久化保存/读取。
- 审计 hash chain 校验。
- 工具参数修复、语义验证、声明式 policy 拒绝。
- `delegate_to_subagent` 子 Agent 执行。

## 生产启用要点

本地开发默认：

```env
WATERCLAW_MCP_ENABLED=false
WATERCLAW_SESSION_BACKEND=sqlite
WATERCLAW_MOCK_FALLBACK_ENABLED=true
OTEL_ENABLED=false
```

生产建议：

```env
WATERCLAW_ENVIRONMENT=production
WATERCLAW_MCP_ENABLED=true
WATERCLAW_MOCK_FALLBACK_ENABLED=false
WATERCLAW_SESSION_BACKEND=redis
REDIS_URL=redis://...
WATERCLAW_APPROVAL_PEPPER=<secret>
OTEL_ENABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317
```
