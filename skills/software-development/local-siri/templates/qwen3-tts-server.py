#!/usr/bin/env python3
"""Qwen3-TTS FastAPI сервер для local-siri.

Запуск:
  cd ~/shelf/qwen3-tts-apple-silicon && source .venv/bin/activate
  python3 /path/to/qwen3-tts-server.py

Зависимости: mlx-audio, fastapi, uvicorn, pydantic

Эндпоинты:
  POST /tts  — {"text": "привет мир", "voice": "custom"} -> audio/wav
  GET  /health — {"status": "ok"}

Сервер слушает на 0.0.0.0:8642 — доступен всем в локальной сети.
"""

import os
import io
import gc
import json
import argparse
import warnings
import numpy as np
from pathlib import Path

warnings.filterwarnings("ignore")
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Qwen3-TTS Server")

# CORS — разрешить запросы с любого origin (для local-siri с другого Mac)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Модель грузится лениво при первом запросе
_model = None
_SAMPLE_RATE = 24000


class TTSRequest(BaseModel):
    text: str
    voice: str = "custom"  # custom, design, base


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool


def get_model():
    """Ленивая загрузка модели при первом запросе."""
    global _model
    if _model is not None:
        return _model
    print("[TTS] Loading Qwen3-TTS 1.7B CustomVoice...")
    from mlx_audio.tts.utils import load_model
    _model = load_model("mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-8bit")
    print("[TTS] Model loaded OK")
    return _model


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok",
        model_loaded=_model is not None,
    )


@app.post("/tts")
async def tts(req: TTSRequest):
    """Генерация речи из текста. Возвращает WAV."""
    if not req.text.strip():
        return Response(status_code=400, content=b'{"error":"empty text"}')

    print(f"[TTS] Generating: {req.text[:60]!r}")
    model = get_model()
    from mlx_audio.tts.generate import generate_audio

    audio = generate_audio(model, req.text)
    # audio — numpy array, float32

    # Конвертировать в WAV
    import soundfile as sf
    buf = io.BytesIO()
    sf.write(buf, audio, _SAMPLE_RATE, format="WAV")
    wav_data = buf.getvalue()

    # GC после каждой генерации — освободить память
    del audio
    gc.collect()

    return Response(
        content=wav_data,
        media_type="audio/wav",
        headers={
            "X-Sample-Rate": str(_SAMPLE_RATE),
            "X-Duration-Sec": f"{len(audio) / _SAMPLE_RATE:.2f}",
        },
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8642)
    parser.add_argument("--reload", action="store_true", help="auto-reload on code change")
    args = parser.parse_args()

    print(f"[TTS] Starting server on {args.host}:{args.port}")
    print(f"[TTS] Model: Qwen3-TTS-12Hz-1.7B-CustomVoice-8bit")
    print(f"[TTS] Model will load on first request")
    uvicorn.run(app, host=args.host, port=args.port, reload=args.reload)
