# Скачивание моделей в Китае

Приоритет способов (от лучшего к запасному):

## 1. ModelScope Python SDK

```bash
pip install modelscope
python3 -c "from modelscope import snapshot_download; snapshot_download('Qwen/Qwen2.5-7B-Instruct')"
```

## 2. hfd.sh (HF → зеркало прокси)

```bash
wget https://hf-mirror.com/hfd/hfd.sh
chmod +x hfd.sh
./hfd.sh meta-llama/Llama-2-7b --tool aria2c -x 4
```

## 3. HF_ENDPOINT (huggingface-cli через зеркало)

```bash
export HF_ENDPOINT=https://hf-mirror.com
huggingface-cli download Qwen/Qwen2.5-7B-Instruct
```

## 4. aria2c (многопоточная загрузка)

Установлен: `/opt/homebrew/bin/aria2c`

```bash
aria2c -x 4 -s 4 <url>
```

## 5. Через прокси (inpro/SSH туннель)

Когда зеркала нет — использовать SOCKS5 :1080 или HTTP bridge :8888.
