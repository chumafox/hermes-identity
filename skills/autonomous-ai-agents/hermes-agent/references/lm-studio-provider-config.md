# LM Studio Provider Setup for Hermes Agent

## Overview
LM Studio runs local LLMs with an OpenAI-compatible API server. Hermes Agent can use this as a provider — useful for offline operation, privacy, or when cloud APIs are slow/restricted.

## Prerequisites
- LM Studio installed (`lms` CLI in PATH)
- A model loaded in LM Studio (e.g. `gemma-4-e4b-it-mlx`)
- API server running on localhost:1234

## Quick Setup

### 1. Start LM Studio server
```bash
# Check loaded models
lms ps

# Start API server (one-time)
lms server start  # → "Server running on port 1234"

# If model needs loading:
lms load gemma-4-e4b-it-mlx
```

### 2. Configure Hermes Agent
```bash
# Set provider to use local LM Studio
hermes config set model.provider lmstudio
hermes config set model.default gemma-4-e4b-it-mlx
hermes config set model.base_url http://localhost:1234/v1
```

### 3. Add API key to .env
LM Studio doesn't require a real API key, but Hermes' openai-compatible provider expects one:
```bash
# In ~/.hermes/.env:
OPENAI_API_KEY=lm-studio

# Or through config:
hermes config set providers.lmstudio.api_key lm-studio
hermes config set providers.lmstudio.base_url http://localhost:1234/v1
hermes config set model.provider lmstudio
```

### 4. Test
```bash
hermes chat -q "What model are you?" --quiet
# Expected: "gemma-4-e4b-it-mlx" or whatever model is loaded
```

## Provider Selection Rules

Use these endpoint mappings for common LM Studio setups:

| LM Studio Setting | Hermes `model.base_url` | `model.provider` |
|---|---|---|
| Local server (default port) | `http://localhost:1234/v1` | `lmstudio` or `openai` |
| Remote server (same WiFi) | `http://192.168.x.x:1234/v1` | `lmstudio` or `openai` |
| Via SSH tunnel | `http://localhost:1234/v1` | `lmstudio` or `openai` |

## API key values LM Studio accepts
- Empty string `""` — authentication disabled
- `lm-studio` — any non-empty string works
- Any arbitrary string

## Context Window Issues
LM Studio models often have small context windows (e.g. Gemma-4: 4096 tokens). Hermes requires ≥64K tokens by default.

**Workaround (not recommended for production):**
```bash
hermes config set model.context_length 4096
```
This disables context compression threshold check. Skills, long conversations, and tool-heavy tasks will break.

**Better: use a model with ≥64K context.** Qwen2.5-7B, Mistral-7B, Llama-3-8B all support 32K-128K.

## Primary + Fallback Setup
With a local LM Studio as fallback behind a cloud provider:
```yaml
# config.yaml
model:
  default: deepseek-chat
  provider: deepseek

fallback_model:
  provider: lmstudio
  model: gemma-4-e4b-it-mlx
  base_url: http://localhost:1234/v1
```

Or swap: local model as primary (risky — small models can't self-diagnose complexity):
```yaml
model:
  default: gemma-4-e4b-it-mlx
  provider: lmstudio
  base_url: http://localhost:1234/v1

fallback_model:
  provider: deepseek
  model: deepseek-chat
```

## Troubleshooting

**Symptom:** `Primary auth failed — switching to fallback`
**Cause:** Hermes can't authenticate with LM Studio. Check `model.api_key` or `OPENAI_API_KEY`.

**Symptom:** `Provider kimi-coding ignores model.base_url`
**Cause:** Some built-in providers (kimi-coding, openrouter) hardcode their own base_url. Use a generic `openai` provider or the `lmstudio` custom provider instead.

**Symptom:** `ReadTimeout` or slow responses
**Cause:** Small models on MPS are slow (~5-20 tok/s for 7B models). This is normal — LM Studio runs on the GPU but local inference is orders of magnitude slower than cloud APIs.

**Symptom:** `lms` command not found
**Cause:** CLI binary is inside LM Studio.app bundle. Create symlink:
```bash
# Find the binary:
find /Applications/LM\ Studio.app -name "lms" -type f

# Symlink:
ln -sf "/Applications/LM Studio.app/Contents/Resources/app/.webpack/lms" /usr/local/bin/lms
```

## Related
- `lms ps` — list loaded models and status
- `lms ls` — list downloaded models
- `lms server start/stop` — control API server
- `lms load <model>` — load a model into memory
- `lms chat` — interactive chat in terminal
