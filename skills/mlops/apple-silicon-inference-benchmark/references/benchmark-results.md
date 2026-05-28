# M1 Air 8GB — benchmark results (2026-05-28)

## Ollama (llama.cpp Metal, GGUF)

| Model | tok/s | GPU RAM | Size | Russian |
|---|---|---|---|---|
| qwen2.5:3b Q4_K_M | **27.0** | 1.8 GB | 1.9 GB | Medium |
| qwen2.5-coder:3b Q4_K_M | **27.0** | 1.8 GB | 1.9 GB | Medium |
| QVikhr-3-4B Q4_K_S | **20.1** | 3.4 GB | 2.2 GB | Excellent |
| Gemma-4-E2B Q4_K_M | — | — | 3.2 GB | Too large |

## mlx-lm (MLX native)

| Model | tok/s | GPU RAM | Size | Russian |
|---|---|---|---|---|
| Vikhr-1.5B 8bit | **10.6** | 1.6 GB | 1.5 GB | Excellent |
| Phi-4-mini 4bit | **4.3** | 2.1 GB | 2.0 GB | Gibberish |

## LM Studio (llama.cpp внутри, НЕ mlx-lm)

| Модель | tok/s | GPU RAM | Комментарий |
|--------|-------|---------|-------------|
| qwen2.5-3b-instruct | **22.9** | ~1.8 GB | Дефолтная, стабильно |
| vikhr-qwen-1.5b-mlx | **17.7** | ~1.6 GB | MLX safetensors, движок llama.cpp |
| qvikhr-3-4b-instruction | **3.0** | 3.4 GB | Не влез — Vikhr уже занял память |

## Key findings

- **Ollama (llama.cpp) is ~2.5x faster than mlx-lm** on M1 Air for same GPU memory bandwidth
- Q4_K_M 3B through Ollama: 27 tok/s consistent (cold or warm)
- mlx-lm 8bit 1.5B: 10.6 tok/s — slower despite smaller model
- Q4_K_S 4B on Ollama: 20.1 tok/s, but 3.4GB GPU allocation barely fits 8GB total
- Vikhr 1.5B MLX gives best Russian quality per MB of GPU RAM (1.6GB)
- qwen2.5:3b is the optimal balance for 8GB: 27 tok/s, fits with ~1GB system RAM to spare
