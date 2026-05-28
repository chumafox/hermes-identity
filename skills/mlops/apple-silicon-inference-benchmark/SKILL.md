---
name: apple-silicon-inference-benchmark
description: Benchmark local LLM inference speed and memory on Apple Silicon (M1/M2/M3/M4). Tests Ollama (llama.cpp Metal) and mlx-lm backends. Memory-safe methodology for constrained machines (8GB).
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
---

# Apple Silicon Inference Benchmark

Benchmark local LLMs for speed (tok/s) and memory (GPU RAM, system RAM) on Apple Silicon Macs. Two backends: **Ollama (llama.cpp Metal)** for GGUF models, and **mlx-lm** for MLX-native models.

## When to use

- User asks "какая модель быстрее" or "сравни производительность"
- Need to choose between Ollama and MLX for a project
- Picking the right quantization for available RAM
- Determining if a model fits in memory (esp. 8GB Macs)
- Before building a local voice assistant or chat app

## Safety (8GB M1 Air critical rules)

1. **Check free RAM first** — `memory_pressure | grep "Pages free"` — need at least 300MB free before loading a model
2. **Unload between tests** — `ollama stop <model>` after each test; wait 2-3 seconds for memory to recover
3. **One model at a time** — never run two models concurrently on 8GB
4. **Watch GPU memory** — use `mx.get_active_memory()` for mlx-lm; `ollama ps` shows SIZE for Ollama
5. **If system overloads** (swap, beachball): immediately stop and free memory

## Methodology

### Ollama models (accurate tok/s)

Use `/api/generate` with `stream: false`. The response includes precise timing:

```bash
curl -s -X POST http://localhost:11434/api/generate \
  -d '{"model":"<model>","prompt":"<prompt>","stream":false,"options":{"num_predict":50,"temperature":0}}' \
  | python3 -c "
import json,sys; d=json.load(sys.stdin)
tok_s = d['eval_count']/(d['eval_duration']/1e9) if d['eval_duration'] > 0 else 0
print(f'tok/s: {tok_s:.1f}')
print(f'gen: {d[\"eval_duration\"]/1e6:.0f}ms ({d[\"eval_count\"]} tok)')
print(f'prompt: {d[\"prompt_eval_duration\"]/1e6:.0f}ms ({d[\"prompt_eval_count\"]} tok)')"
```

Key fields: `eval_count` (tokens), `eval_duration` (nanoseconds), `prompt_eval_count`, `prompt_eval_duration`.
Formula: `tok/s = eval_count / (eval_duration / 1e9)`

Memory: check `ollama ps` after load — `SIZE` column is GPU memory allocation.

### MLX models (accurate tok/s)

Use a Python script. Model configs are in `~/.lmstudio/models/`.

```python
import time
import mlx.core as mx
from mlx_lm import generate, load

model, tokenizer = load("<path>")
mem_before = mx.get_active_memory()

start = time.time()
response = generate(model, tokenizer, prompt=chat_prompt, max_tokens=50, verbose=False)
elapsed = time.time() - start

tokens = len(response.split())
tok_s = tokens / elapsed if elapsed > 0 else 0
print(f"tok/s: {tok_s:.1f}")
print(f"GPU_MEM: {(mx.get_active_memory()-mem_before)/1e6:.0f} MB")
```

**CRITICAL: Instruct/chat models need the chat template applied.** Raw prompt → empty response.

```python
# Qwen-style (ChatML)
chat_prompt = "<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"

# Llama-style
chat_prompt = "<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n"
```

Check `tokenizer_config.json` for the exact template.

### Memory monitoring

```bash
memory_pressure | head -4          # system free RAM
python3 -c "import mlx.core as mx; print(mx.get_active_memory())"  # GPU memory
ollama ps                          # Ollama GPU allocation
```

## Known findings (M1 Air 8GB)

- **Ollama (llama.cpp Metal)**: Q4_K_M 3B ~27 tok/s, Q4_K_S 4B ~20 tok/s
- **LM Studio**: uses llama.cpp internally (NOT mlx-lm), even for MLX-format models. Vikhr-1.5B MLX: 17.7 tok/s via LM Studio vs 10.6 via pure mlx-lm
- **mlx-lm**: 8bit 1.5B ~10-11 tok/s, 4bit 2B ~4-11 tok/s (depends on architecture)
- **llama.cpp is ~2.5x faster than mlx-lm** on M1 Air for same GPU memory bandwidth
- Reasons: llama.cpp has years of Metal kernel optimization; mlx-lm quantized inference is newer; 8bit MLX needs 2x memory bandwidth vs 4bit GGUF
- Q4_K_S 4B model allocates 3.4GB GPU on M1 Air — very tight on 8GB total RAM
- <more>Detailed comparison: see `references/lm-studio-vs-mlx-vs-ollama.md`</more>

### Importing GGUF to Ollama

```bash
cat > /tmp/Modelfile << 'EOF'
FROM /path/to/model.gguf
TEMPLATE "{{ .Prompt }}"
EOF
ollama create <name> -f /tmp/Modelfile
# Remove when done:
ollama rm <name>
```

## LM Studio API — измерение

LM Studio НЕ использует mlx-lm. Её движок — модифицированный llama.cpp. MLX safetensors конвертируются на лету.

### Замер

LM Studio не возвращает тайминги, только wall-clock:

```bash
START=$(date +%s%N)
curl -s -X POST http://localhost:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"<model>","messages":[{"role":"user","content":"Текст"}],"max_tokens":50,"temperature":0,"stream":false}'
```

Извлечь tok/s: `completion_tokens / wall_time`.

### Особенности

- Выбери модель в GUI → она активна для API
- Смена модели в GUI НЕ выгружает предыдущую из GPU
- `/v1/models` показывает все установленные модели, не только загруженные
- При переполнении памяти скорость падает до 2-5 tok/s (swapping)

### Модели на полке (локально)

~/.lmstudio/models/ содержит поддиректории по вендорам:

```
~/.lmstudio/models/
├── Qwen/Qwen2.5-3B-Instruct-GGUF/qwen2.5-3b-instruct-q4_k_m.gguf
├── Vikhrmodels/
│   ├── QVikhr-3-4B-Instruction-GGUF/QVikhr-3-4B-Instruction-Q4_K_S.gguf
│   └── Vikhr-Qwen-2.5-1.5B-Instruct-MLX_8bit/   (MLX safetensors)
└── lmstudio-community/
    ├── Phi-4-mini-reasoning-MLX-4bit/              (MLX safetensors)
    └── gemma-4-E2B-it-GGUF/gemma-4-E2B-it-Q4_K_M.gguf
```

## Scripts

- **[scripts/benchmark.py](scripts/benchmark.py)** — Full benchmark runner: Ollama models (short/medium prompts), auto-unload, JSON results
- **[scripts/test_mlx.py](scripts/test_mlx.py)** — Single MLX model test with chat template, tok/s, GPU memory
- **[scripts/diag_mlx.py](scripts/diag_mlx.py)** — Detailed MLX diagnostics (cold/warm/long, GPU tracking)

## Scripts

- **[scripts/benchmark.py](scripts/benchmark.py)** — Full benchmark runner: Ollama models (short/medium prompts), auto-unload, JSON results
- **[scripts/test_mlx.py](scripts/test_mlx.py)** — Single MLX model test with chat template, tok/s, GPU memory
- **[scripts/diag_mlx.py](scripts/diag_mlx.py)** — Detailed MLX diagnostics (cold/warm/long, GPU tracking)

## Pitfalls

- **Don't use curl-wall-clock time with Ollama** — `eval_duration` is the only accurate timing. curl adds 0.5-3s overhead.
- **Instruct models need chat template** — raw prompt → None response in mlx-lm. Always check `tokenizer_config.json`.
- **8GB machines** — Q4_K_S 4B allocates 3.4GB GPU. Test only with other apps closed.
- **Ollama caches models in memory** — always `ollama stop <model>` between tests. Check with `ollama ps`.
- **Ollama pull in China** — extremely slow (hours/days). Import local GGUF files via `ollama create` from Modelfile instead.
- **Direct llama-cli on 8GB** — `llama-cli` loads model fresh each time → slow swapping. Use `ollama serve` as daemon (keeps model cached in GPU).
- **Russian language quality varies wildly** — qwen2.5:3b = средний, Vikhr/QVikhr = отличный, Phi-4-mini = бред ("Итак dialogue proceedure")
- **Model paths** — `~/.lmstudio/models/<vendor>/<model>/<file>` for LM Studio models
- **Always test download speed in China** — before downloading any model, run a small speed test first: `curl -s -o /dev/null -w '%{speed_download}' --max-time 10 <mirror_url>`. Speeds range from 89 B/s to 5 MB/s depending on time-of-day and VPN.
