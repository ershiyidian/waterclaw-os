# Security Policy / 安全策略

## Scope / 范围

This repository is a research and demonstration system for river-network patrol, water-quality incident response, and human-in-the-loop command workflows.

本仓库是面向河网巡查、水质事件响应和人工审批指令链路的科研与演示系统。

Security reports are in scope when they affect:

以下问题属于安全报告范围：

- Backend Agent Host authentication, authorization, or approval bypass.
- 后端 Agent Host 的认证、授权或审批绕过。
- Leakage of provider API keys, approval tokens, audit data, or local databases.
- 模型供应商 API Key、审批 token、审计数据或本地数据库泄露。
- Unsafe execution of critical or hardware-affecting tools.
- 高风险或影响硬件工具的不安全执行。
- MCP server trust boundary violations.
- MCP 服务信任边界绕过。
- Stored or reflected injection in the HMI.
- HMI 中的存储型或反射型注入。
- Supply-chain or CI issues that could alter release artifacts or repository state.
- 可能改变发布产物或仓库状态的供应链与 CI 问题。

## Reporting / 报告方式

Do not publish exploitable details in public issues.

请不要在公开 Issue 中发布可利用细节。

Use GitHub private vulnerability reporting if it is enabled for the repository. If it is not available, contact the repository owner through GitHub and request a private disclosure channel.

如果仓库启用了 GitHub private vulnerability reporting，请优先使用该渠道。如果没有，请通过 GitHub 联系仓库所有者并请求私密披露渠道。

## Public Demo Boundaries / 公开演示边界

- Public examples use placeholder `.example.invalid` endpoints.
- 公开示例使用 `.example.invalid` 占位端点。
- Public examples do not include provider API keys.
- 公开示例不包含模型供应商 API Key。
- Local fallback data is explicitly degraded/local and must not be represented as production truth.
- 本地 fallback 数据会显式标记 degraded/local，不应作为生产真值。
- The browser must not execute production tools or claim real hardware actions as completed facts.
- 浏览器不得执行生产工具，也不得宣称真实硬件动作已完成。
- Critical actions require backend approval, command records, idempotency keys, and audit.
- 高风险动作必须经过后端审批、命令记录、幂等键和审计。

## Deployment Guidance / 部署建议

Before connecting real telemetry, GIS, MCP, or USV command services:

接入真实遥测、GIS、MCP 或无人艇指令服务前：

- Replace placeholder endpoints with authenticated internal services.
- 将占位端点替换为带鉴权的内部服务。
- Store provider keys and approval peppers in a secret manager.
- 将模型密钥和审批 pepper 存放在 secret manager 中。
- Disable `WATERCLAW_MOCK_FALLBACK_ENABLED` in production.
- 生产环境禁用 `WATERCLAW_MOCK_FALLBACK_ENABLED`。
- Put the backend behind an API gateway with authentication and rate limiting.
- 将后端置于带认证和限流的 API Gateway 后。
- Enable audit retention and review audit-chain verification.
- 启用审计保留，并复核审计链校验。
- Perform a safety review before enabling write-side or hardware-affecting MCP tools.
- 启用写入类或影响硬件的 MCP 工具前进行安全评审。

## Supported Versions / 支持版本

This project currently has no stable release line. Security fixes are applied to the `main` branch.

当前项目尚无稳定版本线。安全修复会合入 `main` 分支。
