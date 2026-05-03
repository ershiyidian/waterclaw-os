---
name: waterclaw-gb3838-report
description: Use this skill to generate concise GB3838 surface-water compliance reports from WaterClaw station telemetry.
---

# GB3838 Report

Use WaterClaw MCP in this order:

1. Call `query_sensor_data` for the station window requested by the operator.
2. Call `eval_gb3838` with the target class, usually `III`.
3. Identify the worst parameter, grade, exceedance state, and likely upstream/downstream relationship.
4. If the report implies enforcement action or public authority notification, request HITL approval instead of sending anything externally.

Report format:

- `结论`: target class pass/fail and current grade.
- `关键指标`: pH, DO, turbidity, NH3-N, CODMn with values and thresholds.
- `趋势`: whether the last window is rising, falling, or stable.
- `处置建议`: sensor recheck, extra sampling, USV mission planning, or approval request.
