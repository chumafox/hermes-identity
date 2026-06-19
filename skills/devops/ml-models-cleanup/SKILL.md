---
name: ml-models-cleanup
description: Аудит и очистка ML-моделей на macOS — HF cache, LM Studio, Ollama, проектные модели. Поиск дублей, неиспользуемых моделей, освобождение места на SSD.
category: devops
trigger: пользователь жалуется на место на диске, просит найти/почистить модели, провести аудит ML-артефактов
---

# ML Models Cleanup

## Когда использовать
- Пользователь говорит «место тает», «SSD забит», «найди что весит много»
- Нужно понять какие ML-модели установлены и сколько занимают
- Периодическая профилактика (раз в 1-2 месяца)

## Типовые локации ML-моделей на macOS

| Локация | Тип | Типичный размер |
|---------|-----|----------------|
| `~/.cache/huggingface/hub/` | HF Hub cache | 3-10 GB |
| `~/.lmstudio/models/` | LM Studio модели | 2-10 GB |
| `~/.ollama/models/blobs/` | Ollama GGUF | 1-10 GB |
| `~/Projects/active/ai-ml/models/` | Проектные GGUF | 2-10 GB |
| `~/Library/Application Support/com.pais.handy/models/` | Handy (ASR) | 1-2 GB |
| `~/.cache/torch/hub/` | Torch Hub (Silero и др.) | 10-100 MB |
| `~/Documents/*/` | Модели в старых проектах | 0.5-2 GB |

## Шаги аудита

### 1. Найти все файлы >2GB
```bash
find /Users/jenyanovak -type f -size +2G -exec ls -lh {} \; 2>/dev/null | sort -k5 -hr
```

### 2. Найти все model-файлы >500MB
```bash
find /Users/jenyanovak \( -name "*.gguf" -o -name "*.safetensors" -o -name "*.bin" -o -name "*.pt" -o -name "*.pth" -o -name "*.ckpt" \) -type f -size +500M -exec ls -lh {} \; 2>/dev/null | sort -k5 -hr
```

### 3. Проверить размер каждой директории с моделями
```bash
du -sh ~/.cache/huggingface/hub/
du -sh ~/.lmstudio/
du -sh ~/.ollama/
du -sh ~/Projects/active/ai-ml/models/
```

### 4. Развернуть HF cache по моделям
```bash
for d in ~/.cache/huggingface/hub/models--*/; do
  name=$(basename "$d"); size=$(du -sh "$d" 2>/dev/null | cut -f1)
  echo "$size  $name"
done | sort -rh
```

### 5. Проверить какие модели реально используются
```bash
# Поиск ссылок на модель в коде проектов
grep -rl "model-name\|repo-id" ~/Projects/active/ --include="*.py" 2>/dev/null | grep -v .venv | head -10
```

## Типовые кандидаты на удаление

### Безопасно (Level 1) — не используются, только место
- Пустые HF модели (только метаданные, 4-32KB) — `models--facebook--seamless-m4t-v2-large/` и подобные
- Множественные whisper модели (large + medium + base + tiny) — оставить одну large
- `snac_24khz` — audio tokenizer, обычно не нужен отдельно
- `sentence-transformers/*` — если не используется semantic search

### Дубли HF cache (Level 2)
HF cache хранит файлы в `blobs/` и симлинки в `snapshots/`. Иногда в корне модели остаются копии тех же файлов — это дубли.

**Ключевой приём — сравнение inode:**
```bash
# Проверить inode — если разные, это копия, а не симлинк
ls -li model.safetensors
ls -li blobs/<hash>
```

**Реальный пример (Qwen3-TTS, 2026-06-17):**
```
models--mlx-community--Qwen3-TTS-12Hz-0.6B-Base-4bit/
├── model.safetensors              # 977MB, inode 194175569 — КОПИЯ
├── speech_tokenizer/
│   └── model.safetensors          # 651MB, inode 194175619 — КОПИЯ
├── blobs/
│   ├── 07dcb37...                 # 977MB, inode 195147615 — оригинал
│   └── 836b7b...                  # 651MB, inode 195147624 — оригинал
└── snapshots/
    └── 0d6bb6.../
        ├── model.safetensors -> ../../blobs/07dcb37...  # симлинк на blobs
        └── speech_tokenizer/
            └── model.safetensors -> ../../blobs/836b7b...  # симлинк на blobs
```

Если `model.safetensors` в корне и `blobs/<hash>` — разные inode, корневой можно удалить. Снапшот продолжит работать через симлинк. В этом примере освобождено ~1.6GB.

**Важно:** некоторые HF модели (особенно скачанные не через huggingface_hub, а вручную) имеют файлы только в корне, без blobs/ — там удалять нельзя.

### Требует решения (Level 3)
- Ollama GGUF в `ai-ml/models/` — если модель не используется в проектах
- LM Studio модели — если LM Studio не используется активно
- Локальные Ollama модели (`qwen2.5:3b` и т.д.) — нужен ли локальный инференс
- Старые проекты в `~/Documents/` с моделями внутри

## HF Cache: структура и дубли

```
models--mlx-community--Qwen3-TTS-12Hz-0.6B-Base-4bit/
├── model.safetensors          # 977MB — может быть копией blobs/
├── speech_tokenizer/
│   └── model.safetensors      # 651MB — может быть копией blobs/
├── blobs/
│   ├── 07dcb37...             # 977MB — оригинал (на него ссылается snapshot)
│   └── 836b7b...              # 651MB — оригинал
└── snapshots/
    └── 0d6bb6.../
        ├── model.safetensors -> ../../blobs/07dcb37...  # симлинк
        └── ...
```

Если `model.safetensors` в корне и `blobs/<hash>` — разные файлы (разные inode), корневой можно удалить. Снапшот продолжит работать через симлинк.

## Проверка после чистки
```bash
# Сводка по HF cache
du -sh ~/.cache/huggingface/hub/

# Свободное место
df -h /
```
