# LM Studio: Model ID Mismatch

## Symptom

Hermes starts, sends a query to LM Studio, gets HTTP 400:

```
⚠️  API call failed (attempt 1/1): BadRequestError [HTTP 400]
   🔌 Provider: lmstudio  Model: gemma-4-e4b-it-ml
   🌐 Endpoint: http://127.0.0.1:1234/v1
   📝 Error: HTTP 400: Error code: 400
```

Then falls back to another provider (if configured) — causing a messy startup where the primary model fails every time.

## Root Cause

The model name in Hermes config (`model.default`) does not match the exact model ID returned by LM Studio's `/v1/models` endpoint.

## Diagnostic

```bash
# 1. Check what Hermes expects
grep 'default:' ~/.hermes/config.yaml

# 2. Check what LM Studio actually has loaded
curl -s http://127.0.0.1:1234/v1/models
```

Compare: the `id` field in LM Studio response vs. the `model.default` in config.yaml.

## Common Variation

LM Studio serves model IDs like `gemma-4-e4b-it-mlx` (MLX backend) but the user wrote `gemma-4-e4b-it-ml` (missing the `x`). The suffix `-mlx` means the model is loaded via Apple's MLX framework; `-gguf` would mean llama.cpp backend. Hermes needs the exact string.

## Fix

```bash
hermes config set model.default <exact-model-id-from-lm-studio>
```

Then restart Hermes.

## Also Check

- LM Studio API server is running (listen on port 1234 by default)
- LM Studio has a model loaded (not just downloaded — it must be selected in the UI or via `lms load`)
- `base_url` in Hermes config matches LM Studio endpoint (`http://127.0.0.1:1234/v1` by default)
- Some LM Studio builds use port 1234, others 8080 — verify with `lms status` or `ps aux | grep lm-studio`
