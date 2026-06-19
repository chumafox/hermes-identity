# Qwen3-TTS Benchmarks on Apple Silicon

Source: community benchmarks + official Alibaba evaluations for Qwen3-TTS via `mlx-audio` (Blaizzy's benchmark script).

## Key Metrics

### 1. RTF (Real-Time Factor) — speed relative to real-time

**RTF = generation_time_ms / audio_duration_ms**

| Model | Backend | RTF | Real-time? |
|-------|---------|-----|------------|
| Qwen3-TTS 1.7B | MLX (Apple Metal) | **~0.79** | ✅ ~25% faster |
| Qwen3-TTS (any) | CPU GGUF / llama.cpp | **1.67–1.87** | ❌ Slower |
| Qwen3-TTS 0.6B | MLX | **~0.4–0.6** (extrapolated) | ✅ Significantly faster |

**Key insight:** MLX backend (Apple Metal via `mlx-audio`) is 2–2.5x faster than generic CPU inference on Apple Silicon. Always use MLX.

### 2. Latency — streaming breakdown (1.7B MLX)

| Metric | Value | What it means |
|--------|-------|---------------|
| **TTFAB** (Time To First Audio Byte) | **1–3 ms** | Negligible — first chunk arrives almost instantly |
| **Inter-chunk latency** | **50–90 ms** | Gap between streaming audio chunks |
| **Generation time per step** | **52–58 ms** | ~92% of total time spent on codec token generation |
| **Decode time** (token→waveform) | **244–457 ms** | Final conversion step (happens once, not per chunk) |

**Practical latency:** For short phrases (<50 chars), total delay before speech starts is a few hundred ms — acceptable for voice assistants.

### 3. Quality metrics

| Metric | Description | Qwen3-TTS 1.7B | Qwen3-TTS 0.6B |
|--------|-------------|--------------|--------------|
| **WER** (Word Error Rate) | Speech intelligibility — lower is better | **3.47%** (4-bit) / **3.66%** (8-bit) | **15.58%** (4-bit) / **9.74%** (8-bit) |
| **SIM** (Speaker Similarity) | For voice cloning — how close to reference | Better than ElevenLabs/MiniMax (Alibaba claim) | N/A (no voice cloning in 0.6B) |

**Critical observation:** 
- For 1.7B: 4-bit vs 8-bit quantization makes almost no difference (3.47% vs 3.66%) — always use 4-bit on constrained machines.
- For 0.6B: 4-bit is terrible (15.58% WER). 8-bit is better (9.74%) but still much worse than 1.7B. If using 0.6B, use 8-bit.

## Recommendations by Hardware

### M1 Air 8GB (display Mac, dispo)

- **Best option:** Edge TTS (online, 0 MB RAM, excellent quality)
- **Local fallback:** Qwen3-TTS 0.6B 4-bit via `mlx-audio`
  - Expected RTF: ~0.4–0.6 (fast)
  - Expected RAM: ~1.5 GB
  - Quality caveat: WER 15.58% — noticeably worse than 1.7B
  - Only use if offline, prefer 8-bit quantization for better quality
- **Not recommended:** Qwen3-TTS 1.7B — likely exceeds 8GB unified memory with macOS overhead (~2.5GB base)

### M1 Pro 32GB (pro, headless)

- **Best option:** Qwen3-TTS 1.7B 4-bit via `mlx-audio`
  - Expected RTF: ~0.6–0.8
  - Expected RAM: ~2.5–3 GB (plenty of headroom on 32GB)
  - WER 3.47% — excellent intelligibility
  - Voice cloning works (3s reference audio)
- **Alternative:** Qwen3-TTS 1.7B bf16 (full precision) if RAM allows — marginal quality gain

### Hardware Not Recommended

- **CPU-only inference (GGUF / llama.cpp)** — RTF 1.6+ (always slower than real-time)
- **Any model when memory_pressure < 20000 free pages** — risk of kernel panic on 8GB

## Setup on macOS with MLX

```bash
# Install
pip install mlx-audio

# Benchmark script (from Blaizzy)
curl -O https://gist.githubusercontent.com/Blaizzy/0f04043849274e858724d2d4fd714385/raw/qwen3_tts_benchmark.py

# Run benchmarks
python qwen3_tts_benchmark.py --model mlx-community/Qwen3-TTS-12Hz-1.7B-Base-bf16
python qwen3_tts_benchmark.py --batch-size 1 2 4 8
python qwen3_tts_benchmark.py -v --num-trials 3
```

## Summary Table

| Use case | Hardware | Recommended config | Expected RTF | WER |
|----------|----------|-------------------|-------------|-----|
| Online (preferred) | Any Mac | Edge TTS (Microsoft neural) | Network-bound | ~1% |
| Local, high quality | M1 Pro 32GB+ | Qwen3-TTS 1.7B 4-bit MLX | 0.6–0.8 | 3.47% |
| Local, lightweight | M1 Air 8GB | Qwen3-TTS 0.6B 8-bit MLX | 0.4–0.6 | 9.74% |
| Avoid | Any Mac | CPU GGUF backend | 1.6+ | — |
