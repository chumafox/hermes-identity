# Hermes Provider Fallback for China

## Background

Two Macs: HK Mac (fast internet) + China Mac (slow/restricted WiFi + iPhone USB tethering + Thunderbolt bridge).

## Provider Config (headless China Mac)

Primary: LM Studio (local, 0 latency, no internet needed)
Fallback: DeepSeek (for complex reasoning, via API)
On-hold: Kimi (rate-limited after heavy use, 2-hour backoff)

## Config

```yaml
model:
  provider: lmstudio
  default: gemma-4-e4b-it-mlx
  base_url: http://127.0.0.1:1234/v1
providers:
  lmstudio:
    api_key: lm-studio
    base_url: http://127.0.0.1:1234/v1
agent:
  api_max_retries: 1
credential_pool_strategies:
  kimi-coding:
    backoff_seconds: 7200
fallback_model:
  provider: deepseek
  model: deepseek-chat
```

## Switching Providers On-the-Fly

```bash
# Use a specific provider for one command (no config change)
hermes chat --provider kimi-coding --model moonshot-v1-8k -q "..." --quiet

# Set permanent
hermes config set model.provider deepseek
hermes config set model.default deepseek-chat
hermes config set model.base_url ""
```

## Notes

- `kimi-coding` plugin has a hardcoded base_url in its `__init__.py` — the `model.base_url` config is only advisory for this provider.
- LM Studio listens on `127.0.0.1:1234` only — no remote access without SSH tunnel.
- DeepSeek API key is stored in `.env` as `DEEPSEEK_API_KEY`.
