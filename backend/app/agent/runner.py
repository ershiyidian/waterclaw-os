from __future__ import annotations

import json
import time
from collections.abc import AsyncIterator
from dataclasses import asdict, dataclass
from typing import Any

from fastapi import HTTPException
from litellm import acompletion

from app.agent.context_builder import context_builder
from app.agent.decision_log import AgentDecisionRecord, decision_log
from app.agent.events import AgentEvent
from app.agent.state import SessionState
from app.agent.tool_arg_repair import tool_arg_repairer
from app.agent.tool_gating import dynamic_tool_gate
from app.core.config import Settings
from app.core.cost import calculate_cost_cny
from app.mcp.manager import mcp_manager
from app.otel import current_trace_id
from app.policy.approval import approval_service
from app.policy.audit import audit_log
from app.policy.commands import command_service
from app.policy.risk import policy_engine
from app.schemas.agent import AgentTurnRequest
from app.skills.registry import SkillManifest
from app.skills.validation import ToolArgumentError, validate_tool_args
from app.skills.registry import ExecutionContext, skill_registry


@dataclass
class ParsedToolCall:
    id: str
    name: str
    args: dict[str, Any]
    raw_args: str | dict[str, Any] = "{}"
    parse_error: str | None = None
    repair_warnings: list[str] | None = None


def _model_message_to_dict(message: Any) -> dict[str, Any]:
    if hasattr(message, "model_dump"):
        return message.model_dump(exclude_none=True)
    if isinstance(message, dict):
        return {key: value for key, value in message.items() if value is not None}
    return {
        "role": getattr(message, "role", "assistant"),
        "content": getattr(message, "content", "") or "",
        "tool_calls": getattr(message, "tool_calls", None),
    }


def _usage_dict(response: Any) -> dict[str, Any]:
    usage_obj = getattr(response, "usage", None)
    if hasattr(usage_obj, "model_dump"):
        return usage_obj.model_dump()
    if isinstance(usage_obj, dict):
        return usage_obj
    return {}


def _response_to_dict(response: Any) -> dict[str, Any]:
    if hasattr(response, "model_dump"):
        return response.model_dump(mode="json", exclude_none=True)
    if isinstance(response, dict):
        return response
    return {"repr": repr(response)}


def _extract_tool_calls(message: Any, visible_manifests: dict[str, SkillManifest]) -> list[ParsedToolCall]:
    raw = getattr(message, "tool_calls", None)
    if raw is None and isinstance(message, dict):
        raw = message.get("tool_calls")
    calls: list[ParsedToolCall] = []
    for call in raw or []:
        if hasattr(call, "model_dump"):
            item = call.model_dump()
        elif isinstance(call, dict):
            item = call
        else:
            item = {
                "id": getattr(call, "id", None),
                "function": getattr(call, "function", None),
                "type": getattr(call, "type", "function"),
            }
        function = item.get("function") or {}
        if hasattr(function, "model_dump"):
            function = function.model_dump()
        name = function.get("name")
        if not name:
            continue
        raw_args = function.get("arguments") or "{}"
        parse_error = None
        warnings: list[str] = []
        manifest = visible_manifests.get(name)
        if manifest is not None:
            args, warnings = tool_arg_repairer.repair(raw_args, manifest.input_schema)
        else:
            args = {}
            parse_error = f"Tool is not visible in current context: {name}"
        calls.append(
            ParsedToolCall(
                id=item.get("id") or f"tool-{int(time.time() * 1000)}-{len(calls)}",
                name=name,
                args=args,
                raw_args=raw_args,
                parse_error=parse_error,
                repair_warnings=warnings,
            )
        )
    return calls


def _safe_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


class AgentRunner:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _completion_kwargs(self, messages: list[dict[str, Any]], visible_tools: list[SkillManifest]) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "model": self.settings.litellm_model,
            "messages": messages,
            "tools": [manifest.as_openai_tool() for manifest in visible_tools],
            "tool_choice": "auto",
            "temperature": self.settings.litellm_temperature,
            "max_tokens": self.settings.litellm_max_tokens,
            "timeout": self.settings.litellm_timeout_seconds,
        }
        if self.settings.litellm_api_base:
            kwargs["api_base"] = self.settings.litellm_api_base
        return kwargs

    def _update_usage(self, session: SessionState, usage: dict[str, Any]) -> None:
        prompt = float(usage.get("prompt_tokens") or usage.get("input_tokens") or 0)
        completion = float(usage.get("completion_tokens") or usage.get("output_tokens") or 0)
        total = float(usage.get("total_tokens") or prompt + completion)
        if not prompt and total:
            prompt = max(0, total - completion)
        session.token_usage["input"] = float(session.token_usage.get("input", 0)) + prompt
        session.token_usage["output"] = float(session.token_usage.get("output", 0)) + completion
        session.token_usage["costCny"] = round(
            float(session.token_usage.get("costCny", 0)) + calculate_cost_cny(self.settings.litellm_model, prompt, completion),
            4,
        )

    def _event(self, event_type: str, data: dict[str, Any]) -> AgentEvent:
        trace_id = current_trace_id()
        if trace_id:
            data = {**data, "_trace_id": trace_id}
        return AgentEvent(event_type, data)

    async def run_turn(self, session: SessionState, req: AgentTurnRequest) -> AsyncIterator[AgentEvent]:
        session.status = "thinking"
        session.current_mission = req.mission
        if req.memory:
            session.memory = req.memory
        session.append_message("user", req.message)

        visible_tools, blocked_tools = await dynamic_tool_gate.evaluate(session)
        visible_manifest_by_name = {manifest.name: manifest for manifest in visible_tools}
        messages = await context_builder.build(session=session, req=req, visible_tools=visible_tools, blocked_tools=blocked_tools)

        yield self._event("state.patch", {"agent": {"status": "thinking", "currentMission": session.current_mission}})
        yield self._event(
            "react.step",
            {
                "thought": "后端 Agent Host 已接收上下文，正在通过 LiteLLM tool-calling loop 选择下一步。",
                "action": f"litellm.acompletion(model={self.settings.litellm_model}, tools={len(visible_tools)})",
                "status": "running",
            },
        )

        for step_index in range(self.settings.waterclaw_agent_max_steps):
            started = time.perf_counter()
            try:
                response = await acompletion(**self._completion_kwargs(messages, visible_tools))
            except Exception as exc:
                session.status = "idle"
                audit_log.write("agent.llm_error", {"session_id": session.session_id, "error": repr(exc)})
                yield self._event(
                    "message.final",
                    {
                        "role": "assistant",
                        "severity": "warn",
                        "content": f"LLM API 调用失败：{type(exc).__name__}: {exc}。后端 Agent Host 已保留审批与工具执行链路，请检查 backend/.env 中的模型供应商配置。",
                    },
                )
                yield self._event("state.patch", {"agent": {"status": "idle"}})
                return

            latency_ms = int((time.perf_counter() - started) * 1000)
            usage = _usage_dict(response)
            self._update_usage(session, usage)
            mcp_manager.register_call("litellm-gateway", latency_ms)
            yield self._event("mcp.status", {"servers": mcp_manager.list_status()})
            yield self._event("usage.patch", {"tokenUsage": session.token_usage})

            choice = response.choices[0]
            model_message = choice.message
            message_dict = _model_message_to_dict(model_message)
            tool_calls = _extract_tool_calls(model_message, visible_manifest_by_name)
            content = getattr(model_message, "content", None)
            if content is None and isinstance(model_message, dict):
                content = model_message.get("content")
            content = str(content or "").strip()

            messages.append(message_dict)
            if content:
                session.append_message("assistant", content)
                yield self._event("message.delta", {"content": content})

            decision_record = AgentDecisionRecord(
                session_id=session.session_id,
                step_index=step_index,
                messages_snapshot=messages[-12:],
                model_response=_response_to_dict(response),
                parsed_tool_calls=[asdict(call) for call in tool_calls],
                latency_ms=latency_ms,
                trace_id=current_trace_id(),
            )

            if not tool_calls:
                session.status = "idle"
                final = content or "处置链路已完成，暂无需要执行的工具。"
                decision_log.save(decision_record)
                yield self._event(
                    "react.step",
                    {
                        "thought": "模型未请求更多工具，当前轮次完成。",
                        "observation": f"finish_reason={getattr(choice, 'finish_reason', None)}",
                        "status": "success",
                    },
                )
                yield self._event("message.final", {"role": "assistant", "severity": "ai", "content": final})
                yield self._event("state.patch", {"agent": {"status": "idle"}})
                return

            for call in tool_calls:
                tool_name = call.name
                args = call.args
                if call.parse_error:
                    error = call.parse_error
                    audit_log.write("tool.arguments_parse_failed", {"session_id": session.session_id, "tool": tool_name, "error": error})
                    messages.append({"role": "tool", "tool_call_id": call.id, "content": _safe_json({"error": error})})
                    decision_record.tool_results.append({"tool": tool_name, "status": "failed", "error": error})
                    yield self._event("tool.failed", {"callId": call.id, "error": error})
                    continue
                try:
                    skill = skill_registry.get(tool_name)
                except KeyError:
                    error = f"未注册工具：{tool_name}"
                    messages.append({"role": "tool", "tool_call_id": call.id, "content": error})
                    decision_record.tool_results.append({"tool": tool_name, "status": "failed", "error": error})
                    yield self._event("tool.failed", {"callId": call.id, "error": error})
                    continue

                manifest = skill.manifest
                try:
                    args = validate_tool_args(manifest, args).args
                    policy_engine.validate_args_policy(
                        manifest,
                        args,
                        {"fleet": req.fleet, "telemetry": req.telemetry, "memory": session.memory, "alert_level": req.alert_level},
                    )
                except (ToolArgumentError, PermissionError) as exc:
                    error = f"Tool argument rejected before execution: {exc}"
                    audit_log.write(
                        "tool.arguments_rejected",
                        {"session_id": session.session_id, "tool": tool_name, "args": args, "error": str(exc)},
                    )
                    messages.append({"role": "tool", "tool_call_id": call.id, "content": _safe_json({"error": error})})
                    decision_record.tool_results.append({"tool": tool_name, "status": "failed", "error": error})
                    yield self._event("tool.failed", {"callId": call.id, "error": error})
                    continue

                decision = policy_engine.classify(manifest, args)
                decision_record.policy_decisions.append({"tool": tool_name, "args": args, "risk": decision.risk_level, "requiresApproval": decision.requires_approval, "reason": decision.reason})
                category = manifest.category
                call_payload = {
                    "id": call.id,
                    "toolName": tool_name,
                    "category": category,
                    "status": "running",
                    "args": args,
                    "riskLevel": decision.risk_level,
                    "replayable": decision.risk_level != "critical",
                    "mcpServer": manifest.required_mcp[0] if manifest.required_mcp else None,
                    "repairWarnings": call.repair_warnings or [],
                }
                session.status = "tool_call"
                for server_id in manifest.required_mcp:
                    mcp_manager.mark_calling(server_id)
                yield self._event("state.patch", {"agent": {"status": "tool_call"}})
                yield self._event("tool.started", {"call": call_payload})
                yield self._event(
                    "react.step",
                    {
                        "thought": f"模型请求调用 {tool_name}，后端 Policy Engine 判定风险为 {decision.risk_level}。",
                        "action": f"{tool_name}({_safe_json(args)})",
                        "status": "running",
                    },
                )

                if decision.requires_approval:
                    approval = approval_service.create(
                        session_id=session.session_id,
                        tool_name=tool_name,
                        args=args,
                        risk_level=decision.risk_level,
                        description=f"{decision.reason} 参数哈希已锁定，审批后只能执行同一组参数。",
                    )
                    session.pending_approval_id = approval.id
                    session.status = "awaiting_approval"
                    session.resume_messages = messages
                    decision_log.save(decision_record)
                    yield self._event("tool.awaiting_approval", {"callId": call.id, "approvalId": approval.id})
                    yield self._event(
                        "approval.required",
                        {"approval": approval.public(requires_code=bool(self.settings.waterclaw_approval_code))},
                    )
                    yield self._event("state.patch", {"agent": {"status": "awaiting_approval", "pendingApprovalId": approval.id}})
                    return

                tool_started = time.perf_counter()
                try:
                    result = await skill_registry.execute(
                        tool_name,
                        args,
                        ExecutionContext(
                            session_id=session.session_id,
                            mcp_manager=mcp_manager,
                            operator_id="agent-host",
                            allow_mock_fallback=self.settings.waterclaw_mock_fallback_enabled,
                        ),
                    )
                except Exception as exc:
                    result = {"error": f"{type(exc).__name__}: {exc}"}
                    messages.append({"role": "tool", "tool_call_id": call.id, "content": _safe_json(result)})
                    decision_record.tool_results.append({"tool": tool_name, "status": "failed", "result": result})
                    yield self._event(
                        "tool.failed",
                        {
                            "callId": call.id,
                            "error": result["error"],
                            "durationMs": int((time.perf_counter() - tool_started) * 1000),
                        },
                    )
                    continue

                duration_ms = int((time.perf_counter() - tool_started) * 1000)
                for server_id in manifest.required_mcp:
                    mcp_manager.register_call(server_id, duration_ms)
                audit_log.write(
                    "tool.executed",
                    {
                        "session_id": session.session_id,
                        "tool": tool_name,
                        "risk": decision.risk_level,
                        "args": args,
                        "duration_ms": duration_ms,
                    },
                )
                messages.append({"role": "tool", "tool_call_id": call.id, "content": _safe_json(result)})
                decision_record.tool_results.append({"tool": tool_name, "status": "success", "result": result, "durationMs": duration_ms})
                yield self._event("tool.finished", {"callId": call.id, "result": result, "durationMs": duration_ms})
                yield self._event(
                    "react.step",
                    {
                        "thought": "工具结果已回填给模型，继续判断是否需要下一步。",
                        "observation": str(result.get("summary") or result)[:260],
                        "status": "success",
                    },
                )
                yield self._event("mcp.status", {"servers": mcp_manager.list_status()})
            decision_log.save(decision_record)

        session.status = "idle"
        audit_log.write("agent.max_steps", {"session_id": session.session_id})
        yield self._event("message.final", {"role": "assistant", "severity": "warn", "content": "Agent 达到最大工具调用步数，已停止本轮执行。"})
        yield self._event("state.patch", {"agent": {"status": "idle"}})

    async def execute_approved(self, session: SessionState, approval_id: str, code: str, operator_id: str) -> AsyncIterator[AgentEvent]:
        try:
            approval, token = approval_service.approve(
                approval_id,
                code=code,
                operator_id=operator_id,
                expected_code=self.settings.waterclaw_approval_code,
            )
        except (PermissionError, ValueError, KeyError) as exc:
            yield self._event("approval.resolved", {"approvalId": approval_id, "status": "failed", "error": str(exc)})
            return

        try:
            skill = skill_registry.get(approval.tool_name)
            policy_engine.assert_allowed_after_approval(skill.manifest)
            validate_tool_args(skill.manifest, approval.args)
            policy_engine.validate_args_policy(skill.manifest, approval.args, {"memory": session.memory})
            command = command_service.create_or_get(
                approval_id=approval.id,
                session_id=session.session_id,
                tool_name=approval.tool_name,
                args=approval.args,
                requested_by=operator_id,
            )
            if command.status in {"acknowledged", "sent"} and command.result:
                approval_service.mark_used(approval.id)
                yield self._event("approval.resolved", {"approvalId": approval_id, "status": "approved", "command": command.public()})
                yield self._event(
                    "message.final",
                    {
                        "role": "assistant",
                        "severity": "ok",
                        "content": f"重复审批请求已按幂等键合并：{command.result.get('summary', command.command_id)}",
                    },
                )
                yield self._event("state.patch", {"agent": {"status": "idle", "pendingApprovalId": None}})
                return
            approval_service.start_execution(approval.id, token, approval.args, command.command_id, command.idempotency_key)
        except Exception as exc:
            yield self._event("approval.resolved", {"approvalId": approval_id, "status": "failed", "error": str(exc)})
            return

        session.pending_approval_id = None
        session.status = "tool_call"
        call_id = f"approved-{approval.id}"
        yield self._event("approval.resolved", {"approvalId": approval_id, "status": "approved"})
        yield self._event("state.patch", {"agent": {"status": "tool_call", "pendingApprovalId": None}})
        yield self._event(
            "tool.started",
            {
                "call": {
                    "id": call_id,
                    "toolName": approval.tool_name,
                    "category": skill.manifest.category,
                    "status": "running",
                    "args": approval.args,
                    "riskLevel": skill.manifest.risk_level,
                    "replayable": False,
                    "mcpServer": skill.manifest.required_mcp[0] if skill.manifest.required_mcp else None,
                }
            },
        )

        started = time.perf_counter()
        try:
            command_service.mark(command.command_id, "executing")
            result = await skill_registry.execute(
                approval.tool_name,
                approval.args,
                ExecutionContext(
                    session_id=session.session_id,
                    approval_token=token,
                    mcp_manager=mcp_manager,
                    operator_id=operator_id,
                    command_id=command.command_id,
                    idempotency_key=command.idempotency_key,
                    allow_mock_fallback=self.settings.waterclaw_mock_fallback_enabled,
                ),
            )
        except Exception as exc:
            approval_service.mark_failed(approval.id, f"{type(exc).__name__}: {exc}")
            command_service.mark(command.command_id, "failed", error=f"{type(exc).__name__}: {exc}")
            session.status = "idle"
            yield self._event("tool.failed", {"callId": call_id, "error": f"{type(exc).__name__}: {exc}"})
            yield self._event("state.patch", {"agent": {"status": "idle"}})
            return

        duration_ms = int((time.perf_counter() - started) * 1000)
        for server_id in skill.manifest.required_mcp:
            mcp_manager.register_call(server_id, duration_ms)
        audit_log.write(
            "tool.executed_after_approval",
            {
                "session_id": session.session_id,
                "approval_id": approval.id,
                "tool": approval.tool_name,
                "operator_id": operator_id,
                "duration_ms": duration_ms,
            },
        )
        command_service.mark(command.command_id, "acknowledged", result=result, bus_ack_id=str(result.get("mavlinkSeq") or result.get("ticketId") or command.command_id))
        approval_service.mark_used(approval.id)
        session.status = "idle"
        session.append_message("tool", _safe_json(result), tool_name=approval.tool_name)
        yield self._event("tool.finished", {"callId": call_id, "result": result, "durationMs": duration_ms})
        yield self._event(
            "message.final",
            {
                "role": "assistant",
                "severity": "ok",
                "content": f"审批动作已执行：{result.get('summary', approval.tool_name)}",
            },
        )
        yield self._event("mcp.status", {"servers": mcp_manager.list_status()})
        yield self._event("state.patch", {"agent": {"status": "idle"}})

    async def reject_approval(self, session: SessionState, approval_id: str, operator_id: str) -> AsyncIterator[AgentEvent]:
        try:
            record = approval_service.reject(approval_id, operator_id=operator_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        session.pending_approval_id = None
        session.status = "idle"
        yield self._event("approval.resolved", {"approvalId": approval_id, "status": record.status})
        yield self._event("message.final", {"role": "system", "severity": "warn", "content": f"人工拒绝：{record.tool_name}。控制总线未写入。"})
        yield self._event("state.patch", {"agent": {"status": "idle", "pendingApprovalId": None}})

    async def request_control(self, session: SessionState, tool_name: str, args: dict[str, Any], operator_id: str) -> AsyncIterator[AgentEvent]:
        try:
            skill = skill_registry.get(tool_name)
            validate_tool_args(skill.manifest, args)
            policy_engine.validate_args_policy(skill.manifest, args, {"memory": session.memory})
            decision = policy_engine.classify(skill.manifest, args)
        except Exception as exc:
            audit_log.write("control.request_rejected", {"session_id": session.session_id, "tool": tool_name, "args": args, "error": str(exc)})
            yield self._event("message.final", {"role": "system", "severity": "warn", "content": f"控制请求被后端拒绝：{exc}。未写入控制总线。"})
            yield self._event("state.patch", {"agent": {"status": "idle"}})
            return

        call_id = f"control-{tool_name}-{int(time.time() * 1000)}"
        yield self._event(
            "tool.started",
            {
                "call": {
                    "id": call_id,
                    "toolName": tool_name,
                    "category": skill.manifest.category,
                    "status": "awaiting_approval" if decision.requires_approval else "running",
                    "args": args,
                    "riskLevel": decision.risk_level,
                    "replayable": False,
                    "mcpServer": skill.manifest.required_mcp[0] if skill.manifest.required_mcp else None,
                }
            },
        )

        if decision.requires_approval:
            approval = approval_service.create(
                session_id=session.session_id,
                tool_name=tool_name,
                args=args,
                risk_level=decision.risk_level,
                description=f"{decision.reason} 请求来源：{operator_id}。控制动作不会在前端伪执行，必须等待后端审批和回执。",
            )
            session.pending_approval_id = approval.id
            session.status = "awaiting_approval"
            yield self._event("tool.awaiting_approval", {"callId": call_id, "approvalId": approval.id})
            yield self._event(
                "approval.required",
                {"approval": approval.public(requires_code=bool(self.settings.waterclaw_approval_code))},
            )
            yield self._event("message.final", {"role": "system", "severity": "warn", "content": f"{skill.manifest.label} 已提交后端审批。当前仅为请求状态，未宣称硬件已执行。"})
            yield self._event("state.patch", {"agent": {"status": "awaiting_approval", "pendingApprovalId": approval.id}})
            return

        yield self._event("message.final", {"role": "system", "severity": "warn", "content": "控制请求未标记为审批动作，已按安全策略拒绝。"})
        yield self._event("state.patch", {"agent": {"status": "idle"}})
