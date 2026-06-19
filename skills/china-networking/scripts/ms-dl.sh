#!/bin/bash
# ms-dl — ModelScope Download
# Быстрое скачивание AI-моделей из Китая через modelscope.cn
#
# Использование:
#   ms-dl Qwen/Qwen2.5-7B-Instruct              → в ./models/Qwen-Qwen2.5-7B-Instruct
#   ms-dl Qwen/Qwen2.5-7B-Instruct ./my-model    → в ./my-model
#
# Установка: скопировать в ~/bin/ms-dl, chmod +x

MODEL_ID="${1:?Ошибка: укажи ID модели, например Qwen/Qwen2.5-7B-Instruct}"
DEST="${2:-./models/$(echo "$MODEL_ID" | tr '/' '-')}"

echo "→ ModelScope: $MODEL_ID"
echo "→ Куда: $DEST"
echo ""

# Автоустановка modelscope если нет
if ! python3 -c "import modelscope" 2>/dev/null; then
    echo "→ Устанавливаю modelscope..."
    pip3 install --break-system-packages -q modelscope 2>/dev/null || {
        python3 -m venv /tmp/ms-venv
        source /tmp/ms-venv/bin/activate
        pip install -q modelscope
        deactivate
    }
fi

mkdir -p "$(dirname "$DEST")"

time python3 -c "
from modelscope.hub.snapshot_download import snapshot_download
snapshot_download('$MODEL_ID', local_dir='$DEST', resume_download=True)
print()
print('✓ Готово')
" 2>&1

echo ""
echo "Размер: $(du -sh "$DEST" 2>/dev/null | cut -f1)"
