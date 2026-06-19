# Бенчмарк M1 Air 8GB (MacBookAir10,1)

Дата: 2026-05-28

## Методология замера

**Правильно:** использовать поля `eval_count` / `eval_duration` из ответа Ollama API.
**Неправильно:** замерять curl wall-clock time (включает HTTP overhead, JSON парсинг).

```python
# Ollama generate response:
d["eval_count"] / (d["eval_duration"] / 1e9)  # tok/s
d["prompt_eval_duration"] / 1e6  # ms на промпт
```

## Ollama (llama.cpp Metal)

| Модель | Размер | tok/s | GPU RAM | Русский |
|--------|--------|-------|---------|---------|
| qwen2.5:3b Q4_K_M | 1.9 GB | **27.0** | 1.8 GB | Средний |
| qwen2.5-coder:3b Q4_K_M | 1.9 GB | **27.0** | 1.8 GB | Средний |
| QVikhr-3-4B Q4_K_S | 2.2 GB | **20.1** | 3.4 GB | Отличный ⭐ |

## LM Studio (тоже llama.cpp внутри)

| Модель | tok/s | Коммент |
|--------|-------|---------|
| qwen2.5-3b-instruct | **22.9** | Дефолтная, стабильно |
| vikhr-qwen-1.5b-mlx | **17.7** | Лучший русский, лёгкий |
| qvikhr-3-4b-instruction | **3.0** | Не влезает с др. моделями |

**Важно:** LM Studio НЕ использует mlx-lm для MLX моделей. Она конвертирует их в свой llama.cpp-совместимый формат. Поэтому Vikhr-1.5B через LM Studio (18 tok/s) быстрее чем через чистый mlx-lm (11 tok/s).

## mlx-lm (напрямую)

| Модель | Размер | tok/s | GPU |
|--------|--------|-------|-----|
| Vikhr-1.5B 8bit MLX | 1.5 GB | **10.6** | 1.6 GB |
| Phi-4-mini 4bit MLX | 2.0 GB | **4.3** | 2.1 GB |

mlx-lm медленнее llama.cpp на M1 Air в ~2.5x. Вероятно из-за менее зрелых Metal кернелов для quantized inference.

## Не влазит в 8GB
- Gemma-4-E2B Q4_K_M — 3.2 GB

## Выводы
- llama.cpp (Ollama/LM Studio) > mlx-lm на M1 Air в ~2.5x
- 8bit MLX жрёт столько же сколько 4bit GGUF, но медленнее
- Для local-siri: qwen2.5:3b через Ollama — оптимально (27 tok/s, без GUI)
- TTS: Piper irina-medium (~60MB, CPU, ~1-2s на фразу 5 слов)
