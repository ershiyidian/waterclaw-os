from __future__ import annotations

from typing import Any


MCP_SERVERS: list[dict[str, Any]] = [
    {
        "id": "litellm-gateway",
        "name": "LiteLLM-Gateway",
        "icon": "llm",
        "endpoint": "/api/agent/sessions/{session_id}/turn",
        "status": "connected",
        "permission": "restricted",
        "capabilities": {"resources": 1, "tools": 8, "prompts": 2},
        "callCount": 1,
        "latencyMs": 420,
        "lastCallAt": 1777381200000,
        "description": "后端 Agent Host 通过 LiteLLM 执行 tool-calling loop。",
        "transport": "internal",
        "allowedTools": ["completion", "tool_choice"],
    },
    {
        "id": "influx-tsdb",
        "name": "InfluxDB-TSDB",
        "icon": "stream",
        "endpoint": "mcp://waterclaw.local/influxdb",
        "status": "connected",
        "permission": "read-only",
        "capabilities": {"resources": 128, "tools": 7, "prompts": 2},
        "callCount": 2,
        "latencyMs": 88,
        "lastCallAt": 1777381200100,
        "description": "多源遥测时序数据库。",
        "transport": "streamable-http",
        "allowedTools": ["query.range", "query.last"],
    },
    {
        "id": "city-gis",
        "name": "City-GIS",
        "icon": "map",
        "endpoint": "mcp://shanghai.gov.cn/city-gis",
        "status": "connected",
        "permission": "read-only",
        "capabilities": {"resources": 31, "tools": 5, "prompts": 2},
        "callCount": 1,
        "latencyMs": 76,
        "lastCallAt": 1777381200200,
        "description": "河道、雨污管网、市政边界图层。",
        "transport": "streamable-http",
        "allowedTools": ["gis.layers", "gis.route_constraints"],
    },
]


ILLEGAL_DISCHARGE_AGENT_EVENT_FRAMES: list[dict[str, Any]] = [
    {
        "at": 0,
        "type": "state.patch",
        "data": {"agent": {"status": "thinking", "currentMission": "桃浦河异常排放追溯 #INC-20260428-003"}},
    },
    {
        "at": 20,
        "type": "message.delta",
        "data": {"content": "检测到 TP-03/DP-03 异常排放候选事件，开始按 SOP 补齐证据链。"},
    },
    {
        "at": 40,
        "type": "react.step",
        "data": {
            "thought": "DP-03 浊度突变可能来自偷排、降雨冲刷或传感器漂移。先排除传感器故障。",
            "action": 'ping_sensor({"id":"TP-03","checks":["calibration","drift","link"]})',
            "status": "running",
        },
    },
    {
        "at": 60,
        "type": "tool.started",
        "data": {
            "call": {
                "id": "sim-ping-sensor-001",
                "toolName": "ping_sensor",
                "category": "perception",
                "status": "running",
                "args": {"id": "TP-03", "checks": ["calibration", "drift", "link"]},
                "riskLevel": "safe",
                "replayable": True,
                "mcpServer": "influx-tsdb",
            }
        },
    },
    {"at": 75, "type": "mcp.status", "data": {"servers": MCP_SERVERS}},
    {
        "at": 160,
        "type": "tool.finished",
        "data": {
            "callId": "sim-ping-sensor-001",
            "result": {"ok": True, "calibrationHours": 41, "driftPct": 1.7, "summary": "TP-03 传感器通信正常，校准在72h内，漂移量低于阈值。"},
            "durationMs": 68,
        },
    },
    {
        "at": 180,
        "type": "react.step",
        "data": {
            "thought": "传感器自检通过，读取 TP-03/TP-04 最近窗口确认是否存在下游扩散梯度。",
            "observation": "TP-03 传感器通信正常，校准在72h内，漂移量低于阈值。",
            "status": "success",
        },
    },
    {
        "at": 240,
        "type": "tool.started",
        "data": {
            "call": {
                "id": "sim-query-sensor-002",
                "toolName": "query_sensor_data",
                "category": "perception",
                "status": "running",
                "args": {"stations": ["TP-03", "TP-04"], "window": "5m"},
                "riskLevel": "safe",
                "replayable": True,
                "mcpServer": "influx-tsdb",
            }
        },
    },
    {
        "at": 360,
        "type": "tool.finished",
        "data": {
            "callId": "sim-query-sensor-002",
            "result": {"station": "TP-03", "series": [162, 181, 203, 229, 247, 266, 286], "unit": "NTU", "summary": "TP-03 与 TP-04 出现阶梯式上升，存在下游扩散趋势。"},
            "durationMs": 112,
        },
    },
    {
        "at": 430,
        "type": "react.step",
        "data": {
            "thought": "多变量窗口已确认异常，使用聚类定位疑似污染热点。",
            "action": 'run_kmeans({"k":3,"features":["turbidity","NH3N","VOCs"],"station":"TP-03"})',
            "status": "running",
        },
    },
    {
        "at": 450,
        "type": "tool.started",
        "data": {
            "call": {
                "id": "sim-kmeans-003",
                "toolName": "run_kmeans",
                "category": "analytics",
                "status": "running",
                "args": {"k": 3, "features": ["turbidity", "NH3N", "VOCs"], "station": "TP-03"},
                "riskLevel": "safe",
                "replayable": True,
                "mcpServer": "city-gis",
            }
        },
    },
    {
        "at": 610,
        "type": "tool.finished",
        "data": {
            "callId": "sim-kmeans-003",
            "result": {"hotspot": "DP-03 排口C", "confidence": 0.91, "summary": "k=3 聚类中心锁定 DP-03，特征贡献最高为 turbidity/NH3N/VOCs。"},
            "durationMs": 147,
        },
    },
    {
        "at": 690,
        "type": "tool.started",
        "data": {
            "call": {
                "id": "sim-lstm-004",
                "toolName": "lstm_predict",
                "category": "analytics",
                "status": "running",
                "args": {"station": "TP-03", "horizon": "2h", "confidence": 0.95},
                "riskLevel": "safe",
                "replayable": True,
                "mcpServer": "influx-tsdb",
            }
        },
    },
    {
        "at": 830,
        "type": "tool.finished",
        "data": {
            "callId": "sim-lstm-004",
            "result": {"breachInMin": 45, "peakNtu": 318, "classEstimate": "劣V类", "summary": "TP-03 未来2h高概率突破 300 NTU，水质预计降至劣V类。"},
            "durationMs": 131,
        },
    },
    {
        "at": 900,
        "type": "tool.started",
        "data": {
            "call": {
                "id": "sim-plan-path-005",
                "toolName": "plan_dubins_path",
                "category": "fleet",
                "status": "running",
                "args": {"usv": "USV-01", "target": "DP-03"},
                "riskLevel": "confirm",
                "replayable": True,
                "mcpServer": "city-gis",
            }
        },
    },
    {
        "at": 1010,
        "type": "tool.finished",
        "data": {
            "callId": "sim-plan-path-005",
            "result": {"etaMin": 4, "lengthM": 612, "summary": "USV-01 至 DP-03 的曲率受限拦截航线已生成，预计 4 分钟抵达。"},
            "durationMs": 104,
        },
    },
    {
        "at": 1080,
        "type": "tool.started",
        "data": {
            "call": {
                "id": "sim-dispatch-approval-006",
                "toolName": "dispatch_usv",
                "category": "fleet",
                "status": "awaiting_approval",
                "args": {"usv": "USV-01", "mission": "DP-03_INTERCEPT_SAMPLE_30S", "target": "DP-03"},
                "riskLevel": "critical",
                "replayable": False,
                "mcpServer": "mavlink-bus",
            }
        },
    },
    {"at": 1090, "type": "tool.awaiting_approval", "data": {"callId": "sim-dispatch-approval-006", "approvalId": "approval-simulated-dispatch-001"}},
    {
        "at": 1100,
        "type": "approval.required",
        "data": {
            "approval": {
                "id": "approval-simulated-dispatch-001",
                "title": "审批高权限工具：dispatch_usv",
                "description": "模拟后端 Agent 已完成传感器、时序、聚类、预测和航线证据链。该事件只验证正式 HITL 投影协议，不会写入生产控制总线。",
                "riskLevel": "critical",
                "autoCancelSeconds": 60,
                "remainingSeconds": 60,
                "requestedAt": 1777381200000,
                "command": "dispatch_usv",
                "payload": {"usv": "USV-01", "mission": "DP-03_INTERCEPT_SAMPLE_30S", "target": "DP-03"},
                "argsHash": "simulated-args-hash",
                "requiresHoldMs": 2200,
                "requiresCode": True,
                "status": "pending",
            }
        },
    },
    {"at": 1120, "type": "state.patch", "data": {"agent": {"status": "awaiting_approval", "pendingApprovalId": "approval-simulated-dispatch-001"}}},
    {
        "at": 1140,
        "type": "message.final",
        "data": {"role": "assistant", "severity": "warn", "content": "证据链已补齐，模拟事件进入审批等待。未批准前没有控制命令，也没有 MAVLink-Bus 写入。"},
    },
]
