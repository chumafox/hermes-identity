# Скачивание AI-моделей из Китая

Проверенные методы для macOS (M1 Pro, Shadowrocket TUN).

## Сводка тестов (июнь 2026, Китай, через Shadowrocket TUN)

| Метод | Результат | Скорость |
|-------|-----------|----------|
| Прямой HF (huggingface.co) | ✅ Работает | ~1 МБ/с (через TUN) |
| HF через SOCKS5 1082 | ❌ SOCKS5 не работает | — |
| hf-mirror.com (curl/wget) | ✅ Доступен | ~0.9s latency |
| hf-mirror.com (huggingface_hub) | ❌ SSL ошибка: "Distant resource does not seem to be on huggingface.co" | — |
| ModelScope (modelscope.cn) | ✅ Работает | ~0.5-1.8 МБ/с |

## PEP 668 — установка Python пакетов

На macOS с Homebrew Python (`python@3.14`) `pip install` и `uv pip install --system` блокируются:

```
error: The interpreter at /opt/homebrew/... is externally managed
```

**Workarounds:**

1. **Venv** (рекомендуется):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install modelscope huggingface_hub
   ```

2. **`--break-system-packages`** (для быстрых тестов):
   ```bash
   pip3 install --break-system-packages modelscope
   ```

3. **Homebrew** (если пакет доступен):
   ```bash
   brew install huggingface-cli  # проверьте наличие
   ```

## Метод 1: Прямой HuggingFace (работает через TUN)

Если Shadowrocket/V2rayU в TUN-режиме включён, HF доступен напрямую. Прокси не нужен.

```bash
# Убедись что прокси не задан:
unset http_proxy https_proxy all_proxy ALL_PROXY
unset HF_ENDPOINT

# Скачивание:
pip3 install --break-system-packages huggingface_hub
python3 -c "
from huggingface_hub import snapshot_download
snapshot_download('gpt2', local_dir='./model')
"
```

**Важно:** проверь что нет локального прокси в `.git/config`:
```bash
cd ~/.hermes/hermes-agent && git config --local --list | grep proxy
# Если есть — сбрось:
git config --local --unset http.proxy
git config --local --unset https.proxy
```

## Метод 2: ModelScope (альтернатива HF из Китая)

ModelScope (modelscope.cn) — платформа Alibaba. Работает напрямую из Китая.

**Установка:**
```bash
pip3 install --break-system-packages modelscope
```

**Скачивание:**
```bash
# Через Python:
python3 -c "
from modelscope.hub.snapshot_download import snapshot_download
snapshot_download('Qwen/Qwen2.5-1.5B-Instruct', local_dir='./model')
"

# Или через готовый скрипт ~/bin/ms-dl:
ms-dl Qwen/Qwen2.5-1.5B-Instruct
ms-dl deepseek-ai/DeepSeek-R1-Distill-Qwen-7B ./models/ds
```

**Проверенные модели на ModelScope:**
- Qwen (все версии)
- DeepSeek
- ChatGLM
- Baichuan
- Llama (китайские копии)

## Метод 3: wget/curl через hf-mirror.com (отдельные файлы)

```bash
# Один файл:
curl -LO "https://hf-mirror.com/bert-base-uncased/resolve/main/config.json"

# Список файлов модели:
curl -s "https://hf-mirror.com/api/models/Qwen/Qwen2.5-7B/tree/main"
```

**Важно:** `huggingface_hub` через `HF_ENDPOINT=https://hf-mirror.com` может выдавать SSL ошибку (`Distant resource does not seem to be on huggingface.co`). Это проблема библиотеки, не зеркала. Используй curl/wget для отдельных файлов или прямой HF.

## Скрипт ms-dl (установлен на pro)

Скрипт `~/bin/ms-dl` автоматически устанавливает `modelscope` если нет, и скачивает модель:

```bash
ms-dl Qwen/Qwen2.5-7B-Instruct
```

Если нет в PATH — добавь в `~/.zshrc`:
```bash
export PATH="$HOME/bin:$PATH"
```
