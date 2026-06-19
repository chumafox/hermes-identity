# HuggingFace Model Download from China — tested on pro

## Environment

- pro: M1 Pro 32GB, China (Yangtze River cruise ship), Shadowrocket TUN (utun4)
- Internet via ZTE 4G modem (Type-C), through Shadowrocket VPN node
- pip3 install with `--break-system-packages` (PEP 668 enforced)

## Test Results

| Method | Result | Notes |
|--------|--------|-------|
| Direct HF (huggingface_hub, no proxy) | ✅ Работает ~1MB/s | Через TUN Shadowrocket, медленно но стабильно |
| hf-mirror.com + huggingface_hub (HF_ENDPOINT) | ❌ SSL Error | "Distant resource does not seem to be on huggingface.co" |
| hf-mirror.com + curl direct | ✅ Работает | Для отдельных файлов |
| ModelScope (modelscope SDK) | ✅ Работает ~1MB/s | Тоже через TUN, та же скорость |
| SOCKS5 127.0.0.1:1082 | ❌ Не работает | Shadowrocket порт не отвечает |

## Вывод

На pro через Shadowrocket TUN прямой доступ к HF работает, хотя и медленно. hf-mirror.com через Python SDK ломается с SSL-ошибкой. ModelScope SDK работает но не быстрее прямого HF.

Для больших моделей — скачивать на dispo (где internet_pro даёт стабильный интернет) и rsync на pro.

## ModelScope установка

```bash
pip3 install --break-system-packages modelscope
```

Использование:
```python
from modelscope.hub.snapshot_download import snapshot_download
snapshot_download("Qwen/Qwen2.5-1.5B-Instruct", local_dir="./model")
```
