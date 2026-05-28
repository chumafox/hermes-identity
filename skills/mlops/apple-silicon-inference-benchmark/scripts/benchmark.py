#!/usr/bin/env python3
"""
Бенчмарк LLM для M1 Air 8GB.
Тестирует модели через Ollama API.
Автовыгрузка между тестами. Мониторинг памяти до/после.
"""

import json, time, subprocess, sys, os, re
from datetime import datetime

OLLAMA_URL = "http://localhost:11434/api/generate"
MIN_FREE_MB = 100

PROMPTS = {
    "short": "Напиши одно предложение про искусственный интеллект.",
    "medium": ("Объясни разницу между машинным обучением и глубоким обучением. "
               "Приведи примеры. Ответь кратко."),
}

OLLAMA_MODELS = [
    ("qwen2.5:3b", "Дефолт"),
    ("qwen2.5-coder:3b", "Кодер"),
]

def get_free_mb():
    try:
        r = subprocess.run(["memory_pressure"], capture_output=True, text=True, timeout=5)
        for line in r.stdout.split("\n"):
            m = re.search(r"Pages free:\s+(\d+)", line)
            if m:
                return int(m.group(1)) * 16384 / 1024 / 1024
    except: pass
    return 0

def ollama_unload_all():
    try:
        r = subprocess.run(["ollama", "ps"], capture_output=True, text=True, timeout=5)
        for line in r.stdout.strip().split("\n")[1:]:
            parts = line.split()
            if parts:
                subprocess.run(["ollama", "stop", parts[0]], capture_output=True, timeout=10)
                time.sleep(1)
    except: pass

def test_ollama(model, tag, prompt_key):
    prompt = PROMPTS[prompt_key]
    free_before = get_free_mb()
    if free_before < MIN_FREE_MB:
        return {"model": model, "status": "skipped", "free_mb": round(free_before, 0)}
    
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False,
                          "options": {"num_predict": 128, "temperature": 0}})
    try:
        r = subprocess.run(["curl", "-s", "-X", "POST", OLLAMA_URL, "-d", payload],
                           capture_output=True, text=True, timeout=120)
        elapsed = time.time()  # approximate
        data = json.loads(r.stdout)
    except: return {"model": model, "status": "error"}
    
    if "error" in data:
        return {"model": model, "status": "error", "error": data["error"]}
    
    tokens = data.get("eval_count", 0)
    dur_ns = data.get("eval_duration", 0)
    tok_s = tokens / (dur_ns / 1e9) if dur_ns > 0 else 0
    free_after = get_free_mb()
    ollama_unload_all()
    time.sleep(2)
    
    return {"model": model, "tag": tag, "status": "ok",
            "total_tokens": tokens, "tok_s": round(tok_s, 1),
            "time_sec": round(dur_ns / 1e9, 2),
            "prompt_tokens": data.get("prompt_eval_count", 0),
            "prompt_ms": round(data.get("prompt_eval_duration", 0) / 1e6, 1),
            "free_before": round(free_before, 0),
            "free_after": round(free_after, 0),
            "free_change": round(free_before - free_after, 0),
            "response": data.get("response", "")[:80]}

def main():
    print(f"benchmark {datetime.now():%Y-%m-%d %H:%M}")
    print(f"RAM: {get_free_mb():.0f} MB free / 8192 MB")
    
    ollama_unload_all()
    time.sleep(2)
    results = []
    
    for model, tag in OLLAMA_MODELS:
        for pk in ["short", "medium"]:
            r = test_ollama(model, tag, pk)
            results.append(r)
            status = r.get("status")
            if status == "ok":
                print(f"  {tag}/{model:20s} {r['tok_s']:>5.1f} tok/s  {abs(r['free_change']):>4.0f}MB  {r['time_sec']:>5.2f}s")
            else:
                print(f"  {tag}/{model:20s}  {status}")
            time.sleep(3)
    
    # Save
    out = os.path.join(os.path.dirname(__file__), "..", "references", "benchmark_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump({"timestamp": datetime.now().isoformat(),
                   "system": "MacBookAir10,1 (M1, 8GB)",
                   "results": results}, f, indent=2, ensure_ascii=False)
    print(f"\nsaved: {out}")

if __name__ == "__main__":
    main()
