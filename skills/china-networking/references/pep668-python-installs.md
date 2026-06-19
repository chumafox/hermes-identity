# PEP 668: Python installs on Homebrew-managed Python (macOS)

## Проблема

Homebrew Python 3.14+ помечен как `externally managed` (PEP 668). `pip install` и `uv pip install --system` блокируются:

```
error: The interpreter ... is externally managed
```

## Решения

### 1. `pip3 install --break-system-packages` (проще всего)

```bash
pip3 install --break-system-packages modelscope
```

### 2. Virtual environment (рекомендуется для проектов)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install modelscope
```

### 3. `uv` без --system

```bash
uv venv
uv pip install modelscope
```

### 4. Homebrew формула (если доступна)

```bash
brew install hf-hub  # не всегда есть
```

## Какие пакеты чаще всего нужны из Китая

- `modelscope` — скачивание моделей
- `huggingface_hub` — huggingface-cli
- `chromadb` — векторные БД
- `sentence-transformers` — эмбеддинги
