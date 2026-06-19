# Kimi Code — Provider Configuration

## Provider types

kimi-code v0.14.3 accepts these provider types:
- `openai` — standard OpenAI-compatible API
- `kimi` — Kimi's own API (managed:kimi-code)
- `google-genai` — Google Gemini API

**`openai_legacy` is NOT supported** — it was accepted by the old kimi CLI but kimi-code rejects it with `providers.<name>.type: Invalid input`.

## Adding a custom provider (e.g. Volcengine Coding Plan)

### 1. Add provider block to `~/.kimi-code/config.toml`

```toml
[providers.volc-coding]
type = "openai"
base_url = "https://ark.cn-beijing.volces.com/api/coding/v3"
api_key = "ark-xxxx-xxxxx-xxxxx"
```

### 2. Add model aliases

```toml
[models."volc-coding/deepseek-v4-flash"]
provider = "volc-coding"
model = "deepseek-v4-flash"
max_context_size = 102400
capabilities = [ "thinking", "image_in" ]
display_name = "DeepSeek V4 Flash (Volc)"
```

Model key format: `<provider-id>/<model-name>`. The `display_name` is what shows in the model picker.

### 3. Validate

```bash
kimi doctor              # validates config.toml syntax
kimi provider list       # shows all providers + model counts
```

### 4. Use

```bash
kimi -m volc-coding/deepseek-v4-flash
# Or change default_model in config.toml:
# default_model = "volc-coding/deepseek-v4-flash"
```

## Known providers

| Provider ID | Type | Base URL |
|---|---|---|
| `deepseek` | `openai` | `https://api.deepseek.com` |
| `google` | `google-genai` | built-in |
| `managed:kimi-code` | `kimi` | `https://api.kimi.com/coding/v1` |
| `volc-coding` | `openai` | `https://ark.cn-beijing.volces.com/api/coding/v3` |

## Pitfalls

- **`openai_legacy` → kimi-code rejects it.** Always use `type = "openai"`.
- **`kimi doctor` is the validator.** Run it after any config change.
- **`kimi provider list` shows what's actually loaded.** If your provider doesn't appear, check the type field.
- **`kimi provider add` expects a registry URL**, not a manual config. For custom providers, edit config.toml directly.
