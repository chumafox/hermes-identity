---
name: local-siri
description: "Голосовой ассистент (русский) с распределённой архитектурой. Экранный Mac (M1 Air 8GB): VAD + STT. Безголовый Mac (M1 Pro 32GB): Ollama + Qwen3-TTS 1.7B."
version: 12
author: hermes-agent
---

# local-siri — Голосовой ассистент (распределённый)

## Новая архитектура (June 2026)

Экранный Mac (dispo, M1 Air 8GB):
- Микрофон → VAD → mlx-whisper STT
- Отправка текста на безголовый по WiFi
- Воспроизведение ответного аудио

Безголовый Mac (admin, M1 Pro 32GB):
- HTTP-сервер (FastAPI) на порту 8642
- Получает текст → Ollama qwen2.5:3b → Qwen3-TTS 1.7B (MLX)
- Возвращает WAV/MP3 аудио

**Причина:** Qwen3-TTS 1.7B не влезает в 8GB M1 Air. Перенос LLM + TTS на безголовый с 32GB.

## Компоненты

### Экранный Mac (клиент)
- Микрофон → Silero VAD ONNX → mlx-whisper base (GPU)
- Отправка текста на безголовый по HTTP (POST /tts с текстом)
- Получение аудио → afplay
- Код: ~/Documents/local-siri/assistant.py (модифицированная версия)

### Безголовый Mac (сервер)
- HTTP API (FastAPI) на порту 8642
- Принимает текст → Ollama (qwen2.5:3b, localhost:11434) → ответ
- Ответ → Qwen3-TTS 1.7B (MLX, GPU/MPS) → WAV 24kHz → возврат
- Репозиторий: ~/shelf/qwen3-tts-apple-silicon (MLX-оптимизированный)

## Сеть между Mac

Оба Mac в одной WiFi сети корабля (192.168.102.0/23):
- Экранный: 192.168.103.192 (DHCP)
- Безголовый: 192.168.103.70 (статический)

SSH ключ: ~/.ssh/id_ed25519_hermes → admin@192.168.103.70

Для интернета на безголовом (если корабельный WiFi не даёт):
- SOCKS5 SSH-туннель через экранный Mac (iPhone USB)
- `/usr/local/bin/hermes-proxy` на безголовом — wrapper с автоподнятием туннеля

## Модели Qwen3-TTS (MLX 8bit)

Все модели 1.7B MLX 8bit от mlx-community:

| Модель | Режим | Размер | Назначение |
|--------|-------|--------|------------|
| Qwen3-TTS-12Hz-1.7B-CustomVoice-8bit | custom | ~1.7GB | Кастомный голос (референс 3с) |
| Qwen3-TTS-12Hz-1.7B-VoiceDesign-8bit | design | ~1.7GB | Дизайн голоса по тексту |
| Qwen3-TTS-12Hz-1.7B-Base-8bit | base | ~1.7GB | Базовый, клонирование |

Загрузка через mlx_audio (скачивает с HuggingFace):

```bash
cd ~/shelf/qwen3-tts-apple-silicon
source .venv/bin/activate
python3 -c "
from mlx_audio.tts.utils import load_model
model = load_model('mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-8bit')
print('OK')
"
```

## run.sh — варианты запуска

```bash
# На экранном Mac — клиентская часть (VAD + STT)
python3 assistant.py --remote http://192.168.103.70:8642

# На безголовом Mac — серверная часть (LLM + TTS)
cd ~/shelf/qwen3-tts-apple-silicon
source .venv/bin/activate
python3 server.py  # FastAPI сервер
```

## Быстрый старт (если всё настроено)

```bash
# 1. На безголовом — запустить Ollama и Qwen3-TTS сервер
ssh admin@192.168.103.70 \
  "hermes-proxy exec 'cd ~/shelf/qwen3-tts-apple-silicon && source .venv/bin/activate && python3 server.py'"

# 2. На экранном — запустить ассистента
cd ~/Documents/local-siri && python3 assistant.py --remote http://192.168.103.70:8642
```

## Диагностика

```bash
# Проверить связь
ping -c 2 192.168.103.70

# Проверить Ollama на безголовом
curl http://192.168.103.70:11434/api/tags

# Проверить Qwen3-TTS сервер (health)
curl http://192.168.103.70:8642/health

# Проверить TTS генерацию (сохраняет WAV в /tmp/)
curl -X POST http://192.168.103.70:8642/tts \
  -H "Content-Type: application/json" \
  -d '{"text":"привет"}' \
  -o /tmp/tts-test.wav && afplay /tmp/tts-test.wav

## Параметры конфигурации (assistant.py)

| Параметр | Значение |
|----------|----------|
| LLM_URL | http://192.168.103.70:11434/v1/chat/completions |
| LLM_MODEL | qwen2.5:3b |
| TTS_SERVER | http://192.168.103.70:8642 |
| WHISPER_MODEL | mlx-community/whisper-base-mlx |
| VAD порог | 0.3 |
| TRIGGER_WORDS | ["прием"] |

## Удалённый TTS сервер (endpoint)

```python
POST /tts
Content-Type: application/json

{"text": "привет мир", "voice": "custom"}

-> 200 OK
Content-Type: audio/wav
(бинарные WAV данные, 24kHz, mono)
```

Сервер реализован в `templates/qwen3-tts-server.py` — FastAPI + mlx-audio.
Ленивая загрузка модели (при первом запросе), GC после каждой генерации.

**Запуск:**
```bash
cd ~/shelf/qwen3-tts-apple-silicon
source .venv/bin/activate
python3 /path/to/qwen3-tts-server.py --host 0.0.0.0 --port 8642
```

Слушает на всех интерфейсах — доступен с других Mac в локальной сети.

## Известные проблемы и фиксы

### mlx_audio не импортируется из .venv
Если `import mlx_audio` падает — переустановить:
```bash
cd ~/shelf/qwen3-tts-apple-silicon
source .venv/bin/activate
pip install mlx-audio
```

### Qwen3-TTS не скачивается из Китая
Использовать HF mirror или прокси:
```bash
export HF_ENDPOINT=https://hf-mirror.com
# или через SOCKS5 туннель (ALL_PROXY)
```

### macOS Sandbox блокирует доступ к OpenVox
Модели Qwen3-TTS в sandbox-контейнере OpenVox не читаются даже через sudo. Единственный способ — экспорт через само приложение или перекачка модели через MLX.

### Перегруз M1 Air 8GB
На экранном Mac остаётся только VAD + STT (~200MB RAM). Если что-то ещё запущено — проверять memory_pressure.

## Сеть между Mac (дополнительно)

see: skill `ship-wifi-iphone-sharing` для настройки интернета на безголовом через экранный Mac.
see: skill `headless-mac-static-ip` — статический IP безголового в WiFi корабля.

## История

- Май 2026: Распределённая архитектура. LLM + TTS уезжают на безголовый M1 Pro 32GB.
- Май 2026: Qwen3-TTS 1.7B MLX выбран как целевой TTS. ~/shelf/qwen3-tts-apple-silicon готов.
- Апрель-Май 2026: Итерации TTS — Piper -> MeloTTS -> Silero v4+v5 -> macOS say -> Qwen3-TTS.
- Март 2026: Первая версия — всё локально на M1 Air 8GB.
