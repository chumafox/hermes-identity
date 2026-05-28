#!/usr/bin/env python3
"""MLX diagnostics: cold/warm/long generation, GPU memory tracking."""
import time, os, sys
import mlx.core as mx
from mlx_lm import generate, load

path = os.path.expanduser(sys.argv[1])
prompt = sys.argv[2] if len(sys.argv) > 2 else "Напиши одно предложение про ИИ."
max_tok = int(sys.argv[3]) if len(sys.argv) > 3 else 100

# 1. Load
t0 = time.monotonic()
model, tokenizer = load(path)
print(f"LOAD: {time.monotonic()-t0:.2f}s")
print(f"GPU_MEM: {mx.get_active_memory()/1e6:.0f} MB")

# 2. Cold
chat = f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
t0 = time.monotonic()
resp = generate(model, tokenizer, prompt=chat, max_tokens=max_tok, verbose=False)
elapsed = time.monotonic() - t0
tokens = len(resp.split()) if resp else 0
print(f"COLD: {elapsed:.2f}s, {tokens} слов, {tokens/elapsed:.1f} tok/s" if elapsed > 0 else "COLD: failed")

# 3. Warm (same prompt again)
mem_before = mx.get_active_memory()
t0 = time.monotonic()
resp2 = generate(model, tokenizer, prompt=chat, max_tokens=max_tok, verbose=False)
elapsed2 = time.monotonic() - t0
tokens2 = len(resp2.split()) if resp2 else 0
print(f"WARM: {elapsed2:.2f}s, {tokens2} слов, {tokens2/elapsed2:.1f} tok/s" if elapsed2 > 0 else "WARM: failed")
print(f"GPU_MEM_PEAK: {(mx.get_active_memory()-mem_before)/1e6:.0f} MB")
