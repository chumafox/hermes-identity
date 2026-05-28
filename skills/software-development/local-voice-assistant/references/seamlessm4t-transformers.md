# SeamlessM4T via Transformers

Using Meta's SeamlessM4T through HuggingFace transformers (no fairseq2 needed).

## Installation

```bash
pip install transformers torch torchaudio sentencepiece
```

## Speech-to-Speech Translation

```python
from transformers import AutoProcessor, SeamlessM4TModel
import torchaudio
import torch

# Load model (first time downloads ~5GB)
model = SeamlessM4TModel.from_pretrained("facebook/seamless-m4t-large")
processor = AutoProcessor.from_pretrained("facebook/seamless-m4t-large")

# Use MPS on Apple Silicon
device = "mps" if torch.backends.mps.is_available() else "cpu"
model = model.to(device)

# Load audio
audio, sr = torchaudio.load("input_russian.wav")
if sr != 16000:
    audio = torchaudio.transforms.Resample(sr, 16000)(audio)

# Process
audio_inputs = processor(audios=audio.squeeze().numpy(), return_tensors="pt", sampling_rate=16000)
audio_inputs = {k: v.to(device) for k, v in audio_inputs.items()}

# Russian → German speech
output_tokens = model.generate(
    **audio_inputs,
    tgt_lang="deu",
    generate_speech=True,
    speaker_id=0  # male voice
)

# Save output
output_audio = output_tokens[0].cpu().numpy()
torchaudio.save("output_german.wav", torch.tensor(output_audio).unsqueeze(0), 16000)
```

## Text-to-Speech

```python
text = "Hallo, wie geht es dir?"
text_inputs = processor(text=text, src_lang="deu", return_tensors="pt")
output_tokens = model.generate(**text_inputs, tgt_lang="deu", generate_speech=True)
```

## Supported Languages

| Code | Language |
|------|----------|
| rus | Russian |
| deu | German |
| eng | English |
| cmn | Chinese (Mandarin) |
| fra | French |
| spa | Spanish |
| ... | 100+ total |

## Pitfalls

- **Model size:** large = ~5GB, medium = ~2.5GB. Ensure enough disk space.
- **MPS memory:** large model may OOM on 8GB Macs. Use medium or CPU.
- **First run:** downloads model from HuggingFace. May need token for gated models.
- **fairseq2 not needed:** transformers approach avoids fairseq2 compilation issues.
