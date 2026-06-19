# M1 Air 8GB — Specific Benchmark Notes

This MacBook Air (M1, 8GB unified memory) has specific constraints and known model results.

## Safety Rules (8GB-specific)

1. **Check free RAM first** — `memory_pressure | grep "Pages free"` — need at least 300MB free
2. **Unload between tests** — `ollama stop <model>` after each test; wait 2-3 seconds
3. **One model at a time** — never run two models concurrently on 8GB
4. **Watch GPU memory** — `ollama ps` shows SIZE
5. **If system overloads** (swap, beachball): immediately stop and free memory
6. **Free pages below 15000 (~250MB)** = do NOT load another model
7. **Whisper large models** (medium: ~1.2GB, large-v3-turbo: ~2.5GB) are too heavy for 8GB

## Key Findings (M1 Air 8GB)

| Model | Backend | tok/s | GPU RAM | Verdict |
|-------|---------|-------|---------|---------|
| qwen2.5:3b Q4_K_M | Ollama (Metal) | ~27 | ~1.1 GB | ✅ Excellent |
| qwen2.5-coder:3b Q4_K_M | Ollama (Metal) | ~27 | ~0.6 GB | ✅ Excellent |
| QVikhr-3-4B Q4_K_S | Ollama (Metal) | ~20 | ~3.4 GB | ⚠️ Tight |
| Vikhr-Qwen-1.5B 8bit | mlx-lm | ~11 | ~1.6 GB | ⚠️ Slow |
| Phi-4-mini MLX 4bit | mlx-lm | ~4-11 | ~2.0 GB | ❌ Broken Russian |
| Gemma-4-E2B Q4_K_M | LM Studio/Ollama | ~10-15 | ~3.2 GB | ❌ Too heavy for 8GB |

## Ollama is ~2.4x faster than mlx-lm on M1 Air

Reason: llama.cpp has years of Metal kernel optimization. MLX quantized inference is newer.

## LM Studio Performance

LM Studio uses modified llama.cpp (NOT mlx-lm), even for MLX-format models. MLX safetensors are converted on the fly. LM Studio does NOT return eval_duration timing — only wall clock.

Measuring:
```bash
START=$(date +%s%N)
curl -s -X POST http://localhost:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"<model>","messages":[{"role":"user","content":"test"}],"max_tokens":50,"temperature":0,"stream":false}'
```

## Russian Language Quality

| Model | Russian Quality |
|-------|----------------|
| qwen2.5:3b | Средний (good enough) |
| QVikhr-3-4B / Vikhr-Qwen | Отличный (best for Russian) |
| Phi-4-mini | Бред ("Итак dialogue proceedure") |

## Available GGUF Models (this Mac)

```
~/.lmstudio/models/
├── Qwen/Qwen2.5-3B-Instruct-GGUF/qwen2.5-3b-instruct-q4_k_m.gguf
├── Vikhrmodels/QVikhr-3-4B-Instruction-GGUF/QVikhr-3-4B-Instruction-Q4_K_S.gguf
├── Vikhrmodels/Vikhr-Qwen-2.5-1.5B-Instruct-MLX_8bit/  (MLX)
├── lmstudio-community/Phi-4-mini-reasoning-MLX-4bit/    (MLX)
└── lmstudio-community/gemma-4-E2B-it-GGUF/gemma-4-E2B-it-Q4_K_M.gguf
```
