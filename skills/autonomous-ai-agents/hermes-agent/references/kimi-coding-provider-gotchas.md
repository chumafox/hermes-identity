# Kimi Coding Provider Gotchas

## Hardcoded base_url (ignores model.base_url)

The `kimi-coding` provider plugin (`plugins/model-providers/kimi-coding/__init__.py`) hardcodes its own `base_url`:

```python
kimi = KimiProfile(
    name="kimi-coding",
    ...
    base_url="https://api.moonshot.ai/v1",   # ← IGNORES user's model.base_url
    ...
)
```

This means setting `model.base_url: https://api.kimi.com/coding/v1` in `config.yaml` has **no effect** — the provider always uses `https://api.moonshot.ai/v1`.

### Impact

- You CANNOT override the API endpoint for `kimi-coding` via `model.base_url`
- The provider internally selects between `api.moonshot.ai/v1` (global) and `api.moonshot.cn/v1` (China) based on which profile you use (`kimi-coding` vs `kimi-coding-cn`)
- Simulating a Kimi failure for testing (by setting a dead `model.base_url`) will NOT cause the provider to fail — it still connects to the hardcoded moonshot endpoint instead

### Workaround

If you need a different endpoint for Kimi, you must either:
1. Create a custom provider plugin that overrides the base_url
2. Use the `openai` provider type with a custom base_url + API key
3. Switch to the `kimi-coding-cn` provider (uses `https://api.moonshot.cn/v1`) if you need the China endpoint

### Testing Provider Fallback

Because `model.base_url` doesn't affect `kimi-coding`, you CANNOT test fallback by setting a bad base_url. To force fallback activation during testing:
- Use an invalid model name: `hermes chat --model NOSUCHMODEL`
- Wait for actual rate limit (429) from Kimi
- Or temporarily remove/rename the API key from `.env`

## Fallback Activation Conditions

`fallback_model` in Hermes only activates on:
- **Rate limits (429)** ✅
- **Authorization failures** ✅
- **ReadTimeout / stream drops** ❌ (will retry primary instead)

For unstable connections, set:
```yaml
agent:
  api_max_retries: 1           # fail fast
credential_pool_strategies:
  kimi-coding:
    backoff_seconds: 7200      # don't retry Kimi for 2 hours after rate limit
```

## API Key Loading

`kimi-coding` reads its API key from `KIMI_API_KEY` env var (or `KIMI_CODING_API_KEY`). If you set `OPENAI_API_KEY` with a Kimi key, the provider won't find it — the key must be in the correct env var.
