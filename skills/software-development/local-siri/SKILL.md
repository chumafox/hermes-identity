---
name: local-siri
description: "Локальный голосовой ассистент (русский) на M1 Air 8GB. Стек: VAD → mlx-whisper → LLM (Ollama) → TTS в поиске (Piper/Silero/MeloTTS отклонены). Код: ~/Documents/local-siri/"
version: 7
author: hermes-agent
---

# local-siri — Голосовой ассистент

## Быстрый старт
```bash
cd ~/Documents/local-siri
python3 assistant.py  # полный режим: микрофон → голосовой ответ
./run.sh --no-web     # запуск (без web UI, чтобы не было конфликта портов)
./run.sh --no-tts     # только текст (экономит ресурсы)
./run.sh --check      # диагностика компонентов
```

Ollama должен быть запущен: `ollama ps` — увидеть qwen2.5:3b.

## Архитектура (TTS — в поиске)
```
Микрофон → Silero VAD ONNX (CPU) → mlx-whisper (GPU)
                                        ↓
                                   Ollama :11434
                                   qwen2.5:3b
                                        ↓
                              TTS: ПОИСК — Piper/Silero/MeloTTS отклонены
                              Очередь: edge-tts → Fish Speech
```

## Конфиг (assistant.py)
| Параметр | Значение | Примечание |
|----------|----------|------------|
| LLM_URL | http://localhost:11434/v1/chat/completions | Ollama API |
| LLM_MODEL | qwen2.5:3b | |
| WHISPER_MODEL | mlx-community/whisper-base-mlx | 137MB, предустановлен |
| TTS | Silero TTS v5 (v4_ru) | torch.hub, ~38MB, CPU |

## Whisper модели в кэше (~/.cache/huggingface/hub/)
| Модель | Размер | Рекомендация |
|--------|--------|--------------|
| whisper-tiny-mlx | 71 MB | Быстрый, низкая точность |
| **whisper-base-mlx** | **137 MB** | **Дефолт — баланс** |
| whisper-small-mlx | ❌ не скачан | Скачивать 460MB из Китая — долго |
| whisper-medium-mlx | 1.4 GB | Точнее, но тяжелее |
| whisper-large-v3-turbo | 1.5 GB | Макс точность, для 8GB норм |

Все кроме small уже скачаны. Переключение: поменять `WHISPER_MODEL` в assistant.py.

## Silero TTS v5

### Установка и загрузка

```python
import torch

# Первая загрузка — скачивает модель ~38MB в ~/.cache/torch/hub/
model, example_text = torch.hub.load(
    repo_or_dir='snakers4/silero-models',
    model='silero_tts',
    language='ru',
    speaker='v4_ru',
    trust_repo=True,
)
```

Требуется `omegaconf`: `pip3 install omegaconf`

### Доступные русские голоса

| Имя | Пол | Качество |
|-----|-----|----------|
| **xenia** | женский | ★★★★★ |
| **baya** | женский | ★★★★ |
| **kseniya** | женский | ★★★★ |
| aidar | мужской | ★★★★ |
| eugene | мужской | ★★★ |

### Параметры синтеза

```python
audio = model.apply_tts(
    text="Привет, мир",
    speaker='xenia',        # голос
    sample_rate=48000,      # 48000 или 24000
)
```

### Воспроизведение

```bash
# Сохранить и сыграть
python3 -c "import soundfile as sf; sf.write('/tmp/test.wav', audio.numpy(), 48000)"
afplay /tmp/test.wav
```

### Производительность на M1 Air 8GB
- **Загрузка модели**: ~73 сек (первый раз, сеть медленная)
- **Синтез**: ~0.9 сек на фразу (~3 сек аудио)
- **RAM**: ~150 MB (CPU, не использует MPS/GPU)
- **Размер модели**: ~38 MB (кэш torch.hub)

### Важно
- Первая загрузка идёт с GitHub + HuggingFace — может быть медленно из Китая
- Модель кэшируется в `~/.cache/torch/hub/snakers4_silero-models_master/`
- Веса скачиваются отдельно в `~/.cache/torch/hub/checkpoints/`
- torch.hub просит подтверждение — нужен `trust_repo=True`

## Текущий статус TTS (актуально на май 2026)

TTS в assistant.py сейчас на **Piper** (последняя правка), но пользователь хочет другой. Идёт поиск. Ниже — что попробовано.

## Piper TTS (ОТКЛОНЁН)

**Модель**: ru_RU-irina-medium (женский, ~60MB)  
**Дополнительно**: ru_RU-denis-medium (мужской, ~60MB) тоже скачан  
**Результат**: голос звучит неестественно/грустно — пользователь отказался  
**Где лежит**: `~/Documents/local-siri/piper-voices/`  
**Установка**: `pip3 install piper-tts` (глобально, Python 3.12)  

Полезные команды:
```bash
# Тест
echo "текст" | piper -m model.onnx -c model.json -f output.wav --length-scale 0.9 --noise-scale 0.8 --noise-w-scale 0.6
afplay output.wav
```

**Питфол**: URL на HuggingFace — `ru/ru_RU/...` (двойной `ru`). Одиночный `ru_RU/...` возвращает HTML-страницу 404.  
**Проверка битой модели**: `file model.onnx` — должно быть "data", не "HTML document".

## Silero TTS v5 (ОТКЛОНЁН)

**Модель**: v4_ru (38.2MB, torch.hub)  
**Установка**: 
```bash
pip3 install omegaconf
```
**Загрузка через torch.hub**:
```python
import torch
model, _ = torch.hub.load('snakers4/silero-models', 'silero_tts',
    language='ru', speaker='v4_ru', trust_repo=True)
```
**Русские голоса**: xenia (жен), baya (жен), kseniya (жен), aidar (муж), eugene (муж)  
**Результат**: пользователю не понравились — звучат неестественно  
**Производительность**: синтез ~0.9 сек на фразу, ~150 MB RAM (CPU), модель кэшируется в `~/.cache/torch/hub/`  
**Важно**:
- torch.hub требует `trust_repo=True` (иначе запрашивает интерактивное подтверждение)
- Можно обойти: `torch.hub._validate_not_a_forked_repo = lambda a,b,c: True`
- Первая загрузка — скачивает модель с GitHub + HuggingFace (может быть медленно)
- `omegaconf` обязателен (без него: `No module named 'omegaconf'`)

## MeloTTS (НЕ ПОДДЕРЖИВАЕТ РУССКИЙ)

MeloTTS (myshell-ai/MeloTTS) поддерживает только EN/FR/ES/JA/ZH/KR. Русского нет.  
Установка требует MeCab (японский токенизатор):
```bash
brew install mecab mecab-ipadic
pip3 install git+https://github.com/myshell-ai/MeloTTS.git
```
Не тратить время на попытки запустить русский.

## Что дальше

Очередь на проверку:
1. **edge-tts** (Microsoft Edge cloud TTS) — отличные русские голоса (Svetlana), простейшая установка
2. **Fish Speech** — есть русский, но тяжёлые зависимости + медленная сеть
3. **macOS `say`** — встроенный, запасной вариант

## Бенчмарк M1 Air 8GB
Подробная таблица: `references/benchmark.md`

Сводка:
- **qwen2.5:3b через Ollama**: 27 tok/s — оптимально
- qwen2.5:3b через LM Studio: 23 tok/s (LM Studio внутри llama.cpp, не mlx-lm)
- Vikhr-1.5B через LM Studio: 18 tok/s (лучший русский, но медленнее)
- QVikhr-3-4B через Ollama: 20 tok/s (жрёт 3.4GB GPU — риск для 8GB)
- mlx-lm напрямую: ~10-11 tok/s — медленнее llama.cpp в 2.5x на M1 Air

## Известные ошибки и фиксы

### mlx-whisper 0.4.3 — load_models стал модулем
```python
# Было (0.3.x):
mlx_whisper.load_models(model_name)

# Стало (0.4.x):
from mlx_whisper.load_models import load_model
load_model(model_name)
```

### onnxruntime не установлен
Silero VAD с `onnx=True` требует:
```bash
pip3 install onnxruntime
```

### Python 3.12 — SyntaxError с global
Когда переменная используется в default-аргументе функции, `global` в той же функции даёт SyntaxError.
Фикс: использовать `sys.modules[__name__]` вместо `global`.

### VADIterator API изменился
```python
# Было:
self.iterator = self.model.get_iterator(threshold=0.5, ...)

# Стало:
from silero_vad import VADIterator
self.iterator = VADIterator(model, threshold=0.5, ...)
# reset():
self.iterator.reset_states()  # вместо создания нового итератора
```

### run.sh — переход с LM Studio на Ollama
Проверка в run.sh: заменить `lsof -i :1234` на `curl -sf http://localhost:11434/api/tags`.

### log() не поддерживал end=" "
Фикс: `def log(msg="", **kwargs): print(f"[{ts}] {msg}", flush=True, **kwargs)`

### Silero TTS — torch.hub просит подтверждение
torch.hub требует интерактивного ввода. Фикс перед загрузкой:
```python
torch.hub._validate_not_a_forked_repo = lambda a,b,c: True
torch.hub._check_repo_is_trusted = lambda *args, **kwargs: True
```
Или передать `trust_repo=True` в torch.hub.load().

### Silero TTS — ModuleNotFoundError: omegaconf
```bash
pip3 install omegaconf
```
Ошибка: `No module named 'omegaconf'` при загрузке silero_tts через torch.hub.

### Piper не установлен (если всё же нужно)
```bash
pip3 install piper-tts
```

### Piper — битая модель (HTML вместо ONNX)
Путь на HuggingFace — `ru/ru_RU/...` (двойной ru). Одиночный `ru_RU/...` возвращает HTML-страницу 404.
Проверка: `file piper-voices/ru_RU-*.onnx` — должно быть "data", не "HTML document".

### Перегруз M1 Air 8GB
- Не запускать >1 модели в одном бэкенде
- Проверять `memory_pressure` перед запуском (минимум 300MB свободно)
- Пауза 3-5 сек между тестами разных моделей
- Выгружать: `ollama stop <model>`
- Если мак выключился — слишком много моделей одновременно

## Сеть
Пользователь в Китае, HK eSIM + Shadowrocket VPN — скорость от 89 B/s до 5 MB/s в зависимости от маршрута и времени суток. Всегда проверять скорость тестовым файлом перед скачиванием.
