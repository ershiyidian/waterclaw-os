# WaterClaw OS / 河网智巡操作系统

[![CI](https://github.com/ershiyidian/waterclaw-os/actions/workflows/ci.yml/badge.svg)](https://github.com/ershiyidian/waterclaw-os/actions/workflows/ci.yml)

WaterClaw OS is an intelligent river-network patrol and incident-response HMI for unmanned surface vehicle operations.

WaterClaw OS（河网智巡操作系统）是一个面向无人水面艇巡河、水质异常研判和应急处置的人机协同指挥界面与后端 Agent Host 原型。

The project combines a Vue industrial dashboard, a FastAPI backend Agent Host, LiteLLM tool calling, MCP integration, human-in-the-loop approval, telemetry projection, and river-aware GIS visualization.

项目集成了 Vue 工业驾驶舱、FastAPI 后端 Agent Host、LiteLLM 工具调用、MCP 集成、人工审批、水文遥测投影和河道感知地图能力。

> Status: research and demonstration system. It is not certified for direct field deployment or autonomous hardware control.
>
> 当前状态：科研与演示系统。尚未经过现场部署认证，也不应直接用于真实硬件自主控制。

## Table Of Contents / 目录

- [Highlights / 核心亮点](#highlights--核心亮点)
- [Demo Scenario / 演示场景](#demo-scenario--演示场景)
- [Architecture / 架构](#architecture--架构)
- [River-Aware Map / 河道感知地图](#river-aware-map--河道感知地图)
- [Tech Stack / 技术栈](#tech-stack--技术栈)
- [Repository Layout / 仓库结构](#repository-layout--仓库结构)
- [Quick Start / 快速启动](#quick-start--快速启动)
- [Environment Configuration / 环境配置](#environment-configuration--环境配置)
- [MCP Integration / MCP 集成](#mcp-integration--mcp-集成)
- [Safety And Trust Boundaries / 安全与信任边界](#safety-and-trust-boundaries--安全与信任边界)
- [Validation / 验证](#validation--验证)
- [API Surface / API 概览](#api-surface--api-概览)
- [Public Repository Notes / 公开仓库说明](#public-repository-notes--公开仓库说明)
- [License / 许可证](#license--许可证)

## Highlights / 核心亮点

- Industrial Vue HMI for patrol maps, fleet state, telemetry, charts, alerts, agent reasoning, and operator approvals.
- 工业风 Vue HMI，覆盖巡河地图、艇队状态、遥测、图表、告警、Agent 推理和操作员审批。
- Leaflet map centered on an OpenStreetMap Taopu River `waterway=river` segment, with river corridor rendering and river/land click classification.
- Leaflet 地图默认启动在 OpenStreetMap 桃浦河 `waterway=river` 线段上，支持河道走廊渲染和点击点位的“河道/陆地”判定。
- FastAPI Agent Host owns LLM turns, tool execution, policy checks, MCP calls, approval state, audit, and SSE event streaming.
- FastAPI Agent Host 统一负责 LLM 回合、工具执行、策略校验、MCP 调用、审批状态、审计和 SSE 事件流。
- LiteLLM gateway supports OpenAI-compatible providers, Anthropic, OpenRouter, Ollama, and other LiteLLM backends.
- LiteLLM 网关支持 OpenAI 兼容服务、Anthropic、OpenRouter、Ollama 等模型后端。
- MCP boundary for external GIS, time-series telemetry, GB3838 evaluation, weather, drainage registry, and USV command bus adapters.
- MCP 边界用于接入外部 GIS、时序遥测、GB3838 评价、气象、排水登记和无人艇指令总线适配器。
- Human-in-the-loop workflow for critical or hardware-affecting actions.
- 对高风险或影响硬件的动作提供人工审批流程。
- SQLite-backed local persistence for sessions, approvals, command records, audit chain, and decision logs.
- 本地默认使用 SQLite 持久化会话、审批、命令记录、审计链和决策日志。
- Optional Redis session backend and OpenTelemetry tracing for production-style experiments.
- 可选 Redis 会话后端和 OpenTelemetry 链路追踪，便于生产化实验。

## Demo Scenario / 演示场景

The default scenario simulates a Taopu River patrol area:

默认场景模拟桃浦河巡查区域：

- USV-01 performs routine patrol and can be assigned to intercept sampling after approval.
- USV-01 执行常态巡航，并可在审批后进入拦截采样任务。
- USV-02 holds position near a drain point for fixed monitoring.
- USV-02 在排口附近定点监测。
- Monitoring stations TP-01 to TP-05 and drain points DP-01 to DP-05 are projected onto the map.
- TP-01 至 TP-05 监测断面、DP-01 至 DP-05 排口被投影到地图上。
- The agent panel can present a formal incident reasoning chain: sensor self-check, time-series query, clustering, forecast, route planning, and approval request.
- Agent 面板可以展示正式事件推理链：传感器自检、时序查询、聚类、预测、路径规划和审批请求。

## Architecture / 架构

```text
Vue 3 HMI / 前端指挥界面
  Map cockpit, telemetry, charts, approvals, conversation, trace
  地图驾驶舱、遥测、图表、审批、对话、追踪
  |
  | HTTP + SSE
  v
FastAPI Agent Host / 后端智能体主机
  LiteLLM tool-calling loop
  Tool argument repair and schema validation
  Declarative policy and dynamic risk checks
  Human-in-the-loop approval state machine
  SQLite / Redis persistence
  Audit hash chain and decision logs
  |
  | MCP client / local explicit fallback
  v
External services / 外部服务
  GIS, TSDB, GB3838, weather, drainage registry, USV command bus
```

Frontend responsibilities:

前端职责：

- Render the current projection of fleet, telemetry, agent, MCP, approval, and map state.
- 渲染艇队、遥测、Agent、MCP、审批和地图状态的当前投影。
- Send operator messages, slash commands, approval responses, and hard-control requests to the backend.
- 向后端发送操作员消息、Slash 命令、审批响应和硬控制请求。
- Consume backend SSE events as the source of truth.
- 以后端 SSE 事件作为状态真源。
- Never execute production tools or claim physical hardware actions are complete without backend events.
- 不在浏览器中执行生产工具，也不在缺少后端事件时宣称真实硬件动作已完成。

Backend responsibilities:

后端职责：

- Build LLM context and run LiteLLM completions.
- 构造 LLM 上下文并调用 LiteLLM。
- Decide visible tools through dynamic tool gating.
- 通过动态工具门控决定可见工具。
- Repair and validate tool arguments.
- 修复并验证工具参数。
- Enforce semantic validation and declarative policy.
- 执行语义校验和声明式策略。
- Create approval records for risky actions.
- 为高风险动作创建审批记录。
- Execute safe local tools or MCP-backed production tools.
- 执行安全本地工具或 MCP 后端生产工具。
- Persist sessions, approvals, commands, audit events, and decision logs.
- 持久化会话、审批、命令、审计事件和决策日志。
- Stream normalized AgentEvent updates to the HMI.
- 向 HMI 推送规范化 AgentEvent。

## River-Aware Map / 河道感知地图

The map starts on a verified OpenStreetMap-derived Taopu River centerline instead of a land-biased synthetic point.

地图默认启动在经 OpenStreetMap / Overpass 验证的桃浦河中心线上，而不是偏向陆地的人工点位。

- OSM way: `768410671`
- Name / 名称：`桃浦河`
- Tag / 标签：`waterway=river`
- Default center / 默认中心：`31.2755918, 121.3875979`
- River corridor threshold / 河道走廊阈值：`32 m`

Implementation:

实现位置：

- `src/config/constants.ts`: default center, OSM provenance, river path, corridor radius, drain points, and station points.
- `src/config/constants.ts`：默认中心、OSM 来源、河道路径、走廊半径、排口与断面点位。
- `src/utils/geo.ts`: haversine distance and nearest-point-on-path helpers.
- `src/utils/geo.ts`：球面距离和折线最近点计算。
- `src/services/MapService.ts`: river corridor rendering and river/land classification popup.
- `src/services/MapService.ts`：河道走廊渲染和“河道/陆地”判定弹窗。
- `src/styles/map.css`: map marker and popup styling.
- `src/styles/map.css`：地图锚点和弹窗样式。

Limitations:

限制：

- The river/land classifier is a deterministic visualization based on distance to the OSM river centerline.
- 河道/陆地判定基于点到 OSM 河道中心线的距离，是确定性可视化逻辑。
- It is not a substitute for authoritative hydrographic survey data, bathymetry, navigability constraints, or production-grade geofencing.
- 它不能替代权威水文测绘、测深、通航约束或生产级电子围栏。

## Tech Stack / 技术栈

Frontend / 前端：

- Vue 3
- TypeScript
- Pinia
- Vite
- Leaflet
- ECharts
- lucide-vue-next

Backend / 后端：

- Python 3.12
- FastAPI
- LiteLLM
- Pydantic
- SQLite
- Optional Redis / 可选 Redis
- Optional OpenTelemetry / 可选 OpenTelemetry
- MCP Python SDK / FastMCP when enabled / 启用 MCP 时使用 MCP Python SDK / FastMCP

Tooling / 工具链：

- npm scripts and `bin/waterclaw.js` CLI
- npm 脚本与 `bin/waterclaw.js` CLI
- Conda environment bootstrap
- Conda 环境初始化
- `openapi-typescript` for generated API types
- `openapi-typescript` 用于生成 API 类型
- Protocol simulation tests under `tests/simulation`
- `tests/simulation` 下的协议模拟测试
- GitHub Actions CI
- GitHub Actions 持续集成

## Repository Layout / 仓库结构

```text
.
├── .github/workflows/   GitHub Actions CI
├── src/                 Vue HMI source
├── backend/             FastAPI Agent Host
├── docs/                Architecture, protocol, MCP, LiteLLM docs
├── tests/               AgentEvent protocol simulation tests
├── claude-plugin/       WaterClaw MCP/plugin packaging assets
├── bin/waterclaw.js     Project CLI
├── AGENTS.md            Durable repository instructions for coding agents
├── SECURITY.md          Security policy and reporting guidance
└── README.md            Bilingual project overview
```

More detailed structure:

更细目录结构：

```text
src/
  agents/        AgentClient and reconnecting SSE client
  components/    Vue cockpit, map, panels, approval, and feed components
  composables/   Command builders and UI composition helpers
  config/        Map constants, thresholds, MCP metadata, skills
  core/          Root store, event bus, logger, shared types
  services/      Map, telemetry, charts, persistence services
  stores/        Domain facades around the root store
  styles/        Design tokens, layout, animations, map styles
  utils/         Time, math, geo, formatting utilities

backend/app/
  agent/         Agent runner, state, routes, SSE, context, tool gating
  core/          Config, auth, cost, database helpers
  mcp/           MCP client manager and FastMCP server
  policy/        Approval, audit, commands, declarative policy, risk
  services/      LiteLLM gateway
  skills/        Skill registry, validation, real MCP executors
  telemetry/     Backend telemetry stream
```

## Quick Start / 快速启动

Prerequisites:

前置条件：

- Node.js 18 or newer / Node.js 18 或更高版本
- npm
- Conda or Miniconda / Conda 或 Miniconda
- Python managed by the project Conda environment / 由项目 Conda 环境管理的 Python
- Provider API key only if live LLM calls are needed / 只有调用真实 LLM 时才需要模型供应商 API Key

Install dependencies and create the backend Conda environment:

安装依赖并创建后端 Conda 环境：

```powershell
npm install
npm run waterclaw -- install
```

Start the full system:

启动完整系统：

```powershell
npm run waterclaw -- dev
```

Open the HMI:

打开前端：

```text
http://127.0.0.1:5173/
```

Backend health check:

后端健康检查：

```text
http://127.0.0.1:8787/api/health
```

Frontend only:

仅启动前端：

```powershell
npm run dev
```

Backend only:

仅启动后端：

```powershell
npm run backend:dev
```

## Environment Configuration / 环境配置

Copy the backend environment template:

复制后端环境变量模板：

```powershell
Copy-Item backend/.env.example backend/.env
```

Typical local configuration:

典型本地配置：

```env
LITELLM_MODEL=openai/gpt-4o-mini
LITELLM_TIMEOUT_SECONDS=45
LITELLM_MAX_TOKENS=900
LITELLM_TEMPERATURE=0.2

WATERCLAW_ENVIRONMENT=development
WATERCLAW_SESSION_BACKEND=sqlite
WATERCLAW_SQLITE_PATH=backend/.waterclaw/waterclaw.db
WATERCLAW_MCP_ENABLED=false
WATERCLAW_MOCK_FALLBACK_ENABLED=true
OTEL_ENABLED=false

WATERCLAW_CORS_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
```

Set the provider key matching your model:

按模型供应商设置对应密钥：

```env
OPENAI_API_KEY=<your-openai-api-key>
# ANTHROPIC_API_KEY=<your-anthropic-api-key>
# OPENROUTER_API_KEY=<your-openrouter-api-key>
```

Provider credentials belong on the backend only. Do not put them in frontend environment files.

模型供应商密钥只应放在后端，不应放进前端环境文件。

## MCP Integration / MCP 集成

MCP server configuration lives in `backend/.mcp.json`. Public repository examples use `.example.invalid` endpoints by design. Replace them with authenticated internal services before enabling MCP in a real environment.

MCP 服务配置位于 `backend/.mcp.json`。公开仓库中的示例端点刻意使用 `.example.invalid` 占位域名。真实环境启用 MCP 前，应替换为带鉴权的内部服务。

Local demo defaults:

本地演示默认值：

```env
WATERCLAW_MCP_ENABLED=false
WATERCLAW_MOCK_FALLBACK_ENABLED=true
```

Production-style configuration:

生产化实验配置：

```env
WATERCLAW_ENVIRONMENT=production
WATERCLAW_MCP_ENABLED=true
WATERCLAW_MOCK_FALLBACK_ENABLED=false
WATERCLAW_SESSION_BACKEND=redis
REDIS_URL=redis://127.0.0.1:6379/0
WATERCLAW_APPROVAL_PEPPER=<replace-with-secret-pepper>
OTEL_ENABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://127.0.0.1:4317
```

External MCP output is untrusted observation data. Keep provenance in tool results and never silently convert degraded fallback results into production truth.

外部 MCP 输出属于不可信观测数据。工具结果必须保留来源，不应把降级 fallback 数据静默当作生产真值。

## Safety And Trust Boundaries / 安全与信任边界

WaterClaw OS separates UI projection from physical-world execution.

WaterClaw OS 将前端状态投影与真实物理执行明确分离。

- Frontend code must not claim hardware state changes as completed facts.
- 前端代码不能把硬件状态变化宣称为已完成事实。
- Hardware-affecting actions go through backend approval, command records, idempotency keys, and audit.
- 影响硬件的动作必须经过后端审批、命令记录、幂等键和审计。
- Critical tools must declare write permissions and remain behind HITL approval.
- 高风险工具必须声明写权限，并置于人工审批之后。
- MCP output is external data and must keep provenance.
- MCP 输出属于外部数据，必须保留来源。
- Local fallback data is explicitly marked degraded/local and should not be presented as production truth.
- 本地 fallback 数据会显式标记为 degraded/local，不应展示为生产真值。
- Browser-side simulation paths are not part of production `src/`.
- 浏览器侧模拟路径不属于生产 `src/`。
- Public repository examples use placeholder endpoints and placeholder keys.
- 公开仓库仅使用占位端点和占位密钥。

See also:

更多说明：

- `AGENTS.md`
- `SECURITY.md`
- `docs/architecture.md`
- `docs/agent-protocol.md`
- `docs/mcp-integration.md`

## Validation / 验证

Frontend build:

前端构建：

```powershell
npm run build
```

Backend syntax check:

后端语法检查：

```powershell
python -m compileall backend/app
```

Agent event protocol simulation:

AgentEvent 协议模拟：

```powershell
python -m tests.simulation.run_illegal_discharge_simulation
```

GitHub Actions runs the same baseline checks:

GitHub Actions 会运行同一组基线检查：

- `npm ci`
- `npm run build`
- `python -m pip install -r backend/requirements.txt`
- `python -m compileall backend/app`
- `python -m tests.simulation.run_illegal_discharge_simulation`

## API Surface / API 概览

Main backend routes:

主要后端接口：

- `GET /api/health`
- `POST /api/agent/sessions/{session_id}/turn`
- `GET /api/agent/sessions/{session_id}/stream`
- `GET /api/agent/sessions/{session_id}/telemetry-stream`
- `POST /api/agent/sessions/{session_id}/control/request`
- `POST /api/agent/sessions/{session_id}/approvals/{approval_id}/approve`
- `POST /api/agent/sessions/{session_id}/approvals/{approval_id}/reject`
- `GET /api/agent/sessions/{session_id}/decisions`
- `GET /api/agent/audit/verify`

The OpenAPI schema is available from FastAPI when the backend is running.

后端启动后可以通过 FastAPI 获取 OpenAPI schema。

## Public Repository Notes / 公开仓库说明

The repository intentionally ignores local and generated artifacts:

仓库有意忽略本地和生成文件：

- `node_modules/`
- `dist/`
- `.codex-tasks/`
- `backend/.waterclaw/`
- `backend/backend/`
- root `.env`
- `backend/.env`
- logs, Python bytecode, and merged local exports
- 日志、Python 字节码和本地合并导出文件

Before deploying outside local development:

本地开发之外部署前：

- Replace `.example.invalid` MCP endpoints with authenticated service endpoints.
- 将 `.example.invalid` MCP 端点替换为带鉴权的服务端点。
- Set real provider keys only in backend secrets or deployment secret managers.
- 真实模型密钥只能放入后端 secrets 或部署平台 secret manager。
- Disable mock fallback in production.
- 生产环境禁用 mock fallback。
- Put the backend behind an API gateway with authentication, rate limiting, and audit retention.
- 将后端置于带认证、限流和审计保留策略的 API Gateway 后。
- Review safety cases before connecting a real USV bus.
- 接入真实无人艇总线前必须复核安全案例。

## License / 许可证

No open-source license has been added yet. Until a license is added by the project owner, all rights are reserved.

当前尚未添加开源许可证。在项目所有者正式添加许可证前，保留所有权利。
