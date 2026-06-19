# Cleanup Session 2026-06-17

## Исходное состояние
SSD 245GB — 90% занято, свободно 22GB.
ML-модели разбросаны по 6 локациям, ~23GB всего.

## Что было удалено

### Уровень 1 — пустые/неиспользуемые HF модели
- `models--facebook--seamless-m4t-v2-large/` — только метаданные
- `models--mlx-community--whisper-small-mlx/` — только метаданные
- `models--Andycurrent--Gemma-3-1B-it-GLM-4.7-Flash-Heretic-Uncensored-Thinking_GGUF/` — только метаданные
- `models--Qwen--Qwen3-TTS-12Hz-0.6B-CustomVoice/` — только метаданные
- `whisper-base-mlx` (137MB) — не используется
- `whisper-tiny-mlx` (71MB) — не используется
- `snac_24khz` (76MB) — не используется
- `paraphrase-multilingual-MiniLM-L12-v2` (476MB) — не используется
- `whisper-medium-mlx` (1.4GB) — mlx_audio использует large-v3-turbo

### Уровень 2 — дубли Qwen3-TTS (~1.6GB)
Корневые `model.safetensors` (977MB) и `speech_tokenizer/model.safetensors` (651MB) — копии файлов в `blobs/`. Снапшоты ссылаются на blobs через симлинки, root-файлы были лишними.

### Уровень 3 — неиспользуемые модели (по решению пользователя)
- `gemma4-e2b-test-model.bin` + метаданные — ~3.1GB
- LM Studio (модели + app + кэш) — ~4.6GB

## Итог
Освобождено ~12GB. Свободно: 22GB → 34GB.

## Осталось нетронутым
- `german-tutor-model.bin` — 4.8GB (нужен)
- `qwen2.5:3b` — 1.8GB (Ollama, локальный инференс)
- `~/Downloads/audio_collection/` — 5.4GB (не трогать)
- `~/Documents/ANTI/` — 1.6GB (старый German-проект)
- `~/vendor/google-cloud-sdk/` — 703MB
- Handy (canary-1b-v2 + parakeet) — 1.6GB (голосовой ввод)
- Silero v4_ru.pt — 40MB (TTS)
