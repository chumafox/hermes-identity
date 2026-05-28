# MLX instruct models — chat template requirement

mlx_lm.generate() with instruct-tuned models requires the correct chat template.
A raw prompt produces `None` response.

## Qwen-style (ChatML)

```python
chat = "<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
```

Most Qwen-based models use this format (Vikhr, QVikhr, Qwen2.5).

## How to find the template

Check `tokenizer_config.json` in the model directory for the `chat_template` field.

## Verification

```python
from mlx_lm import generate, load
model, tokenizer = load(path)
resp = generate(model, tokenizer, prompt=chat, max_tokens=50, verbose=False)
assert resp is not None, "Chat template required!"
```
