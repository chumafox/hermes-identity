# Apple Silicon — LM Studio vs mlx-lm vs Ollama

## Ключевое открытие

**LM Studio НЕ использует mlx-lm** для запуска MLX-форматных моделей. У LM Studio собственный движок на базе llama.cpp, который загружает safetensors через конвертацию в GGUF на лету.

Замерено на Vikhr-Qwen-1.5B 8bit:
| Бэкенд | tok/s | GPU память |
|--------|-------|------------|
| mlx-lm (прямой вызов generate) | 10.6 | 1.6 GB |
| LM Studio API (тот же safetensors) | 17.7 | ~1.6 GB |
| Ollama / llama-cli (GGUF Q4) | 27.0 | ~1.8 GB |

## Почему так

1. **llama.cpp Metal backend** точится годами — тысячи коммитов оптимизаций для Apple GPU
2. **mlx-lm** — моложе, quantized inference kernels менее оптимизированы
3. **8bit MLX** медленнее 4bit GGUF при том же memory bandwidth (2x данных на проход)
4. На M1 Air (8-core GPU) разница заметнее, чем на M1 Pro/Max

## Что это значит для тестов

- MLX модель в LM Studio работает с производительностью llama.cpp
- Для честного сравнения бэкендов нужна одна модель через оба движка
- mlx-lm даёт чистый замер MLX формата; LM Studio — практичный сценарий
- Если нужно просто запустить модель — LM Studio быстрее mlx-lm

## Сводная таблица (M1 Air 8GB)

| Модель | Размер | Ollama | LM Studio | mlx-lm | Русский |
|--------|--------|--------|-----------|--------|---------|
| qwen2.5:3b Q4_K_M | 1.9 GB | 27.0 | 22.9 | — | Средний |
| qwen2.5-coder:3b Q4 | 1.9 GB | 27.0 | — | — | Средний |
| QVikhr-3-4B Q4_K_S | 2.2 GB | 20.1 | 3.0* | — | Отличный |
| Vikhr-1.5B 8bit | 1.5 GB | — | 17.7 | 10.6 | Отличный |
| Phi-4-mini 4bit | 2.0 GB | — | — | 4.3 | Бред |
| Gemma-4-E2B Q4 | 3.2 GB | ❌ | ❌ | ❌ | Не влезает |

* QVikhr в LM Studio 3.0 tok/s — не хватило памяти, Vikhr уже занял 1.6GB GPU

## Замер LM Studio API

Без встроенных таймингов — замер через wall-clock:

```
START=$(date +%s%N)
curl -s -X POST http://localhost:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"<model>","messages":[{"role":"user","content":"Текст"}],"max_tokens":50,"temperature":0,"stream":false}'
```

Считать tok/s = completion_tokens / wall_time.

## Особенности LM Studio

- При смене модели в GUI старая остаётся в памяти (не выгружается)
- `/v1/models` показывает все установленные, не только загруженные
- Если модель не влезает в память, скорость падает до 2-5 tok/s (CPU/swapping)
- Не закрывает GPU при бездействии

## Скачивание моделей в Китае

| Источник | Скорость | 1GB за |
|----------|----------|--------|
| Ollama registry | ~90 B/s | ~130 дней |
| HuggingFace прямой | ~17 B/s | ~700 дней |
| hf-mirror.com | 308 (редирект) | — |
| modelscope.cn | 400 (ошибка) | — |

Единственный рабочий путь — GGUF файлы, скачанные заранее или через LM Studio Updater.

## Выводы

1. **Ollama** — самый быстрый бэкенд на M1 Air (27 tok/s на qwen2.5:3b)
2. **LM Studio** — 15-20% медленнее Ollama, но удобен GUI и ест любые форматы
3. **mlx-lm** — в 2-3x медленнее, но не требует сервера (из Python напрямую)
4. **Q4 GGUF через llama.cpp** даёт лучшую производительность на M1 Air
5. **8bit MLX** проигрывает Q4 GGUF при том же memory bandwidth
