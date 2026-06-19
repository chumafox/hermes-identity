# Model Cleanup on M1 Air 8GB

## When
User asks to clean up heavy local models or identify which models the M1 Air can't run.

## Rule on M1 Air 8GB
- **Не грузить LLM >4B параметров** — memory pressure >80%, swap убивает производительность
- Q4_K_M models: parameter count × ~0.7GB per 1B params ≈ RAM usage
- MLX 4-bit: more efficient, but same rule applies (>4B → too heavy)
- Gemma4 models with 131K context: extra RAM for KV cache, even heavier

## Steps to Identify Heavy Models

### Ollama
```bash
# List all models
ollama list

# Check actual params (critical!)
ollama show <model-name>
# Look for "parameters" line: 7.5B, 4.6B, 3.1B etc.

# Skip cloud-only models (tagged :cloud) — they take 0 local space
```

### LM Studio
Check model directories under `~/.lmstudio/models/`:
```bash
ls ~/.lmstudio/models/<publisher>/
# Look for .gguf or .safetensors files
# For safetensors: check config.json for num_parameters or hidden_size
```

### Special cases
- **Empty model dirs**: Some publishers have dirs with only a Modelfile (360B) and no actual weights — delete freely
- **Cloud-only models** (`:cloud` tag in ollama list): SIZE shows `-`, take zero disk space, skip them
- **MLX safetensors**: if only model.safetensors exists + tokenizer files, the actual size is the safetensors file

## Moving Heavy Models Out

### Ollama workflow
1. Check model: `ollama show <name>` — get parameter count and blob digest
2. Read manifest: `cat ~/.ollama/models/manifests/registry.ollama.ai/library/<name>/latest` — extract SHA256 from `layers[0].digest`
3. Create target: `mkdir -p ~/models-too-heavy/ollama`
4. Copy manifest: `cp -r ~/.ollama/models/manifests/registry.ollama.ai/library/<name> ~/models-too-heavy/ollama/<name>-manifest`
5. Move model blob: `mv ~/.ollama/models/blobs/sha256-<digest> ~/models-too-heavy/ollama/<name>-model.bin`
6. Move ALL related blobs (config, system, params, template, license) — check ALL entries in manifest `layers[]` and the `config.digest`
7. Remove from registry: `ollama rm <name>`
8. Write README.md in `~/models-too-heavy/` with restoration sha256 mapping

### LM Studio workflow
Simply move the model directory out:
```bash
mv ~/.lmstudio/models/<publisher>/<model> ~/models-too-heavy/lmstudio/
```

### Check remaining space
```bash
du -sh ~/models-too-heavy/
```

## Safe Models on M1 Air 8GB
- Ollama: `qwen2.5:3b` (3.1B, 1.9 GB) ✓
- LM Studio MLX: `Phi-4-mini 4bit` (3.8B, 2.0 GB in MLX) ✓
- Any model ≤3.8B params in 4-bit quantization

## Unsafe Models (move out)
| Model | Params | Size | Reason |
|-------|--------|------|--------|
| german-tutor (Gemma4) | 7.5B | 4.8 GB | >4B, 131K context |
| gemma4-e2b-test | 4.6B | 3.1 GB | >4B, 131K context |
| Any 7B+ model | 7B+ | >4 GB | Will swap |

## Restoration
Files in `~/models-too-heavy/` can be moved back. Each model directory should have a README with exact sha256 restore commands:
```bash
# Example restore for german-tutor:
cp ~/models-too-heavy/ollama/german-tutor-model.bin \
   ~/.ollama/models/blobs/sha256-b3acbebbf64ab2f905dc23ec0cbb67a18c18f52779c3f7bdf1f40d69947fec1c
cp -r ~/models-too-heavy/ollama/german-tutor-manifest \
   ~/.ollama/models/manifests/registry.ollama.ai/library/german-tutor
# ... plus all supporting blobs
ollama pull german-tutor  # re-register (will skip existing blobs)
```
