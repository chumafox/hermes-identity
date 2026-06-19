---
name: generative-media
description: "Управление генерацией изображений, видео и аудио через muapi.ai"
tags: ["uncategorized"]
---

# Generative Media Skills

Набор инструментов для генерации медиа-контента через [muapi.ai](https://muapi.ai).

## Требования

1. Установить muapi-cli: `npm install -g muapi-cli`
2. Настроить API ключ: `muapi setup`

## Использование

Скрипты находятся в `~/.hermes/skills/generative-media-core/` и `~/.hermes/skills/generative-media-library/`.

### Core (базовые операции)

- `media/upload.sh` — загрузка файлов
- `media/generate-image.sh` — генерация изображения
- `media/generate-video.sh` — генерация видео  
- `media/image-to-video.sh` — изображение → видео
- `media/create-music.sh` — генерация музыки

### Library (экспертные сценарии)

- `visual/ui-design/` — дизайн UI
- `visual/logo-creator/` — создание логотипов
- `motion/cinema-director/` — кинематографическая генерация
- `edit/ai-clipping/` — AI клиппинг видео

## Модели

100+ моделей: Midjourney v7, Flux Kontext, Seedance 2.0, Kling 3.0, Veo3 и др.
