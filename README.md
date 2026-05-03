# WaterClaw OS

WaterClaw OS is an intelligent river-network patrol and incident-response HMI for unmanned surface vehicle operations. The project combines a Vue industrial dashboard, a FastAPI Agent Host, LiteLLM tool calling, MCP integration, human-in-the-loop approval, telemetry projection, and river-aware GIS visualization.

The current demo is centered on the Taopu River patrol scenario in Shanghai. The default map starts directly on a verified OpenStreetMap Taopu River waterway segment, renders a river corridor, and can classify clicked coordinates as river or land based on distance to the river centerline.

## Highlights

- Industrial Vue HMI for river patrol, fleet state, telemetry, water-quality analytics, charts, alerts, and operator approvals.
- Leaflet map with Taopu River `waterway=river` geometry from OpenStreetMap / Overpass, river corridor rendering, river/land click classification, drain points, monitoring stations, USV markers, trails, spread circles, and blockade lines.
- FastAPI Agent Host that owns LLM turns, tool execution, policy checks, MCP calls, audit, approvals, and event streaming.
- LiteLLM gateway support for OpenAI-compatible providers, Anthropic, OpenRouter, Ollama, and other LiteLLM backends.
- MCP boundary for external GIS, TSDB, GB3838 evaluation, weather, drainage registry, and MAVLink-style command buses.
- Human-in-the-loop workflow for high-risk or hardware-affecting actions.
- SSE projection model: frontend renders backend events and does not claim hardware state changes before backend acknowledgement.
- SQLite-backed local persistence for sessions, approval records, command records, audit chain, and decision logs.
- Optional Redis session backend and OpenTelemetry tracing for production-style deployment.

## Project Status

This repository is a working research and demo system. It is suitable for local development, UI demonstration, architecture review, and integration experiments. Real municipal GIS, time-series telemetry, water-quality standard services, weather services, and USV command buses still need production adapters and authentication before field use.

Important safety boundary: the browser is a projection layer. It displays state, sends user input, and submits approval actions, but production hardware-affecting commands must go through the backend approval, policy, command, idempotency, and audit pipeline.

## Screens And Workflows

- Map cockpit: Taopu River patrol map, verified river-centered startup, water/land classification popup, drains, stations, USV positions, planned paths, spread projection, and blockade overlay.
- Fleet panel: USV cards, battery state, mission segment, speed, heading, sensor matrix, and digital twin widgets.
- Telemetry strip: RTK, link, edge AI, weather, and mission clock.
- Analytics panel: water-quality trend charts, GB3838 class bands, brush/data zoom, legends, and incident context.
- Agent panel: conversation feed, ReAct plan tree, MCP rack, tool-call cards, trace timeline, memory inspector, slash commands, and HITL approval UI.
- Hard controls: RTL and E-STOP request paths that submit backend control requests instead of mutating frontend state as fact.

## Architecture

```text
Vue 3 HMI
  Map cockpit, telemetry, charts, operator controls, conversation, approvals
  |
  | HTTP + SSE
  v
FastAPI Agent Host
  LiteLLM tool-calling loop
  Tool argument repair and schema validation
  Declarative policy and dynamic risk checks
  HITL approval state machine
  SQLite / Redis persistence
  Audit hash chain and decision logs
  |
  | MCP client / local fallback
  v
External Services
  GIS, TSDB, GB3838 evaluation, weather, drainage registry, MAVLink bus
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
- Create HITL approvals for risky actions.
- Execute safe local tools or MCP-backed production tools.
- Persist sessions, approvals, commands, audit events, and decision logs.
- Stream normalized AgentEvent updates to the HMI.

## River-Aware Map

The map no longer starts on a land-biased synthetic center. It uses an OpenStreetMap-derived Taopu River centerline:

- OSM way: `768410671`
- Name: `桃浦河`
- Tag: `waterway=river`
- Default center: `31.2755918, 121.3875979`
- River corridor threshold: `32 m`

Implementation details:

- `src/config/constants.ts` stores the default center, OSM provenance, river corridor radius, Taopu River path, drain points, and station points.
- `src/utils/geo.ts` provides haversine distance and nearest-point-on-path helpers.
- `src/services/MapService.ts` renders the river corridor and classifies clicked map points as `河道` or `陆地`.
- `src/styles/map.css` styles the river anchor marker and classification popup.

The classification is a deterministic frontend GIS visualization based on distance to the OSM river centerline. It is not a substitute for authoritative hydrographic survey data, bathymetry, navigation constraints, or production-grade geofencing.

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

- Python
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

## Repository Layout

```text
.
├── src/
│   ├── agents/          Frontend AgentClient and reconnecting SSE client
│   ├── components/      Vue UI components for map, panels, cockpit, approvals
│   ├── composables/     Command builders and UI composition helpers
│   ├── config/          Map constants, thresholds, MCP metadata, skills
│   ├── core/            Root store, event bus, logger, shared types
│   ├── services/        Map, telemetry, charts, persistence services
│   ├── stores/          Domain facades around the root store
│   ├── styles/          Layout, design tokens, map styles, animations
│   └── utils/           Time, math, geo, and formatting utilities
├── backend/
│   ├── app/
│   │   ├── agent/       Agent runner, SSE routes, state, context, tool gating
│   │   ├── core/        Config, cost model, database helpers
│   │   ├── mcp/         MCP client manager and FastMCP server
│   │   ├── policy/      Approval, audit, commands, declarative policy, risk
│   │   ├── routers/     LLM/debug routes
│   │   ├── schemas/     API schemas
│   │   ├── services/    LiteLLM gateway
│   │   ├── skills/      Skill registry, validation, real MCP executors
│   │   └── telemetry/   Backend telemetry stream
│   ├── config/          Policy configuration
│   ├── .env.example     Backend environment template
│   ├── .mcp.json        MCP server configuration example
│   └── run.ps1          Local FastAPI runner
├── docs/
│   ├── architecture.md
│   ├── agent-protocol.md
│   ├── litellm-gateway.md
│   └── mcp-integration.md
├── tests/
│   └── simulation/      Agent event protocol simulation tests
├── claude-plugin/       WaterClaw MCP/plugin packaging assets
├── bin/waterclaw.js     Project CLI
├── AGENTS.md            Durable agent and repository instructions
└── README.md
```

## Prerequisites

Install these before running the full system:

- Node.js 18 or newer
- npm
- Conda or Miniconda
- Python managed through the Conda environment created by the project
- A model provider key if you want live LLM calls

The frontend can run without provider keys. Backend LLM turns require a configured LiteLLM provider unless you only inspect health checks and static UI.

## Quick Start

Install dependencies and create the backend Conda environment:

```powershell
npm install
npm run waterclaw -- install
```

Start the full system:

```powershell
npm run waterclaw -- dev
```

Open:

```text
http://127.0.0.1:5173/
```

Backend health check:

```text
http://127.0.0.1:8787/api/health
```

## Manual Development Commands

Frontend only:

```powershell
npm run dev
```

Backend only:

```powershell
npm run backend:dev
```

Build frontend:

```powershell
npm run build
```

Run protocol simulation:

```powershell
npm run test:simulation
```

Generate API types after backend is running:

```powershell
npm run types:api
```

Run project doctor:

```powershell
npm run doctor
```

Clean generated local artifacts:

```powershell
npm run clean
```

## Environment Configuration

Copy the example backend environment file:

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

Set the provider key that matches your LiteLLM model:

```env
OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...
# OPENROUTER_API_KEY=sk-or-...
```

Do not put model provider keys in frontend environment files. Provider credentials belong on the backend only.

## MCP Configuration

MCP server configuration lives in `backend/.mcp.json`. The demo includes example entries for:

- InfluxDB time-series data
- City GIS
- GB3838 water-quality evaluation
- MAVLink command bus

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
WATERCLAW_APPROVAL_PEPPER=replace-with-a-secret
OTEL_ENABLED=true
OTEL_EXPORTER_OTLP_ENDPOINT=http://127.0.0.1:4317
```

External MCP output is treated as untrusted observation data. Keep provenance in tool results and do not silently convert degraded fallback results into production truth.

## Safety And Trust Boundaries

The project intentionally separates UI projection from real command execution:

- Frontend code must not claim hardware state changes as completed facts.
- Hardware-affecting actions go through backend approval, command records, idempotency keys, and audit.
- Critical tools must declare write permissions and remain behind HITL approval.
- MCP output is external data and must keep provenance.
- Local fallback data is explicitly marked degraded/local and should not be presented as production truth.
- Browser-side simulation paths are not part of production `src/`.

See `AGENTS.md`, `docs/architecture.md`, `docs/agent-protocol.md`, and `docs/mcp-integration.md` for the detailed operating model.

## Validation

Recommended validation after frontend changes:

```powershell
npm run build
```

Recommended validation after backend Python changes:

```powershell
python -m compileall backend/app
```

Recommended validation after Agent event protocol changes:

```powershell
python -m tests.simulation.run_illegal_discharge_simulation
```

For this repository snapshot, the frontend build has been verified with:

```text
vue-tsc --noEmit && vite build
```

## API Surface

Main backend routes include:

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

## GitHub Publishing Notes

The repository intentionally ignores:

- `node_modules/`
- `dist/`
- `.codex-tasks/`
- local backend databases and logs under `backend/.waterclaw/`
- generated backend scratch directories
- `backend/.env`
- root `.env`
- merged local export files such as `merged_frontend.txt`

Before publishing publicly, review `backend/.mcp.json` and all docs for organization-specific endpoint names. The default recommendation is to publish as a private repository until production endpoints, credentials, and demo data are audited.

## License

No license file is included yet. Until a license is added, all rights are reserved by the project owner.
