# Транскрибация лекций Udemy (Apple Silicon M-серия)

После скачивания видео лекций — следующий шаг: транскрибация аудио в текст.

## Конфигурация

- **Mac:** M1 Pro, 32GB RAM
- **CPU:** Apple Silicon (ARM64)
- **Язык:** Русский (один спикер)
- **Объём:** 44 лекции, ~6.5 часов видео, ~8.1 GB

## Выбор инструмента

### 1. mlx-whisper (РЕКОМЕНДУЕТСЯ)

Самая быстрая опция на Apple Silicon. Использует Apple MLX framework — нативный Metal Performance Shaders.

```bash
pip install mlx-whisper
```

**Модель:** `mlx-community/whisper-large-v3-turbo-mlx`
- Размер: ~2.1 GB
- Точность: large-v3 уровня
- Скорость: ~6x быстрее openai-whisper
- Память: ~4 GB на M1 Pro (32 GB хватит с запасом)

**Параллельный запуск:** на M1 Pro 32 GB можно гнать 2-3 лекции одновременно.

**Использование:**
```python
import mlx_whisper

result = mlx_whisper.transcribe(
    "lecture.mp4",
    path_or_hf_repo="mlx-community/whisper-large-v3-turbo-mlx",
    language="ru",
    verbose=False
)

# Сохранить текст
with open("lecture.txt", "w") as f:
    f.write(result["text"])

# Сохранить с таймкодами (segments)
import json
with open("lecture.json", "w") as f:
    json.dump(result["segments"], f, ensure_ascii=False, indent=2)
```

### 2. faster-whisper (второй выбор)

CTranslate2-based. Медленнее mlx, но стабильнее на старых версиях.

```bash
pip install faster-whisper
```

**Модель:** `guillaumekln/faster-whisper-large-v3`

### 3. openai-whisper (PyTorch MPS)

Оригинал от OpenAI. PyTorch MPS backend. Самая медленная опция, наибольшее потребление памяти.

```bash
pip install openai-whisper
```

### 4. whisper.cpp (экономия памяти)

С++ реализация, quantized модели (Q5_0 ~2 GB). Можно скомпилировать с CoreML бэкендом для M1, но настройка сложная.

## Батч-скрипт (заготовка)

```python
#!/usr/bin/env python3
"""Batch transcribe all lecture mp4s."""
import glob, os, subprocess, sys, json
from pathlib import Path

LECTURES_DIR = Path.home() / "Downloads" / "udemy" / "romikwvf"
OUTPUT_DIR = Path.home() / "Downloads" / "udemy" / "transcripts"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

mp4s = sorted(glob.glob(str(LECTURES_DIR / "**" / "*.mp4"), recursive=True))
print(f"Found {len(mp4s)} lectures")

for i, mp4 in enumerate(mp4s):
    stem = Path(mp4).stem
    out_txt = OUTPUT_DIR / f"{stem}.txt"
    if out_txt.exists():
        print(f"SKIP [{i+1}/{len(mp4s)}] {stem} (already exists)")
        continue

    print(f"[{i+1}/{len(mp4s)}] Transcribing: {stem}")
    # Replace with your chosen tool:
    # mlx-whisper:  mlx_whisper.transcribe(mp4, ...)
    # faster-whisper: faster_whisper.WhisperModel(...)
    # OpenAI API:    openai.Audio.transcribe(...)
    print(f"    -> {out_txt}")
```

## Структура вывода

```
~/Downloads/udemy/transcripts/
├── 001 Первая лекция.txt
├── 001 Первая лекция.json   (с таймкодами)
├── 002 Вторая лекция.txt
└── ...
```
