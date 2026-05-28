# Hermes Provider Quirks

## kimi-coding Ignores config base_url
The `kimi-coding` plugin hardcodes its base_url in `__init__.py`:
- `KimiProfile` → `base_url="https://api.moonshot.ai/v1"`
- `kimi_cn` → `base_url="https://api.moonshot.cn/v1"`

Setting `model.base_url` in config.yaml does NOT override this.
To use a different URL, either:
- Create a `custom` provider entry
- Or edit the plugin's `__init__.py` directly

## LM Studio as Hermes Provider
LM Studio exposes an OpenAI-compatible API on `localhost:1234`.
To use it as a Hermes provider:

```bash
# Method 1: custom provider (recommended)
hermes config set providers.lmstudio.api_key lm-studio
hermes config set providers.lmstudio.base_url http://localhost:1234/v1
hermes config set model.provider lmstudio
hermes config set model.default gemma-4-e4b-it-mlx

# Method 2: openai provider (needs OPENAI_API_KEY=lm-studio)
# OPENAI_API_KEY=lm-studio hermes chat ...
```

The `openai` provider approach fails silently if the env var isn't set.
The `custom` provider embeds the key in config — more reliable.

## Fallback Mechanics
- Fallback triggers on: auth errors, rate limits (429), connection errors
- Fallback does NOT trigger on: ReadTimeout, stream drops, model errors
- `fallback_providers` in config can list multiple entries
- `fallback_model` is a single dict or list of dicts for chain fallback

## Weak Local Model + Cloud Fallback Problem
When the primary provider is a weak local model (e.g., Gemma-4 4B):
- The model can't self-diagnose task complexity
- It won't trigger fallback for tasks it can't handle
- **Solution:** Use cloud model as primary (DeepSeek), local as fallback
- Alternative: use `--provider deepseek` for complex one-off queries

## Credential Pool Backoff
After rate-limit, prevent retrying the primary for N seconds:

```bash
hermes config set agent.api_max_retries 1
hermes config set credential_pool_strategies.kimi-coding.backoff_seconds 7200
```

This triggers fallback on the first error and keeps the primary out of rotation for 2 hours.

## Context Window Minimum
Hermes requires ≥64,000 token context window. Models with smaller context
(e.g., Gemma-4 with 4,096) will fail with:
```
Model X has a context window of 4,096 tokens, which is below the minimum 64,000
```
Workaround: `hermes config set model.context_length 4096` (compression will degrade).

## Forced Provider Selection
```bash
hermes chat --provider deepseek --model deepseek-chat -q "prompt"
```
This bypasses the default provider entirely for a single query.
Useful for testing fallback or routing specific tasks.

## config set model.base_url "" — Empty String
Setting `base_url` to an empty string should be done via:
```bash
hermes config set model.base_url ""
```
This writes `base_url: ''` in config.yaml. Verify with:
```bash
grep base_url ~/.hermes/config.yaml
```

## Node.js Dependencies for Tools
Hermes tools requiring Node.js (browser, playwright, etc.) need:
- `node` and `npm` in PATH
- Install via portable bundle: `tar xzf node_portable.tar.gz -C /usr/local` with sudo -S
