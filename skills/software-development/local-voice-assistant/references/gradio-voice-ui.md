# Gradio Voice UI — Complete Example

Minimal voice assistant UI with Gradio.

## Installation

```bash
pip install gradio
```

## Basic Voice Assistant

```python
import gradio as gr
import subprocess
import requests
import os

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:3b"

def stt(audio_path):
    """Speech-to-text via mlx-whisper"""
    if not audio_path:
        return ""
    # mlx_whisper outputs txt to CWD
    out_file = audio_path.rsplit(".", 1)[0] + ".txt"
    subprocess.run([
        "mlx_whisper", audio_path,
        "--model", "mlx-community/whisper-large-v3-turbo",
        "--language", "ru",
        "--output-format", "txt"
    ], check=True)
    with open(out_file) as f:
        return f.read().strip()

def llm(text):
    """LLM via Ollama"""
    if not text:
        return ""
    r = requests.post(OLLAMA_URL, json={
        "model": MODEL,
        "prompt": f"Ты полезный ассистент. Пользователь сказал: {text}\nОтветь кратко:",
        "stream": False
    })
    return r.json()["response"]

def tts(text):
    """Text-to-speech via system say (macOS)"""
    if not text:
        return None
    subprocess.run(["say", "-v", "Anna", text])  # German voice
    return None

with gr.Blocks(title="Local Siri") as demo:
    gr.Markdown("# 🎙️ Local Voice Assistant")
    
    with gr.Row():
        audio_input = gr.Audio(sources=["microphone"], type="filepath", label="Говори")
        btn = gr.Button("Отправить", variant="primary")
    
    transcript = gr.Textbox(label="Распознано", lines=2)
    response = gr.Textbox(label="Ответ", lines=3)
    
    btn.click(stt, inputs=audio_input, outputs=transcript).then(
        llm, inputs=transcript, outputs=response
    ).then(
        tts, inputs=response, outputs=None
    )

demo.launch(server_name="0.0.0.0", server_port=7860)
```

## Run

```bash
python3 voice_assistant.py
# Open http://localhost:7860
```

## Advanced — With Piper TTS

```python
def tts_piper(text, lang="de"):
    """TTS via Piper"""
    model = f"{lang}_{lang}-thorsten-medium.onnx"
    subprocess.run([
        "piper", "--model", model,
        "--output_file", "/tmp/response.wav"
    ], input=text.encode())
    return "/tmp/response.wav"
```
