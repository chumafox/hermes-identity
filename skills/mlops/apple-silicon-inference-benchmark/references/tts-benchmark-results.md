# TTS (Text-to-Speech) Benchmark Results

## Model: Qwen3-TTS 0.6B Base 4bit (MLX)

Tested via `mlx-audio` on both M1 Pro 32GB and M1 Air 8GB.

### Methodology

Benchmark script: `qwen3_tts_benchmark.py` (from Blaizzy/mlx-audio).
Metrics:
- **TTFB** — Time to First Audio Byte (ms)
- **RTF** — Real-Time Factor (audio_duration / generation_time); >1.0 = faster than realtime
- **TPS** — Tokens per second
- **Peak memory** — system-level wired+active during generation

### M1 Pro 32GB (pro)

| Prompt | TTFB(ms) | InterChunk | TPS | RTF | Memory(GB) |
|--------|----------|------------|-----|-----|-----------|
| short | 172.9 | 126.6 | 28.2 | 2.25x | 2.24 |
| medium | 151.2 | 130.8 | 29.8 | 2.38x | 2.24 |
| long | 158.6 | 131.6 | 30.1 | 2.41x | 2.29 |

### M1 Air 8GB (display Mac)

| Metric | Cold (1st gen) | Warm (2nd gen) | Long phrase |
|--------|---------------|----------------|-------------|
| Generation time | 5.00-6.97s | 3.07-4.39s | 10.24s |
| Est RTF | ~0.9x | ~1.5x | ~0.9x |
| Pages wired | peak ~2598MB | ~2393MB | — |

### Memory Analysis (M1 Air 8GB)

```
State        | Pages free | Pages active | Pages wired
-------------|-----------|--------------|-------------
Idle         | 1782MB    | 1305MB       | 1365MB
After load   | 62MB      | 1619MB       | 1585MB
During gen   | 217MB     | 1254MB       | 2598MB
```

- **Active delta after load**: ~314MB (model in active RAM)
- **Wired delta peak during gen**: +1013MB (audio buffer + compute)
- **Free pages drop**: from 1782MB → 62MB after load (file cache), recovers to ~500MB during gen

### M1 Air Bottleneck

- **Memory**: ~300MB active + ~1GB wired peak is workable on 8GB (~4GB free for OS + other apps)
- **Speed**: M1 Air is ~1.3-1.5x slower than M1 Pro for same TTS model (3s vs 2.4s for short phrase)
- **RTF** on M1 Air: warm ~1.5x (faster than realtime), cold ~0.9x (just under realtime)

### Key Takeaways

1. **0.6B 4bit fits on 8GB** — ~314MB active RAM, ~2.6GB wired peak during generation. Leaves ~4GB for OS + apps.
2. **Warm vs cold matters**: first generation is ~2x slower (model needs to settle in Metal cache)
3. **4bit quantization has minimal quality loss**: WER 3.47% (4bit) vs 3.66% (8bit) per published benchmarks
4. **Edge TTS (online) uses 0MB RAM** — better default if internet is available
5. **For translation use case**: ~3s warm generation on M1 Air is acceptable, but Edge TTS is instant

### Command to reproduce

```bash
# On M1 Pro 32GB with mlx-audio installed:
python3 qwen3_tts_benchmark.py \
  --model mlx-community/Qwen3-TTS-12Hz-0.6B-Base-4bit

# Custom benchmark (memory tracking):
python3 -c "
from mlx_audio.tts.utils import load
import subprocess, time

model = load('/path/to/model')
def mem(label):
    r = subprocess.run(['memory_pressure'], capture_output=True, text=True)
    for l in r.stdout.split('\n'):
        for k in ['Pages free','Pages active','Pages wired down']:
            if k in l:
                v = int(l.split(':')[-1].strip())*16384//(1024*1024)
                print(f'  [{label}] {k}: {v}MB')

mem('idle')
for result in model.generate(text='Test phrase', voice='Chelsie', stream=True):
    if result.audio is not None: pass
mem('after gen')
"
```

### Model download workflow (China)

1. Download on pro (HK VPN via Shadowrocket): `huggingface-cli download mlx-community/Qwen3-TTS-12Hz-0.6B-Base-4bit`
2. Copy to Air via rsync over SSH
3. Verify: `find ~/.cache/huggingface/hub/models--mlx-community--Qwen3-TTS-12Hz-0.6B-Base-4bit -name '*.safetensors' -ls`
