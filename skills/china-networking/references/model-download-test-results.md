Модель 8B (16GB+ RAM) — не запускать на M1 Air 8GB. Требует Python 3.10, 30-40GB на диске, GPU 24GB VRAM.
На pro (M1 Pro 32GB) теоретически работает на CPU, но очень медленно.

ModelScope — единственная китайская платформа, стабильно работающая через Python SDK.
Установка: `pip3 install --break-system-packages modelscope` (PEP 668).
Скачивание: `snapshot_download("Qwen/Qwen2.5-1.5B-Instruct", local_dir="./model")`.

Сравнение методов (тест на pro, июнь 2026):
- Прямой HF (через TUN): ✅ работает (~1MB/s для gpt2)
- hf-mirror.com (curl): ✅ доступен
- hf-mirror.com (huggingface_hub Python): ❌ SSL ошибка (Distant resource not found)
- ModelScope (Python SDK): ✅ работает (~1MB/s для Qwen2.5)
