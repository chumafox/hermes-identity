# Shelf (~/shelf/)

Пользователь кладёт репозитории "на полку" в `~/shelf/` для будущего использования.

## Процедура

```bash
mkdir -p ~/shelf
cd ~/shelf && git clone --filter=tree:0 --depth=1 --single-branch <URL>
```

## Известное содержимое

### Проекты на полке (~/shelf/)

| Репозиторий | ★ | Описание | Путь |
|------------|---|----------|------|
| TTS-WebUI | 3.1k | Gradio+React WebUI для множества TTS моделей (SeamlessM4T, Bark, Piper, F5-TTS, CosyVoice и др.) | ~/shelf/seamlessm4t-projects/TTS-WebUI |
| NeuroSandboxWebUI | 106 | Локальная WebUI для нейросетей (текст, изображение, аудио) | ~/shelf/seamlessm4t-projects/NeuroSandboxWebUI |
| SeamlessM4TApp | 57 | Flask API + Flutter мобильное приложение для SeamlessM4T (speech-to-speech перевод) | ~/shelf/seamlessm4t-projects/SeamlessM4TApp |
| Fast-SeamlessM4T-ONNX | 43 | ONNX-оптимизированный SeamlessM4T | ~/shelf/seamlessm4t-projects/Fast-SeamlessM4T-ONNX |
| SeamlessM4t-Translator | 13 | Простой переводчик на SeamlessM4T | ~/shelf/seamlessm4t-projects/SeamlessM4t-Translator |
| seamlessly | 10 | Colab ноутбук для SeamlessM4T | ~/shelf/seamlessm4t-projects/seamlessly |
| AutoTranslate | 9 | JS модуль авто-перевода на SeamlessM4T | ~/shelf/seamlessm4t-projects/AutoTranslate |
| SeamlessM4T-finetune | 4 | Файнтюнинг SeamlessM4T | ~/shelf/seamlessm4t-projects/SeamlessM4T-finetune |
| SeamlessM4Tv2-API | 4 | Docker API для SeamlessM4Tv2 | ~/shelf/seamlessm4t-projects/SeamlessM4Tv2-API |
| qwenwishper | 20 | macOS menu bar dictation + live translation (Whisper + Qwen) | ~/shelf/qwenwishper |
| open-webui | 62k | Self-hosted LLM web interface (Ollama + OpenAI API) | ~/shelf/open-webui |

### Особые упоминания

- **open-webui (62k★)** — самый популярный self-hosted интерфейс для LLM. Поддерживает встроенный STT (Whisper) и TTS (ElevenLabs/Azure/OpenAI). Не требует отдельной установки моделей для голоса — всё через API. Но для полностью локального сценария (LM Studio + mlx-whisper + Qwen3 TTS) лучше собрать свой Gradio UI.
- **SeamlessM4TApp** — содержит Flask API для speech-to-speech перевода. Проблема: требует fairseq2 (не ставится на Python 3.12/macOS 15). Альтернатива: transformers + MPS (см. seamless-m4t-install.md).
- **TTS-WebUI** — самый полный набор TTS/STT моделей в одном проекте. ~10.7GB базовая установка. Каждая модель 2-8GB. Overkill для одной задачи.

## Память

После клонирования — сохранить ссылку в memory tool, чтобы при следующем разговоре знать что есть на полке.
