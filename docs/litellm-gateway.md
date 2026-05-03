# LiteLLM Gateway

WaterClaw OS 的 LLM 能力通过本地 Python 后端提供，而不是在浏览器中直接调用模型供应商 API。

## Why Backend

- 浏览器前端不能保存 `OPENAI_API_KEY`、`ANTHROPIC_API_KEY`、`OPENROUTER_API_KEY` 等密钥。
- LiteLLM 的 Python SDK 适合在应用后端统一封装多供应商模型。
- 前端只调用 `/api/agent/sessions/{session_id}/turn`。`/api/llm/agent-turn` 只保留为 legacy debug endpoint，不属于生产 UI 路径。
- 本地后端可以统一做超时、错误映射、审计、成本统计、权限控制和 HITL 策略。

## Setup

```powershell
npm run waterclaw -- install
```

`waterclaw install` 会安装前端依赖，使用 `backend/create-conda-env.ps1` 创建 Conda 环境 `waterclaw-llm`，并在该环境内用 `python -s -m pip --isolated --no-user` 安装 LiteLLM 相关依赖。不会向全局 Python 安装包。

编辑 `backend/.env`：

```env
LITELLM_MODEL=openai/gpt-4o-mini
OPENAI_API_KEY=<your-openai-api-key>
```

也可以使用 OpenRouter：

```env
LITELLM_MODEL=openrouter/openai/gpt-4o-mini
OPENROUTER_API_KEY=<your-openrouter-api-key>
```

或本地 Ollama：

```env
LITELLM_MODEL=ollama_chat/qwen2.5:7b
LITELLM_API_BASE=http://127.0.0.1:11434
```

## Run

终端 1：

```powershell
npm run waterclaw -- backend
```

默认使用 Conda 环境 `waterclaw-llm`。如需改环境名：

```powershell
$env:WATERCLAW_CONDA_ENV="your-env-name"
npm run waterclaw -- backend
```

终端 2：

```powershell
npm run waterclaw -- frontend
```

前端通过 Vite proxy 将 `/api/*` 转发到 `http://127.0.0.1:8787`。

## API

Health:

```http
GET /api/llm/health
```

Agent turn:

```http
POST /api/agent/sessions/{session_id}/turn
Content-Type: application/json
Accept: text/event-stream
```

请求包含当前任务、遥测、舰队状态、记忆和最近消息。后端通过 LiteLLM 发起 OpenAI-compatible tool calling，执行 JSON Schema 校验、Policy、HITL 和审计后，以 SSE 返回 `state.patch`、`react.step`、`tool.started`、`tool.finished`、`approval.required`、`message.final` 等正式 AgentEvent。

## Security Notes

- `.env` 不应提交到版本控制。
- 如果要给多人访问本地后端，可以设置 `WATERCLAW_LLM_GATEWAY_KEY`，再让前端或反向代理注入 `X-WaterClaw-LLM-Key`。
- 生产部署时建议把后端放在内网 API Gateway 后面，并加访问控制、审计日志、速率限制和模型预算。
- LiteLLM 依赖应定期更新；本项目 `backend/requirements.txt` 使用 `litellm>=1.83.0`，避免使用已知存在供应链风险的旧版本范围。

