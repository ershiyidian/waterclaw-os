from __future__ import annotations

import asyncio
import math
import random
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Literal


RiskLevel = Literal["safe", "confirm", "critical"]
SkillCategory = Literal["analytics", "perception", "reports", "fleet", "emergency", "communications"]


@dataclass(frozen=True)
class SkillManifest:
    name: str
    label: str
    category: SkillCategory
    description: str
    input_schema: dict[str, Any]
    required_mcp: list[str]
    risk_level: RiskLevel
    permissions: dict[str, list[str]] = field(default_factory=dict)
    approval: dict[str, Any] | None = None

    def as_openai_tool(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": f"{self.label}: {self.description} Risk={self.risk_level}.",
                "parameters": self.input_schema,
            },
        }

    def as_public_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "label": self.label,
            "category": self.category,
            "description": self.description,
            "parameters": self.input_schema,
            "requiredMcp": self.required_mcp,
            "riskLevel": self.risk_level,
            "permissions": self.permissions,
            "approval": self.approval,
        }


@dataclass
class ExecutionContext:
    session_id: str
    operator_id: str
    approval_token: str | None = None
    mcp_manager: Any | None = None
    command_id: str | None = None
    idempotency_key: str | None = None
    allow_mock_fallback: bool = True


Executor = Callable[[dict[str, Any], ExecutionContext], Awaitable[dict[str, Any]]]


@dataclass(frozen=True)
class Skill:
    manifest: SkillManifest
    execute: Executor


def _schema(properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


def _series(base: float, length: int = 12, slope: float = 0) -> list[int]:
    return [round(base + math.sin(i * 0.7) * 12 + i * slope + random.uniform(-3, 3)) for i in range(length)]


async def query_sensor_data(args: dict[str, Any], ctx: ExecutionContext) -> dict[str, Any]:
    await asyncio.sleep(0.08)
    stations = [str(item) for item in args["stations"]]
    base = 162 if "TP-03" in stations else 42
    slope = 5.2 if "TP-03" in stations else 0.8
    return {
        "station": stations[0],
        "window": str(args["window"]),
        "series": _series(base, 16, slope),
        "unit": "NTU",
        "summary": "TP-03 浊度 5分钟内突增，趋势未回落。" if "TP-03" in stations else "全站点最近窗口数据读取完成。",
    }


async def ping_sensor(args: dict[str, Any], ctx: ExecutionContext) -> dict[str, Any]:
    await asyncio.sleep(0.05)
    sensor_id = str(args["id"])
    return {
        "ok": True,
        "sensorId": sensor_id,
        "calibrationHours": 41,
        "driftPct": 1.7,
        "checks": args["checks"],
        "summary": f"{sensor_id} 传感器通信正常，校准在72h内，漂移量低于阈值。",
    }


async def run_kmeans(args: dict[str, Any], ctx: ExecutionContext) -> dict[str, Any]:
    await asyncio.sleep(0.12)
    features = [str(item) for item in args["features"]]
    return {
        "hotspot": "DP-03 排口C",
        "confidence": 0.91,
        "clusters": [
            {"x": 42, "y": 34, "r": 18},
            {"x": 61, "y": 42, "r": 24},
            {"x": 53, "y": 61, "r": 14},
        ],
        "summary": f"k={int(args['k'])} 聚类中心锁定 DP-03，特征贡献最高为 {'/'.join(features)}。",
    }


async def lstm_predict(args: dict[str, Any], ctx: ExecutionContext) -> dict[str, Any]:
    await asyncio.sleep(0.13)
    station = str(args["station"])
    horizon = str(args["horizon"])
    values = [round(82 + pow(i, 2) * 1.1 + random.uniform(-4, 4)) for i in range(16)]
    return {
        "station": station,
        "horizon": horizon,
        "breachInMin": 45,
        "peakNtu": max(values),
        "classEstimate": "劣V类",
        "values": values,
        "confidence": float(args.get("confidence", 0.95)),
        "summary": f"{station} 未来{horizon}高概率突破 300 NTU，水质预计降至劣V类。",
    }


async def eval_gb3838(args: dict[str, Any], ctx: ExecutionContext) -> dict[str, Any]:
    await asyncio.sleep(0.08)
    stations = [str(item) for item in args["stations"]]
    degraded = "TP-03" in stations and len(stations) == 1
    return {
        "grade": "V 类" if degraded else "III 类",
        "pass": not degraded,
        "targetClass": str(args["targetClass"]),
        "metrics": [
            {"key": "pH", "value": "7.2", "limit": "6~9", "status": "ok"},
            {"key": "DO", "value": "6.5 mg/L", "limit": ">=5", "status": "ok"},
            {"key": "浊度", "value": "286 NTU" if degraded else "42 NTU", "limit": "<100", "status": "critical" if degraded else "ok"},
            {"key": "NH3-N", "value": "1.8 mg/L" if degraded else "0.8 mg/L", "limit": "<=1.0", "status": "critical" if degraded else "ok"},
            {"key": "CODMn", "value": "8.1 mg/L" if degraded else "4.2 mg/L", "limit": "<=6", "status": "warn" if degraded else "ok"},
        ],
        "summary": "TP-03 当前不满足 III 类目标，建议进入异常排放追溯流程。" if degraded else "所有核心指标处于 III 类水达标区间内，建议维持当前巡航频率。",
    }


async def plan_dubins_path(args: dict[str, Any], ctx: ExecutionContext) -> dict[str, Any]:
    await asyncio.sleep(0.1)
    target = str(args["target"])
    usv = str(args["usv"])
    path = [
        [31.2785, 121.3690],
        [31.2774, 121.3721],
        [31.2757, 121.3764],
        [31.2734, 121.3812],
        [31.2728, 121.3855],
    ]
    return {
        "path": path,
        "etaMin": 4,
        "lengthM": 612,
        "constraints": {"minTurnRadiusM": 18, "maxSpeedMps": 1.8},
        "summary": f"{usv} 至 {target} 的曲率受限拦截航线已生成，预计 4 分钟抵达。",
    }


async def dispatch_usv(args: dict[str, Any], ctx: ExecutionContext) -> dict[str, Any]:
    await asyncio.sleep(0.15)
    if not ctx.approval_token:
        raise PermissionError("dispatch_usv requires a valid one-time approval token.")
    if not ctx.command_id or not ctx.idempotency_key:
        raise PermissionError("dispatch_usv requires a durable command context.")
    usv = str(args["usv"])
    mission = str(args["mission"])
    return {
        "ack": True,
        "commandId": ctx.command_id,
        "idempotencyKey": ctx.idempotency_key,
        "usv": usv,
        "mission": mission,
        "target": str(args["target"]),
        "mavlinkSeq": random.randint(4200, 4999),
        "summary": f"{usv} {mission} 指令已通过后端 Policy Gate 写入 MAVLink-Bus。",
    }


async def notify_authority(args: dict[str, Any], ctx: ExecutionContext) -> dict[str, Any]:
    await asyncio.sleep(0.12)
    if not ctx.approval_token:
        raise PermissionError("notify_authority requires a valid one-time approval token.")
    if not ctx.command_id or not ctx.idempotency_key:
        raise PermissionError("notify_authority requires a durable command context.")
    incident_id = str(args["incidentId"])
    channel = str(args["channel"])
    return {
        "ticketId": "WC-20260428-003",
        "commandId": ctx.command_id,
        "idempotencyKey": ctx.idempotency_key,
        "incidentId": incident_id,
        "channel": channel,
        "summary": f"{incident_id} 一级预警工单已推送至 {channel}。",
    }


async def rtl_usv(args: dict[str, Any], ctx: ExecutionContext) -> dict[str, Any]:
    await asyncio.sleep(0.12)
    if not ctx.approval_token:
        raise PermissionError("rtl_usv requires a valid one-time approval token.")
    if not ctx.command_id or not ctx.idempotency_key:
        raise PermissionError("rtl_usv requires a durable command context.")
    scope = [str(item) for item in args["usvs"]]
    return {
        "ack": True,
        "commandId": ctx.command_id,
        "idempotencyKey": ctx.idempotency_key,
        "usvs": scope,
        "mode": "RTL_REQUESTED",
        "busAckId": f"RTL-{ctx.command_id[-8:]}",
        "summary": f"{'/'.join(scope)} RTL 返航请求已写入控制总线，等待艇端 ACK 状态回传。",
    }


async def request_estop(args: dict[str, Any], ctx: ExecutionContext) -> dict[str, Any]:
    await asyncio.sleep(0.08)
    if not ctx.approval_token:
        raise PermissionError("request_estop requires a valid one-time approval token.")
    if not ctx.command_id or not ctx.idempotency_key:
        raise PermissionError("request_estop requires a durable command context.")
    scope = [str(item) for item in args["usvs"]]
    return {
        "ack": True,
        "commandId": ctx.command_id,
        "idempotencyKey": ctx.idempotency_key,
        "usvs": scope,
        "mode": "ESTOP_REQUESTED",
        "busAckId": f"ESTOP-{ctx.command_id[-8:]}",
        "summary": f"{'/'.join(scope)} E-STOP 请求已发送到安全控制通道。UI 仅显示请求与回执，不宣称物理断电。",
    }


async def delegate_to_subagent(args: dict[str, Any], ctx: ExecutionContext) -> dict[str, Any]:
    from app.agent.subtasks import task_delegator

    task = await task_delegator.delegate(str(args["agent"]), dict(args.get("input") or {}))
    return {
        "taskId": task.task_id,
        "subAgent": task.sub_agent_name,
        "status": task.status,
        "result": task.result,
        "summary": (task.result or {}).get("summary", f"{task.sub_agent_name} delegated task {task.status}."),
    }


class SkillRegistry:
    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}
        self._bootstrap()

    def _register(self, skill: Skill) -> None:
        self._skills[skill.manifest.name] = skill

    def replace_executor(self, skill_name: str, executor: Executor) -> None:
        skill = self.get(skill_name)
        self._skills[skill_name] = Skill(manifest=skill.manifest, execute=executor)

    def _bootstrap(self) -> None:
        self._register(
            Skill(
                SkillManifest(
                    name="delegate_to_subagent",
                    label="委派子Agent",
                    category="analytics",
                    description="将专项分析委派给已注册的水质、路径或合规子 Agent。",
                    input_schema=_schema(
                        {
                            "agent": {
                                "type": "string",
                                "enum": ["water-quality-analyst", "usv-path-planner", "compliance-checker"],
                            },
                            "input": {"type": "object", "additionalProperties": True},
                        },
                        ["agent", "input"],
                    ),
                    required_mcp=[],
                    risk_level="safe",
                    permissions={"read": ["agent.context"]},
                ),
                delegate_to_subagent,
            )
        )
        self._register(
            Skill(
                SkillManifest(
                    name="query_sensor_data",
                    label="查询传感器数据",
                    category="perception",
                    description="从时序库读取指定站点的最近窗口数据。",
                    input_schema=_schema(
                        {
                            "stations": {"type": "array", "items": {"type": "string"}},
                            "window": {"type": "string", "description": "Example: 5m, 30m, 2h"},
                        },
                        ["stations", "window"],
                    ),
                    required_mcp=["influx-tsdb"],
                    risk_level="safe",
                    permissions={"read": ["telemetry.timeseries"]},
                ),
                query_sensor_data,
            )
        )
        self._register(
            Skill(
                SkillManifest(
                    name="ping_sensor",
                    label="传感器自检",
                    category="perception",
                    description="检查传感器通信、校准时间与漂移量。",
                    input_schema=_schema(
                        {
                            "id": {"type": "string"},
                            "checks": {"type": "array", "items": {"type": "string"}},
                        },
                        ["id", "checks"],
                    ),
                    required_mcp=["influx-tsdb"],
                    risk_level="safe",
                    permissions={"read": ["telemetry.health"]},
                ),
                ping_sensor,
            )
        )
        self._register(
            Skill(
                SkillManifest(
                    name="run_kmeans",
                    label="K-means热点聚类",
                    category="analytics",
                    description="对浊度、氨氮、VOCs 等多变量进行聚类，定位污染热点。",
                    input_schema=_schema(
                        {
                            "k": {"type": "integer", "minimum": 2, "maximum": 8},
                            "features": {"type": "array", "items": {"type": "string"}},
                            "station": {"type": "string"},
                        },
                        ["k", "features"],
                    ),
                    required_mcp=["influx-tsdb", "city-gis"],
                    risk_level="safe",
                    permissions={"read": ["telemetry.timeseries", "gis.layers"]},
                ),
                run_kmeans,
            )
        )
        self._register(
            Skill(
                SkillManifest(
                    name="lstm_predict",
                    label="LSTM趋势预测",
                    category="analytics",
                    description="生成未来时段水质预测与置信区间。",
                    input_schema=_schema(
                        {
                            "station": {"type": "string"},
                            "horizon": {"type": "string"},
                            "confidence": {"type": "number", "minimum": 0.5, "maximum": 0.99},
                        },
                        ["station", "horizon"],
                    ),
                    required_mcp=["influx-tsdb"],
                    risk_level="safe",
                    permissions={"read": ["telemetry.timeseries"]},
                ),
                lstm_predict,
            )
        )
        self._register(
            Skill(
                SkillManifest(
                    name="eval_gb3838",
                    label="GB3838实时评价",
                    category="reports",
                    description="按地表水环境质量标准进行站点评价。",
                    input_schema=_schema(
                        {
                            "stations": {"type": "array", "items": {"type": "string"}},
                            "targetClass": {"type": "string", "enum": ["I", "II", "III", "IV", "V"]},
                        },
                        ["stations", "targetClass"],
                    ),
                    required_mcp=["gb3838-eval", "influx-tsdb"],
                    risk_level="safe",
                    permissions={"read": ["telemetry.timeseries", "standards.gb3838"]},
                ),
                eval_gb3838,
            )
        )
        self._register(
            Skill(
                SkillManifest(
                    name="plan_dubins_path",
                    label="Dubins拦截路径",
                    category="fleet",
                    description="基于当前航向和目标点生成曲率受限任务级路径。",
                    input_schema=_schema(
                        {
                            "usv": {"type": "string"},
                            "target": {"type": "string"},
                        },
                        ["usv", "target"],
                    ),
                    required_mcp=["city-gis"],
                    risk_level="confirm",
                    permissions={"read": ["gis.layers", "fleet.state"]},
                    approval={"required": False, "reason": "只生成计划，不写入控制总线。"},
                ),
                plan_dubins_path,
            )
        )
        self._register(
            Skill(
                SkillManifest(
                    name="dispatch_usv",
                    label="派遣USV",
                    category="fleet",
                    description="向 MAVLink 指令总线下发任务级航行指令。",
                    input_schema=_schema(
                        {
                            "usv": {"type": "string"},
                            "mission": {"type": "string"},
                            "target": {"type": "string"},
                        },
                        ["usv", "mission", "target"],
                    ),
                    required_mcp=["mavlink-bus"],
                    risk_level="critical",
                    permissions={"read": ["fleet.state"], "write": ["mavlink.mission"], "hardware": ["usv"]},
                    approval={"required": True, "reason": "写入 MAVLink-Bus，会改变无人艇行为。", "minRole": "supervisor", "twoFactor": True},
                ),
                dispatch_usv,
            )
        )
        self._register(
            Skill(
                SkillManifest(
                    name="rtl_usv",
                    label="USV返航请求",
                    category="fleet",
                    description="向控制总线发送任务级 RTL 返航请求。",
                    input_schema=_schema(
                        {
                            "usvs": {
                                "type": "array",
                                "items": {"type": "string", "enum": ["USV-01", "USV-02"]},
                                "minItems": 1,
                                "uniqueItems": True,
                            },
                            "reason": {"type": "string", "minLength": 4, "maxLength": 240},
                        },
                        ["usvs", "reason"],
                    ),
                    required_mcp=["mavlink-bus"],
                    risk_level="critical",
                    permissions={"read": ["fleet.state"], "write": ["mavlink.mission"], "hardware": ["usv"]},
                    approval={"required": True, "reason": "返航会改变无人艇当前任务，需要人工确认。", "minRole": "supervisor", "twoFactor": True},
                ),
                rtl_usv,
            )
        )
        self._register(
            Skill(
                SkillManifest(
                    name="request_estop",
                    label="E-STOP请求",
                    category="emergency",
                    description="向安全控制通道发送 E-STOP 请求。此工具只声明请求和回执，不由前端伪造物理断电结果。",
                    input_schema=_schema(
                        {
                            "usvs": {
                                "type": "array",
                                "items": {"type": "string", "enum": ["USV-01", "USV-02"]},
                                "minItems": 1,
                                "uniqueItems": True,
                            },
                            "reason": {"type": "string", "minLength": 4, "maxLength": 240},
                        },
                        ["usvs", "reason"],
                    ),
                    required_mcp=["mavlink-bus"],
                    risk_level="critical",
                    permissions={"read": ["fleet.state"], "write": ["safety.estop"], "hardware": ["usv"]},
                    approval={"required": True, "reason": "E-STOP 属于安全控制请求，必须由后端审计并等待控制通道回执。", "minRole": "supervisor", "twoFactor": True},
                ),
                request_estop,
            )
        )
        self._register(
            Skill(
                SkillManifest(
                    name="notify_authority",
                    label="上报主管部门",
                    category="communications",
                    description="生成并推送预警工单到外部主管部门通道。",
                    input_schema=_schema(
                        {
                            "incidentId": {"type": "string"},
                            "channel": {"type": "string"},
                        },
                        ["incidentId", "channel"],
                    ),
                    required_mcp=["drainage-registry"],
                    risk_level="critical",
                    permissions={"read": ["incident.state"], "write": ["authority.ticket"]},
                    approval={"required": True, "reason": "外部上报会形成正式工单和审计记录。", "minRole": "supervisor", "twoFactor": True},
                ),
                notify_authority,
            )
        )

    def list(self) -> list[SkillManifest]:
        return [skill.manifest for skill in self._skills.values()]

    def openai_tools(self) -> list[dict[str, Any]]:
        return [manifest.as_openai_tool() for manifest in self.list()]

    def get(self, name: str) -> Skill:
        try:
            return self._skills[name]
        except KeyError as exc:
            raise KeyError(f"Skill not registered: {name}") from exc

    async def execute(self, name: str, args: dict[str, Any], ctx: ExecutionContext) -> dict[str, Any]:
        skill = self.get(name)
        return await skill.execute(args, ctx)


skill_registry = SkillRegistry()
