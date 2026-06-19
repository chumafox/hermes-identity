# История TTS в local-siri (май-июнь 2026)

## Хронология

| Этап | Действие | Результат |
|------|----------|-----------|
| 1 | Piper TTS (irina-medium, ~60MB) | ❌ "грустный" |
| 2 | MeloTTS | ❌ нет русского |
| 3 | Silero v4 TTS (xenia, 38MB) + ffmpeg pitch 0.85 | ✅ ~неделю |
| 4 | Silero → ffmpeg robot-эффекты | ❌ rejected |
| 5 | Qwen3-TTS-0.6B (ModelScope, ~2.4GB) | ❌ не докачан, отложен |
| 6 | **macOS say "Milena (Enhanced)"** ✅ | **ФИНАЛ — 0MB RAM** |
| 7 | **+ Немецкий: say "Anna"** | **мультиязык** |

## Piper TTS

**Модель**: ru_RU-irina-medium (женский) — голос грустный/неестественный
**Дополнительно**: ru_RU-denis-medium (мужской) тоже скачан
**Где лежит**: `~/Documents/local-siri/piper-voices/`
**Команды:**
```bash
echo "текст" | piper -m model.onnx -c model.json -f out.wav --length-scale 0.9 --noise-scale 0.8 --noise-w-scale 0.6
afplay out.wav
```
**Питфол**: URL на HuggingFace — `ru/ru_RU/...` (двойной `ru`). Одиночный путь → HTML-404.
**Проверка битой модели**: `file model.onnx` → "data", не "HTML document".

## MeloTTS

Только EN/FR/ES/JA/ZH/KR. Русский не поддерживается.

## Qwen3-TTS

**Модель**: Qwen3-TTS-12Hz-0.6B-Base (0.6B params, 10 языков включая русский)
**Установка**: `pip install -U qwen-tts modelscope`
**Размер**: ~1.7GB model + ~650MB speech_tokenizer = ~2.4GB
**RAM**: ~2-3GB на M1 — критично для 8GB
**Статус**: пакет установлен, загрузка отменена пользователем.

## Silero TTS v5 (подробно)

**Модель**: v4_ru (38.2MB, torch.hub, ~150MB RAM)
**Голос**: xenia (женский) ★★★★★
**Активация:**
```python
torch.hub.load('snakers4/silero-models', 'silero_tts', language='ru', speaker='v4_ru', trust_repo=True)
```
**Требуется**: `pip3 install omegaconf`
**Кэш**: `~/.cache/torch/hub/snakers4_silero-models_master/`
**Производительность**: синтез ~0.9с, загрузка ~73с (1-й раз)
**FFmpeg эффекты**: см. references/audio-effects.md
