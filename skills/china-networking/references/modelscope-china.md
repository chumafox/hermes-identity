# ModelScope — скачивание моделей из Китая

ModelScope (modelscope.cn) — платформа AI-моделей от Alibaba. Работает из Китая напрямую, без прокси/VPN.

## Установка

На macOS Homebrew Python (PEP 668):
```bash
pip3 install --break-system-packages modelscope
```

Через venv:
```bash
python3 -m venv .venv && source .venv/bin/activate && pip install modelscope
```

## Скачивание

```python
from modelscope.hub.snapshot_download import snapshot_download
path = snapshot_download("Qwen/Qwen2.5-1.5B-Instruct", local_dir="./model")
```

## Скорость

Через Shadowrocket TUN: ~700KB-1.8MB/s. Конфиги за секунды, веса ~2.88GB за 40-50 мин.

## Проверенные модели

- Qwen (все версии)
- DeepSeek
- ChatGLM
- Baichuan
- Llama (китайские копии)

## Важно

`huggingface_hub` через `HF_ENDPOINT=https://hf-mirror.com` может падать с `FileMetadataError: Distant resource does not seem to be on huggingface.co` из-за SSL-несовместимости с Python на macOS. Использовать прямой HF (через TUN) или ModelScope.
