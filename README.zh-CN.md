# WaterClaw OS / 河网智巡操作系统

[![CI](https://github.com/ershiyidian/waterclaw-os/actions/workflows/ci.yml/badge.svg)](https://github.com/ershiyidian/waterclaw-os/actions/workflows/ci.yml)

[English](README.md)



WaterClaw OS（河网智巡操作系统）是一个面向无人水面艇巡河、水质异常研判和应急处置的人机协同指挥界面与后端 Agent Host 原型。


项目集成了 Vue 工业驾驶舱、FastAPI 后端 Agent Host、LiteLLM 工具调用、MCP 集成、人工审批、水文遥测投影和河道感知地图能力。

> 当前状态：河道巡检人机协同界面的科研演示原型。

## 目录

- [核心亮点](#核心亮点)
- [演示场景](#演示场景)
- [架构](#架构)
- [河道感知地图](#河道感知地图)
- [技术栈](#技术栈)
- [仓库结构](#仓库结构)
- [快速启动](#快速启动)
- [环境配置](#环境配置)
- [MCP 集成](#mcp-集成)
- [安全与信任边界](#安全与信任边界)
- [验证](#验证)
- [API 概览](#api-概览)
- [公开仓库说明](#公开仓库说明)
- [许可证](#许可证)

## 核心亮点

- 工业风 Vue HMI，覆盖巡河地图、艇队状态、遥测、图表、告警、Agent 推理和操作员审批。
- Leaflet 地图默认启动在 OpenStreetMap 桃浦河 `waterway=river` 线段上，支持河道走廊渲染和点击点位的“河道/陆地”判定。
- FastAPI Agent Host 统一负责 LLM 回合、工具执行、策略校验、MCP 调用、审批状态、审计和 SSE 事件流。
- LiteLLM 网关支持 OpenAI 兼容服务、Anthropic、OpenRouter、Ollama 等模型后端。
- MCP 边界用于接入外部 GIS、时序遥测、GB3838 评价、气象、排水登记和无人艇指令总线适配器。
- 对高风险或影响硬件的动作提供人工审批流程。
- 本地默认使用 SQLite 持久化会话、审批、命令记录、审计链和决策日志。
- 可选 Redis 会话后端和 OpenTelemetry 链路追踪，便于生产化实验。

## 演示场景


默认场景模拟桃浦河巡查区域：

- USV-01 执行常态巡航，并可在审批后进入拦截采样任务。
- USV-02 在排口附近定点监测。
- TP-01 至 TP-05 监测断面、DP-01 至 DP-05 排口被投影到地图上。
- Agent 面板可以展示正式事件推理链：传感器自检、时序查询、聚类、预测、路径规划和审批请求。

## 架构

```text
前端指挥界面
  地图驾驶舱、遥测、图表、审批、对话、追踪
  |
  | HTTP + SSE
  v
后端智能体主机
  LiteLLM 工具调用循环
  工具参数修复与模式校验
  声明式策略与动态风险检查
  人工审批状态机
  SQLite / Redis 持久化
  审计哈希链与决策日志
  |
  | MCP 客户端 / 本地显式降级
  v
外部服务
  GIS、时序遥测、GB3838 评价、气象、排水登记、无人艇指令总线
```


前端职责：

- 渲染艇队、遥测、Agent、MCP、审批和地图状态的当前投影。
- 向后端发送操作员消息、Slash 命令、审批响应和硬控制请求。
- 以后端 SSE 事件作为状态真源。
- 不在浏览器中执行生产工具，也不在缺少后端事件时宣称真实硬件动作已完成。


后端职责：

- 构造 LLM 上下文并调用 LiteLLM。
- 通过动态工具门控决定可见工具。
- 修复并验证工具参数。
- 执行语义校验和声明式策略。
- 为高风险动作创建审批记录。
- 执行安全本地工具或 MCP 后端生产工具。
- 持久化会话、审批、命令、审计事件和决策日志。
- 向 HMI 推送规范化 AgentEvent。

## 河道感知地图


地图默认启动在经 OpenStreetMap / Overpass 验证的桃浦河中心线上，而不是偏向陆地的人工点位。

- OSM way: `768410671`
- 名称：`桃浦河`
- 标签：`waterway=river`
- 默认中心：`31.2755918, 121.3875979`
- 河道走廊阈值：`32 m`


实现位置：

- `src/config/constants.ts`：默认中心、OSM 来源、河道路径、走廊半径、排口与断面点位。
- `src/utils/geo.ts`：球面距离和折线最近点计算。
- `src/services/MapService.ts`：河道走廊渲染和“河道/陆地”判定弹窗。
- `src/styles/map.css`：地图锚点和弹窗样式。


**适用边界：**

- 河道/陆地判定基于点到 OSM 河道中心线的距离，是确定性可视化逻辑。
- 权威水文测绘、测深、通航约束与生产级电子围栏不在本原型的范围内。

## 技术栈

前端：


后端：

- 可选 Redis
- 可选 OpenTelemetry
启用 MCP 时使用 MCP Python SDK / FastMCP

工具链：

- npm 脚本与 `bin/waterclaw.js` CLI
- Conda 环境初始化
- `openapi-typescript` 用于生成 API 类型
- `tests/simulation` 下的协议模拟测试
- GitHub Actions 持续集成

## 仓库结构

```text
.
├── .github/workflows/   GitHub Actions 持续集成
├── src/                 Vue 前端源码
├── backend/             FastAPI 后端主机
├── docs/                架构、协议、MCP、LiteLLM 文档
├── tests/               AgentEvent 协议模拟测试
├── claude-plugin/       WaterClaw MCP/插件打包资源
├── bin/waterclaw.js     项目命令行工具
├── AGENTS.md            给代码 Agent 的仓库规范
├── SECURITY.md          安全政策与报告指引
└── README.md            项目说明
```


更细目录结构：

```text
src/
  agents/        Agent 客户端与断线重连 SSE 客户端
  components/    Vue 驾驶舱、地图、面板、审批与信息流组件
  composables/   命令构造器与 UI 组合辅助函数
  config/        地图常量、阈值、MCP 元数据、技能
  core/          根 store、事件总线、日志、共享类型
  services/      地图、遥测、图表、持久化服务
  stores/        根 store 的领域外观层
  styles/        设计变量、布局、动画、地图样式
  utils/         时间、数学、地理、格式化工具

backend/app/
  agent/         Agent 运行器、状态、路由、SSE、上下文、工具门控
  core/          配置、鉴权、成本、数据库辅助
  mcp/           MCP 客户端管理与 FastMCP 服务端
  policy/        审批、审计、命令、声明式策略、风险
  services/      LiteLLM 网关
  skills/        技能注册、校验、真实 MCP 执行器
  telemetry/     后端遥测流
```

## 快速启动


前置条件：

Node.js 18 或更高版本
Conda 或 Miniconda
由项目 Conda 环境管理的 Python
只有调用真实 LLM 时才需要模型供应商 API Key


安装依赖并创建后端 Conda 环境：

```powershell
npm install
npm run waterclaw -- install
```


启动完整系统：

```powershell
npm run waterclaw -- dev
```


打开前端：

```text
http://127.0.0.1:5173/
```


后端健康检查：

```text
http://127.0.0.1:8787/api/health
```


仅启动前端：

```powershell
npm run dev
```


仅启动后端：

```powershell
npm run backend:dev
```

## 环境配置


复制后端环境变量模板：

```powershell
Copy-Item backend/.env.example backend/.env
```


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


按模型供应商设置对应密钥：

```env
OPENAI_API_KEY=<your-openai-api-key>
# ANTHROPIC_API_KEY=<your-anthropic-api-key>
# OPENROUTER_API_KEY=<your-openrouter-api-key>
```


模型供应商密钥只应放在后端，不应放进前端环境文件。

## MCP 集成


MCP 服务配置位于 `backend/.mcp.json`。公开仓库中的示例端点刻意使用 `.example.invalid` 占位域名。真实环境启用 MCP 前，应替换为带鉴权的内部服务。


本地演示默认值：

```env
WATERCLAW_MCP_ENABLED=false
WATERCLAW_MOCK_FALLBACK_ENABLED=true
```


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


外部 MCP 输出属于不可信观测数据。工具结果必须保留来源，不应把降级 fallback 数据静默当作生产真值。

## 安全与信任边界


WaterClaw OS 将前端状态投影与真实物理执行明确分离。

- 前端代码不能把硬件状态变化宣称为已完成事实。
- 影响硬件的动作必须经过后端审批、命令记录、幂等键和审计。
- 高风险工具必须声明写权限，并置于人工审批之后。
- MCP 输出属于外部数据，必须保留来源。
- 本地 fallback 数据会显式标记为 degraded/local，不应展示为生产真值。
- 浏览器侧模拟路径不属于生产 `src/`。
- 公开仓库仅使用占位端点和占位密钥。


更多说明：

- `AGENTS.md`
- `SECURITY.md`
- `docs/architecture.md`
- `docs/agent-protocol.md`
- `docs/mcp-integration.md`

## 验证


前端构建：

```powershell
npm run build
```


后端语法检查：

```powershell
python -m compileall backend/app
```


AgentEvent 协议模拟：

```powershell
python -m tests.simulation.run_illegal_discharge_simulation
```


GitHub Actions 会运行同一组基线检查：

- `npm ci`
- `npm run build`
- `python -m pip install -r backend/requirements.txt`
- `python -m compileall backend/app`
- `python -m tests.simulation.run_illegal_discharge_simulation`

## API 概览


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


后端启动后可以通过 FastAPI 获取 OpenAPI schema。

## 公开仓库说明


仓库有意忽略本地和生成文件：

- `node_modules/`
- `dist/`
- `.codex-tasks/`
- `backend/.waterclaw/`
- `backend/backend/`
- root `.env`
- `backend/.env`
- 日志、Python 字节码和本地合并导出文件


### 生产部署清单

- 将 `.example.invalid` MCP 端点替换为带鉴权的服务端点。
- 真实模型密钥只能放入后端 secrets 或部署平台 secret manager。
- 生产环境禁用 mock fallback。
- 将后端置于带认证、限流和审计保留策略的 API Gateway 后。
- 接入真实无人艇总线前必须复核安全案例。

## 许可证

许可证尚未选定。
