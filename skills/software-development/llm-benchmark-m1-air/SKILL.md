---
name: llm-benchmark-m1-air
title: LLM Benchmark on M1 Air 8GB
description: Benchmark local LLMs for speed (tok/s) and memory usage on M1 Air 8GB. Tests through Ollama API, mlx-lm, and LM Studio. Auto-monitors RAM.
---

# LLM Benchmark on M1 Air 8GB

## Trigger
When the user asks to test/benchmark local LLM performance on this Mac.

## Available Models

### Ollama (llama.cpp Metal, GGUF Q4)
- `qwen2.5:3b` — 1.9GB, ~27 tok/s, ~1.1GB RAM
- `qwen2.5-coder:3b` — 1.9GB, ~27 tok/s, ~0.6GB RAM
- `qvikhr-3-4b` — 2.2GB, ~20 tok/s, 3.4GB GPU (tight on 8GB)

### mlx-lm (MLX native)
- `Vikhr-Qwen-1.5B 8bit` (~/.lmstudio/models/Vikhrmodels/) — 1.5GB, ~11 tok/s
- `Phi-4-mini 4bit` (~/.lmstudio/models/lmstudio-community/) — 2.0GB, ~4 tok/s

### LM Studio API (port 1234, OpenAI-compatible)
- ~23 tok/s for qwen2.5:3b (slightly slower than Ollama)

## Key Findings
- **Ollama (llama.cpp Metal) is ~2.5x faster than mlx-lm** on M1 Air 8GB
- For fair comparison: same model, same quantization, different backend
- 8bit MLX uses same GPU bandwidth as Q4 GGUF but slower due to kernel maturity
- QVikhr-3-4B Q4_K_S has best Russian but 3.4GB GPU — borderline for 8GB

## Benchmark Tools
- `benchmark.py` — automated benchmark (Ollama models + MLX models)
- `test_mlx.py` — MLX model test with chat template formatting
- `test_mlx2.py` — MLX test with `mx.get_active_memory()` GPU monitoring

## Safety on 8GB
1. Always check `memory_pressure` before loading models
2. `ollama stop <model>` between tests to free memory
3. If free < 100MB, don't load new models
4. MLX takes ~2s to load + frees memory on Python exit
5. `llama-cli` loads model fresh each time — slow on 8GB, use Ollama API instead

## Measuring Ollama Speed (most accurate)
Use curl to Ollama API and parse `eval_duration`/`eval_count`:
```bash
curl -s -X POST http://localhost:11434/api/generate \
  -d '{"model":"<name>","prompt":"<prompt>","stream":false,"options":{"num_predict":50,"temperature":0}}' \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'{d[\"eval_count\"]/(d[\"eval_duration\"]/1e9):.1f} tok/s')"
```

## Measuring MLX Speed
Use `test_mlx2.py` which calls `mx.get_active_memory()` for GPU RAM tracking.
