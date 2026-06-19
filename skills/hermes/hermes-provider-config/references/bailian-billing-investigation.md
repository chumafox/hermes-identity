# Bailian Billing Investigation (2026-06-06)

## Symptom

Hermes falls back to secondary providers when using `bailian-cn` as primary. Direct curl to Bailian API returns:

```json
{"error":{"message":"Access denied, please make sure your account is in good standing.",
"type":"Arrearage","code":"Arrearage"}}
HTTP_CODE:400
```

But GET /v1/models works fine (200 OK), and API key is valid.

## Diagnostics Performed

### 1. API Key Check
```bash
echo "$BAILIAN_API_KEY"    # found: sk-07a3...
echo "$DASHSCOPE_API_KEY"  # empty!
```
**Root cause found:** config.yaml had `api_key_env: DASHSCOPE_API_KEY` but the actual env var was `BAILIAN_API_KEY`. Fixed with sed.

### 2. Free Quota Check (Bailian Console → 模型用量 → 免费额度)
- Total models with free quota: 165
- Models with >50% usage: 129 (all LLM models ~20% used)
- Models with >80% usage: 0
- Models WITHOUT free quota: 36 (paid-only)
- Top 3 consumption: qwen3.6-plus (20%, 803K/1M left), qwen3.7-plus (7%), qwen3.6-flash (2%)
- Free quota guard (用完即停): shown as "已开启" for most LLM models

### 3. Billing Check (费用与成本)
- Account balance: ¥9.79 → later -¥3.6 (changed during investigation)
- Outstanding charges: ¥0
- New orders this month: 0
- Banner: "部分功能使用受限" (some features restricted)

### 4. Notifications (消息中心 → 站内消息)
URL: `https://notifications2.console.aliyun.com/innerMsg/unread/0`
11 unread messages, timeline:

| Time | Type | Title |
|------|------|-------|
| 15:21 | 产品消息 | 阿里云百炼大模型推理服务欠费提醒 |
| 15:17 | 账户资金 | 可用额度不足提醒 |
| 13:44 | 服务消息 | Security tip (irrelevant) |
| 11:06 | 产品消息 | 免费额度量用尽通知 |
| 11:05 | 产品消息 | 免费额度余量预警 |
| 10:52 | 产品消息 | 免费额度量用尽通知 |
| 10:06 | 产品消息 | 阿里云百炼大模型推理恢复服务提醒 |
| 09:03 | 产品消息 | 阿里云百炼大模型推理服务欠费提醒 |
| 09:00 | 账户资金 | 可用额度不足提醒 |
| 08:56 | 产品消息 | 免费额度量用尽通知 |
| 2026/6/5 | 账户资金 | 延停权益通知 |

### 5. Support Response (在线服务 → 工单/机器人)

Question written in Chinese:
```
您好，我的账户余额从¥9.79变成了-¥3.60，但我只使用了免费额度模型（qwen3.6-plus, qwen3.6-flash等），
没有使用付费模型。今天收到了3次"免费额度量用尽通知"，然后API就开始返回"Arrearage"错误。
请问具体是哪几个模型的免费额度用完了？免费额度用完后应该返回403而不是扣费，为什么产生了欠费？
```

Support answer:
```
您好，免费额度用尽后产生欠费是因为默认情况下，免费额度耗尽后继续调用会直接按量扣费，而非返回 403 错误。

欠费原因：您未开启"免费额度用完即停"功能。当免费额度（如 qwen3.6-plus/flash）用尽后，系统自动转为按量付费，
导致账户余额扣除并产生欠费。

具体模型：请登录 账单详情，选择对应月份，在"商品名称"中筛选"阿里云百炼大模型推理"，
查看"资产/资源实例ID"列即可确认具体是哪个模型产生了费用。

避免再次欠费：建议在 模型用量-免费额度 页面开启"免费额度用完即停"。
开启后，额度用尽将返回 AllocationQuota.FreeTierOnly 错误并停止计费。
```

Key takeaway: **"免费额度用完即停" guard is OFF by default.** Bailian does NOT auto-stop when free quota runs out — it switches to postpaid billing.

## Resolution Steps

1. Fix `api_key_env` in config.yaml: `DASHSCOPE_API_KEY` → `BAILIAN_API_KEY` (done)
2. Populate billing account: at least ¥10 to restore API access
3. Enable "免费额度用完即停" for ALL models in console:
   - Navigate to 模型用量 → 免费额度
   - Click "批量操作免费额度用完即停"
   - Check all models, click 开启
4. After balance positive + guard ON: Bailian will return 403 (`AllocationQuota.FreeTierOnly`) instead of charging

## Error Code Reference

| HTTP | Type | Meaning | Action |
|------|------|---------|--------|
| 400 | Arrearage | Negative balance. Guard was OFF, free quota exhausted, billing kicked in | Top up account + enable guard |
| 401 | invalid_request_error | API key missing/wrong | Check api_key_env in config.yaml |
| 403 | AllocationQuota.FreeTierOnly | Free quota exhausted, guard ON — normal stop | Switch to another model with quota |
| 404 | — | Model not found | Check model name |

## What NOT to blame

- "Я использовал только free quota модели" — irrelevant. After free quota exhausts, SAME models become paid.
- "Осталось 803K токенов на qwen3.6-plus" — that's ONE model. Other models (across 5 tabs) may be fully exhausted.
- "Счёт был ¥9.79" — that's prepaid. Guard OFF → free quota exhaust → preapid consumption → arrears.
- "GET /v1/models работает" — model list endpoint is always available, not a health indicator.
