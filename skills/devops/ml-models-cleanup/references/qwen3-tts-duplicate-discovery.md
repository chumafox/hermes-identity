# Qwen3-TTS Duplicate Discovery (2026-06-17)

## Структура
```
models--mlx-community--Qwen3-TTS-12Hz-0.6B-Base-4bit/
├── model.safetensors              # 977MB — КОПИЯ (inode 194175569)
├── speech_tokenizer/
│   └── model.safetensors          # 651MB — КОПИЯ (inode 194175619)
├── blobs/
│   ├── 07dcb37...                 # 977MB — оригинал (inode 195147615)
│   └── 836b7b...                  # 651MB — оригинал (inode 195147624)
└── snapshots/
    └── 0d6bb6.../
        ├── model.safetensors -> ../../blobs/07dcb37...  # симлинк
        └── speech_tokenizer/
            └── model.safetensors -> ../../blobs/836b7b...  # симлинк
```

## Ключевой приём — сравнение inode
```bash
ls -li model.safetensors          # смотрим inode
ls -li blobs/<hash>               # сравниваем
```
Если inode разные — это копия, а не симлинк. Корневой файл можно удалить.

## Почему так происходит
HF Hub cache создаёт blobs/ и snapshots/ с симлинками. Но когда модель скачивается не через huggingface_hub API, а вручную или через другой инструмент — файлы могут оказаться и в корне, и в blobs/ как независимые копии.

## Результат
Освобождено ~1.6GB (977MB + 651MB).
