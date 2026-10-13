# WaterClaw OS

[中文版](README.zh-CN.md)

[![CI](https://github.com/ershiyidian/waterclaw-os/actions/workflows/ci.yml/badge.svg)](https://github.com/ershiyidian/waterclaw-os/actions/workflows/ci.yml)

WaterClaw OS is an intelligent river-network patrol and incident-response HMI for unmanned surface vehicle operations.


The project combines a Vue industrial dashboard, a FastAPI backend Agent Host, LiteLLM tool calling, MCP integration, human-in-the-loop approval, telemetry projection, and river-aware GIS visualization.


> Status: research and demonstration prototype for river-patrol HMI.

## Table of Contents

- [Highlights](#highlights)
- [Demo Scenario](#demo-scenario)
- [Architecture](#architecture)
- [River-Aware Map](#river-aware-map)
- [Tech Stack](#tech-stack)
- [Repository Layout](#repository-layout)
- [Quick Start](#quick-start)
- [Environment Configuration](#environment-configuration)
- [MCP Integration](#mcp-integration)
- [Safety and Trust Boundaries](#safety-and-trust-boundaries)
- [Validation](#validation)
- [API Surface](#api-surface)
- [Public Repository Notes](#public-repository-notes)
- [License](#license)

## Highlights

- Industrial Vue HMI for patrol maps, fleet state, telemetry, charts, alerts, agent reasoning, and operator approvals.
- Leaflet map centered on an OpenStreetMap Taopu River `waterway=river` segment, with river corridor rendering and river/land click classification.
- FastAPI Agent Host owns LLM turns, tool execution, policy checks, MCP calls, approval state, audit, and SSE event streaming.
- LiteLLM gateway supports OpenAI-compatible providers, Anthropic, OpenRouter, Ollama, and other LiteLLM backends.
- MCP boundary for external GIS, time-series telemetry, GB3838 evaluation, weather, drainage registry, and USV command bus adapters.
- Human-in-the-loop workflow for critical or hardware-affecting actions.
- SQLite-backed local persistence for sessions, approvals, command records, audit chain, and decision logs.
- Optional Redis session backend and OpenTelemetry tracing for production-style experiments.

## Demo Scenario

The default scenario simulates a Taopu River patrol area:


- USV-01 performs routine patrol and can be assigned to intercept sampling after approval.
- USV-02 holds position near a drain point for fixed monitoring.
- Monitoring stations TP-01 to TP-05 and drain points DP-01 to DP-05 are projected onto the map.
- The agent panel can present a formal incident reasoning chain: sensor self-check, time-series query, clustering, forecast, route planning, and approval request.

## Architecture

```text
Vue 3 HMI
  Map cockpit, telemetry, charts, approvals, conversation, trace
  |
  | HTTP + SSE
  v
FastAPI Agent Host
  LiteLLM tool-calling loop
  Tool argument repair and schema validation
  Declarative policy and dynamic risk checks
  Human-in-the-loop approval state machine
  SQLite / Redis persistence
  Audit hash chain and decision logs
  |
  | MCP client / local explicit fallback
  v
External services
  GIS, TSDB, GB3838, weather, drainage registry, USV command bus
```

Frontend responsibilities:


- Render the current projection of fleet, telemetry, agent, MCP, approval, and map state.
- Send operator messages, slash commands, approval responses, and hard-control requests to the backend.
- Consume backend SSE events as the source of truth.
- Never execute production tools or claim physical hardware actions are complete without backend events.

Backend responsibilities:


- Build LLM context and run LiteLLM completions.
- Decide visible tools through dynamic tool gating.
- Repair and validate tool arguments.
- Enforce semantic validation and declarative policy.
- Create approval records for risky actions.
- Execute safe local tools or MCP-backed production tools.
- Persist sessions, approvals, commands, audit events, and decision logs.
- Stream normalized AgentEvent updates to the HMI.

## River-Aware Map

The map starts on a verified OpenStreetMap-derived Taopu River centerline instead of a land-biased synthetic point.


- OSM way: `768410671`
- Name: `桃浦河`
- Tag: `waterway=river`
- Default center: `31.2755918, 121.3875979`
- River corridor threshold: `32 m`

Implementation:


- `src/config/constants.ts`: default center, OSM provenance, river path, corridor radius, drain points, and station points.
- `src/utils/geo.ts`: haversine distance and nearest-point-on-path helpers.
- `src/services/MapService.ts`: river corridor rendering and river/land classification popup.
- `src/styles/map.css`: map marker and popup styling.

**Scope:**


- The river/land classifier is a deterministic visualization based on distance to the OSM river centerline.
- Authoritative hydrographic survey data, bathymetry, navigability constraints, and production-grade geofencing are out of scope for this prototype.

## Tech Stack

Frontend:

- Vue 3
- TypeScript
- Pinia
- Vite
- Leaflet
- ECharts
- lucide-vue-next

Backend:

- Python 3.12
- FastAPI
- LiteLLM
- Pydantic
- SQLite
- Optional Redis
- Optional OpenTelemetry
- MCP Python SDK / FastMCP when enabled

Tooling:

- npm scripts and `bin/waterclaw.js` CLI
- Conda environment bootstrap
- `openapi-typescript` for generated API types
- Protocol simulation tests under `tests/simulation`
- GitHub Actions CI

## Repository Layout

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
└── README.md            Project overview
```

More detailed structure:


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

## Quick Start

Prerequisites:


- Node.js 18 or newer
- npm
- Conda or Miniconda
- Python managed by the project Conda environment
- Provider API key only if live LLM calls are needed

Install dependencies and create the backend Conda environment:


```powershell
npm install
npm run waterclaw -- install
```

Start the full system:


```powershell
npm run waterclaw -- dev
```

Open the HMI:


```text
http://127.0.0.1:5173/
```

Backend health check:


```text
http://127.0.0.1:8787/api/health
```

Frontend only:


```powershell
npm run dev
```

Backend only:


```powershell
npm run backend:dev
```

## Environment Configuration

Copy the backend environment template:


```powershell
Copy-Item backend/.env.example backend/.env
```

Typical local configuration:


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


```env
OPENAI_API_KEY=<your-openai-api-key>
# ANTHROPIC_API_KEY=<your-anthropic-api-key>
# OPENROUTER_API_KEY=<your-openrouter-api-key>
```

Provider credentials belong on the backend only. Do not put them in frontend environment files.


## MCP Integration

MCP server configuration lives in `backend/.mcp.json`. Public repository examples use `.example.invalid` endpoints by design. Replace them with authenticated internal services before enabling MCP in a real environment.


Local demo defaults:


```env
WATERCLAW_MCP_ENABLED=false
WATERCLAW_MOCK_FALLBACK_ENABLED=true
```

Production-style configuration:


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


## Safety And Trust Boundaries

WaterClaw OS separates UI projection from physical-world execution.


- Frontend code must not claim hardware state changes as completed facts.
- Hardware-affecting actions go through backend approval, command records, idempotency keys, and audit.
- Critical tools must declare write permissions and remain behind HITL approval.
- MCP output is external data and must keep provenance.
- Local fallback data is explicitly marked degraded/local and should not be presented as production truth.
- Browser-side simulation paths are not part of production `src/`.
- Public repository examples use placeholder endpoints and placeholder keys.

See also:


- `AGENTS.md`
- `SECURITY.md`
- `docs/architecture.md`
- `docs/agent-protocol.md`
- `docs/mcp-integration.md`

## Validation

Frontend build:


```powershell
npm run build
```

Backend syntax check:


```powershell
python -m compileall backend/app
```

Agent event protocol simulation:


```powershell
python -m tests.simulation.run_illegal_discharge_simulation
```

GitHub Actions runs the same baseline checks:


- `npm ci`
- `npm run build`
- `python -m pip install -r backend/requirements.txt`
- `python -m compileall backend/app`
- `python -m tests.simulation.run_illegal_discharge_simulation`

## API Surface

Main backend routes:


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


## Public Repository Notes

The repository intentionally ignores local and generated artifacts:


- `node_modules/`
- `dist/`
- `.codex-tasks/`
- `backend/.waterclaw/`
- `backend/backend/`
- root `.env`
- `backend/.env`
- logs, Python bytecode, and merged local exports

### Production checklist


- Replace `.example.invalid` MCP endpoints with authenticated service endpoints.
- Set real provider keys only in backend secrets or deployment secret managers.
- Disable mock fallback in production.
- Put the backend behind an API gateway with authentication, rate limiting, and audit retention.
- Review safety cases before connecting a real USV bus.

## License

License not yet chosen.

