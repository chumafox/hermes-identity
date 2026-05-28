# SeamlessM4T Installation from China

Meta's SeamlessM4T is NOT on PyPI (`pip install seamless-communication` → "no matching distribution"). 

## Attempted Approaches

### 1. fairseq2 (original Meta stack) — FAILS

```bash
pip install fairseq2  # → compilation failure on modern macOS
```
fairseq2 0.2.0 is too old for Python 3.12 / macOS 15. Needs build tools that may not be available.

### 2. Meta's official seamless_communication repo — FAILS (network)

```bash
pip install git+https://github.com/facebookresearch/seamless_communication.git
# → timeout / RPC failed from China
```

### 3. transformers + PyTorch (works, but model download may fail)

```bash
# In a fresh venv (Python 3.12 compatible):
python3 -m venv venv_seamless
source venv_seamless/bin/activate
pip install transformers torch torchaudio sentencepiece
```

Then load model in Python:
```python
from transformers import AutoProcessor, SeamlessM4TModel
import torch

device = "mps" if torch.backends.mps.is_available() else "cpu"
processor = AutoProcessor.from_pretrained("facebook/seamless-m4t-v2-large")
model = SeamlessM4TModel.from_pretrained("facebook/seamless-m4t-v2-large").to(device)
```

## Pitfalls

- **Model size:** `facebook/seamless-m4t-v2-large` is ~5GB. From China, HuggingFace may time out.
  - Workaround: download on HK Mac, scp over cable: `scp -r ~/.cache/huggingface/hub/models--facebook--seamless-m4t-v2-large admin@192.168.2.2:~/.cache/huggingface/hub/`
- **HF_TOKEN warning:** `"You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN"` — set `export HF_TOKEN=hf_...` for faster downloads.
- **Separate venv required:** transformers conflicts with mlx-whisper's older dependencies. Always create a dedicated venv.
- **MPS (Apple Silicon):** Works on `mps` device for inference, but model may be slightly slower than on CUDA. Acceptable for batch processing.
- **SeamlessM4T v1 vs v2:** v2 requires a HuggingFace token AND is in a private repo (`meta-private/M4Tv2`). Use `facebook/seamless-m4t-v2-large` (public) on HF instead.
