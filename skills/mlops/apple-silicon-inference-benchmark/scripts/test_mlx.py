#!/usr/bin/env python3
"""MLX model test: load + generate + measure tok/s + GPU memory."""
import time, sys, os
import mlx.core as mx
from mlx_lm import generate, load

path = sys.argv[1]
prompt_text = sys.argv[2] if len(sys.argv) > 2 else "Напиши одно предложение про искусственный интеллект."
max_tok = int(sys.argv[3]) if len(sys.argv) > 3 else 50

mem_before = mx.get_active_memory()
start = time.monotonic()
model, tokenizer = load(path)
print(f"LOAD_TIME: {time.monotonic()-start:.2f}s")

# ChatML format (Qwen-style). Adjust for other architectures.
chat = f"<|im_start|>user\n{prompt_text}<|im_end|>\n<|im_start|>assistant\n"

start = time.monotonic()
response = generate(model, tokenizer, prompt=chat, max_tokens=max_tok, verbose=False)
elapsed = time.monotonic() - start
mem_after = mx.get_active_memory()

tokens = len(response.split()) if response else 0
tok_s = tokens / elapsed if elapsed > 0 else 0
print(f"GEN_TIME: {elapsed:.2f}s")
print(f"TOKENS: {tokens}")
print(f"TOK_S: {tok_s:.1f}" if tok_s > 0 else "TOK_S: 0.0")
print(f"GPU_MEM: {(mem_after-mem_before)/1e6:.0f} MB")
print(f"RESP: {response[:150] if response else '[None]'}")
