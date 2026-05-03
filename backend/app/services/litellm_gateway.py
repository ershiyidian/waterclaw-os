import json
import time
from typing import Any

from fastapi import HTTPException
from litellm import acompletion

from app.core.config import Settings
from app.schemas.llm import AgentTurnRequest, AgentTurnResponse, ToolIntent


SYSTEM_PROMPT = """你是 WaterClaw OS 的城市水生态智能协同指挥 Agent。

你必须以工业 HMI 场景回答，语言为中文，风格简洁、专业、可执行。
你可以建议调用工具，但不能声称已经下发真实 USV 指令，除非请求中显示人工审批已通过。
高风险动作必须请求 HITL 审批，包括 MAVLink 派遣、E-STOP、向主管部门上报。

返回必须是严格 JSON，不要 Markdown，不要代码块：
{
  "content": "给操作员看的回答",
  "thoughts": ["结构化、可展示的简短推理步骤，不要泄露隐私或密钥"],
  "tool_intents": [
    {"tool_name": "eval_gb3838", "args": {"stations": ["TP-03"], "targetClass": "III"}, "reason": "为什么需要此工具"}
  ],
  "confidence": 0.0
}

可用工具名包括：
query_sensor_data, ping_sensor, run_kmeans, lstm_predict, eval_gb3838, plan_dubins_path, dispatch_usv, notify_authority。
"""


def _compact_context(req: AgentTurnRequest) -> str:
    context = {
        "session_id": req.session_id,
        "mission": req.mission,
        "alert_level": req.alert_level,
        "telemetry": req.telemetry.model_dump(),
        "fleet": [item.model_dump() for item in req.fleet],
        "memory": req.memory,
        "available_tools": req.available_tools,
        "recent_messages": req.recent_messages[-8:],
    }
    return json.dumps(context, ensure_ascii=False, separators=(",", ":"))


def _parse_json_content(content: str) -> dict[str, Any]:
    text = content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    return {"content": content, "thoughts": [], "tool_intents": [], "confidence": 0.55}


class LiteLLMGateway:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def agent_turn(self, req: AgentTurnRequest) -> AgentTurnResponse:
        started = time.perf_counter()
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"当前 WaterClaw OS 上下文 JSON：{_compact_context(req)}\n\n操作员输入：{req.message}",
            },
        ]
        kwargs: dict[str, Any] = {
            "model": self.settings.litellm_model,
            "messages": messages,
            "temperature": self.settings.litellm_temperature,
            "max_tokens": self.settings.litellm_max_tokens,
            "timeout": self.settings.litellm_timeout_seconds,
            "response_format": {"type": "json_object"},
        }
        if self.settings.litellm_api_base:
            kwargs["api_base"] = self.settings.litellm_api_base

        try:
            response = await acompletion(**kwargs)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"LiteLLM 调用失败：{type(exc).__name__}: {exc}") from exc

        choice = response.choices[0]
        content = choice.message.content or ""
        parsed = _parse_json_content(content)
        usage_obj = getattr(response, "usage", None)
        usage = usage_obj.model_dump() if hasattr(usage_obj, "model_dump") else dict(usage_obj or {})
        intents = []
        for item in parsed.get("tool_intents", []) or []:
            if isinstance(item, dict) and item.get("tool_name"):
                intents.append(ToolIntent(tool_name=str(item["tool_name"]), args=dict(item.get("args") or {}), reason=str(item.get("reason") or "")))

        return AgentTurnResponse(
            content=str(parsed.get("content") or content),
            thoughts=[str(item) for item in parsed.get("thoughts", []) if item],
            tool_intents=intents[:4],
            confidence=float(parsed.get("confidence") or 0.75),
            model=self.settings.litellm_model,
            usage=usage,
            latency_ms=int((time.perf_counter() - started) * 1000),
            raw_finish_reason=getattr(choice, "finish_reason", None),
        )
