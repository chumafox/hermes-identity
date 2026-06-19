# Session Audit: 28 May 2026 — Code Review & Fixes

Внешний ассистент провёл аудит assistant.py и нашёл 5 дефектов. Все исправлены.

## Defects Found & Fixed

### D1: Loss of text case on trigger word
- **Когда:** `_handle_speech()`, stripping trigger word
- **Почему:** `text = text_lower[:-len(tw)].strip()` перезаписывает оригинальный текст нижним регистром
- **Фикс:** использовать `rfind` на lowercased тексте, срез по оригинальному тексту
- **Коммит:** 28.05.2026, patch в строки 318-328

### D2: Global state mutation via sys.modules
- **Когда:** main(), строки 388-392
- **Почему:** `sys.modules[__name__].WHISPER_MODEL = args.model` — антипаттерн
- **Фикс:** передавать конфиг через конструктор VoiceAssistant()
- **Коммит:** 28.05.2026

### D3: PortAudio callback blocks on Whisper
- **Когда:** `_callback()` вызывает `_handle_speech()` синхронно
- **Почему:** Whisper ~0.5-1.5с блокирует аудио-поток → Input overflow
- **Фикс:** callback кладёт в `queue.Queue`, основной цикл забирает
- **Коммит:** 28.05.2026

### D4: Temp file leak on Ctrl+C
- **Когда:** TTS создаёт WAV в /tmp, удаление только при нормальном завершении
- **Фикс:** глобальный `_TEMP_FILES` + `atexit` + SIGINT/SIGTERM handler
- **Коммит:** 28.05.2026

### D5: Outdated macOS privacy path
- **Когда:** сообщение об ошибке микрофона
- **Почему:** macOS 15+ изменил путь в настройках
- **Фикс:** `Privacy & Security → Microphone` (вместо `Privacy → Microphone`)
- **Коммит:** 28.05.2026

## Cторонние TTS tested this session

| Engine | Verdict | Reason |
|--------|---------|--------|
| Piper (irina-medium) | ❌ Rejected | Voice sad/unnatural |
| Piper (denis-medium) | ⏬ Downloaded, not tested | — |
| Silero v5 (xenia/baya/kseniya) | ❌ Rejected raw | Didn't like natural voices |
| Silero v5 + pitch 0.85 | ✅ FINAL | Low female voice, accepted |
| MeloTTS | ❌ No Russian | EN/FR/ES/JA/ZH/KR only |
| Fish Speech | ❌ Deps too heavy | lightning, wandb, gradio |
| Qwen3-TTS-0.6B | ❌ Abandoned by user | 2.4GB download, RAM risk |
| edge-tts | ⏭️ Skipped | User only wants local |
