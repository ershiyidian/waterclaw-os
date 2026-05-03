---
name: waterclaw-incident-response
description: Use this skill when analyzing WaterClaw water-quality alerts, illegal discharge suspicion, sensor anomalies, GB3838 compliance, or USV mission planning.
---

# WaterClaw Incident Response

Follow this operating sequence:

1. Verify sensor health before assuming pollution.
2. Read recent telemetry from WaterClaw MCP tools.
3. Compare upstream and downstream stations.
4. Evaluate the current GB3838 target class.
5. Correlate drainage registry context, weather, and station history.
6. Forecast spread before proposing USV movement.
7. For MAVLink dispatch or authority notification, create a WaterClaw HITL approval request first.

Relevant MCP tools:

- `get_telemetry_snapshot`
- `query_sensor_data`
- `ping_sensor`
- `eval_gb3838`
- `run_hotspot_clustering`
- `predict_spread`
- `plan_usv_mission`
- `request_dispatch_approval`

Never claim that a USV has been dispatched unless WaterClaw returns a completed approved dispatch result. Direct low-level control, collision avoidance, motor commands, and E-STOP are outside the LLM boundary.
