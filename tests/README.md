# Tests

当前版本把旧 demo 线移出生产源码。测试目录保留一条正式 AgentEvent 协议模拟，用来验证“假装后端返回 LLM/tool/approval 事件”时，前端预期消费的事件顺序仍然和生产 Agent Host 一致。

```bash
npm run test:simulation
```

构建验证：

```bash
npm run waterclaw -- build
```

后续建议增加：

- Store actions 单元测试。
- 后端 Skill manifest / schema / policy 单元测试。
- AgentEvent SSE chunk boundary 与重复事件测试。
- approval hash mismatch、token reuse、idempotency 测试。
- MapService 与 ChartService 的轻量集成测试。
- Playwright 端到端截图和关键交互测试。
