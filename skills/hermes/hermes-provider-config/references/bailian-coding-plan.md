# Bailian Coding Plan — Subscription Details

**Source:** https://help.aliyun.com/zh/model-studio/coding-plan
**Date:** 2026-06-05

## Plan: Pro 高级套餐

| Item | Details |
|------|---------|
| **Price** | ¥200/month (~$28 USD) |
| **Requests** | 6,000 / 5h | 45,000 / week | 90,000 / month |

### Supported Models (exact versions only — strict whitelist)

**Recommended:**
- `qwen3.6-plus` (vision)
- `kimi-k2.5` (vision)
- `glm-5`
- `MiniMax-M2.5`

**Additional:**
- `qwen3.5-plus` (vision)
- `qwen3-max-2026-01-23`
- `qwen3-coder-next`
- `qwen3-coder-plus`
- `glm-4.7`

> ⚠️ Exact-match whitelist. `glm-5.1` won't work if only `glm-5` is listed.
> No version compatibility inference. Must match character-for-character.

### Usage Mechanics

- **Single query** consumes 5–10 requests (simple) or 10–30+ (complex)
- **5h quota** rolls over every minute (releases 5h-old requests automatically)
- **Weekly quota** resets Monday 00:00 (UTC+8)
- **Monthly quota** resets on subscription day each month
- **No refunds** once subscribed
- Limited daily stock (replenished 09:30 UTC+8)

### Compatible Tools

OpenClaw, **Hermes Agent**, Claude Code, OpenCode, Cursor, Codex, Qwen Code,
Cherry Studio, Chatbox, Cline, Qoder, Lingma, Kilo CLI

### Hermes Agent Configuration

```bash
hermes config set model.provider custom
hermes config set model.base_url https://coding.dashscope.aliyuncs.com/apps/anthropic
hermes config set model.api_mode anthropic_messages
hermes config set model.api_key YOUR_CODING_PLAN_KEY
hermes config set model.default qwen3.6-plus
```

> **Important:** Coding Plan API Key and Base URL are NOT interchangeable with
> pay-as-you-go (DashScope) keys. Do not mix them.

### vs Pay-as-you-go (наш случай)

| | Coding Plan | Pay-as-you-go |
|---|---|---|
| Price | ¥200/month fixed | Per-token (e.g. qwen3.6-plus ¥2/M input) |
| API Base | `coding.dashscope.aliyuncs.com` | `dashscope.aliyuncs.com` |
| API Mode | `anthropic_messages` | standard OpenAI |
| Models | Limited whitelist (~9) | All 211+ |
| Risk | Overage-proof (fixed cost) | Can run up bills if quota exhausted |
