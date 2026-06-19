# kimi-code Provider Configuration

kimi-code v0.14.3 uses TOML config at `~/.kimi-code/config.toml`.

## Provider types

| Type string | Valid? | Description |
|---|---|---|
| `openai` | ✅ | OpenAI-compatible API |
| `openai_legacy` | ❌ | **NOT valid** in v0.14.3 — causes `kimi doctor` error |
| `kimi` | ✅ | Managed Kimi API (OAuth) |
| `google-genai` | ✅ | Google Gemini API |

## Adding a custom provider (volc-coding example)

```toml
[providers.volc-coding]
type = "openai"           # NOT "openai_legacy"!
base_url = "https://ark.cn-beijing.volces.com/api/coding/v3"
api_key = "ark-xxxxx"

[models."volc-coding/deepseek-v4-flash"]
provider = "volc-coding"
model = "deepseek-v4-flash"
max_context_size = 102400
capabilities = [ "thinking", "image_in" ]
display_name = "DeepSeek V4 Flash (Volc)"
```

## Verification

```bash
kimi doctor                # должен быть OK
kimi provider list         # должен показывать новый провайдер
```

## Pitfalls

- `openai_legacy` causes `Invalid configuration: providers.volc-coding.type: Invalid input`
- Fix: change to `type = "openai"`
- After fixing, run `kimi doctor` to validate
- Provider appears as `volc-coding` in `kimi provider list` with N models
- Use with: `kimi -m volc-coding/deepseek-v4-flash`
