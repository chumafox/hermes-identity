# Скачивание AI-моделей из Китая

Проверено на pro (M1 Pro, China, Shadowrocket TUN).

## Сводка методов

| Метод | Статус | Скорость | Комментарий |
|-------|--------|----------|-------------|
| Direct HF (через TUN) | ✅ Работает | ~1-2 MB/s | Идёт через Shadowrocket utun4 |
| huggingface_hub + HF_ENDPOINT=mirror | ❌ SSL ошибка | — | "Distant resource not on huggingface.co" |
| curl/wget с hf-mirror.com | ✅ Файлы доступны | ~медленно | Через TUN |
| **ModelScope (modelscope.cn)** | **✅ Лучший** | **~0.3-1.8 MB/s** | **Китайский хостинг, стабилен** |

## ModelScope (рекомендуемый)

Установка:
```bash
pip3 install --break-system-packages modelscope
```

Скачивание:
```python
from modelscope.hub.snapshot_download import snapshot_download
snapshot_download("Qwen/Qwen2.5-1.5B-Instruct", local_dir="./model")
```

Или скриптом `ms-dl` (доступен в `scripts/ms-dl.sh` этого скилла, скопировать в ~/bin/):
```bash
ms-dl Qwen/Qwen2.5-1.5B-Instruct
ms-dl deepseek-ai/DeepSeek-R1-Distill-Qwen-7B ./models/deepseek
```

## Прямой HuggingFace (через TUN/прокси)

Работает если TUN активен (Shadowrocket, V2rayU):
```bash
unset HF_ENDPOINT
python3 -c "
from huggingface_hub import snapshot_download
snapshot_download('gpt2', local_dir='./model')
"
```

## hf-mirror.com — ограниченно

curl/wget для отдельных файлов — работает.
```bash
curl -LO "https://hf-mirror.com/bert-base-uncased/resolve/main/config.json"
```

huggingface_hub Python SDK через HF_ENDPOINT — **НЕ РАБОТАЕТ** на этой машине:
- Ошибка: "Distant resource does not seem to be on huggingface.co"
- Причина: SSL/TLS несовместимость между библиотекой и зеркалом

## Установка Python-пакетов (PEP 668)

На этой машине (Homebrew Python 3.14) `pip install` без venv запрещён:
```bash
# Пробить защиту:
pip3 install --break-system-packages <package>

# Или через venv:
python3 -m venv .venv && source .venv/bin/activate && pip install <package>

# uv тоже не работает с --system:
uv pip install --system <package>  # → ошибка
```
