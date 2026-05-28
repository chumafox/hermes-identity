# LM Studio on Headless Mac

## Installation Path
- App: `/Applications/LM Studio.app/`
- CLI: `/usr/local/bin/lms` → `/Applications/LM Studio.app/Contents/Resources/app/.webpack/lms`

## Installing from DMG
```bash
# Mount
hdiutil attach /path/to/LM-Studio.dmg -mountpoint /tmp/lm_mount
# Copy app
cp -R "/tmp/lm_mount/LM Studio.app" /Applications/
# Symlink CLI (lms binary inside .webpack folder)
sudo ln -sf "/Applications/LM Studio.app/Contents/Resources/app/.webpack/lms" /usr/local/bin/lms
# Add to PATH for non-interactive SSH
echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.zshenv
# Cleanup
hdiutil detach /tmp/lm_mount
rm /path/to/LM-Studio.dmg
```

## Loading a Model
```bash
# List available models
lms get           # search/status

# Load a model
lms load gemma-4-e4b-it-mlx

# Check status
lms ps
```

## Starting API Server
```bash
lms server start
# → Server on port 1234 (OpenAI-compatible)
```

## Verifying
```bash
curl http://localhost:1234/v1/models
curl http://localhost:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"gemma-4-e4b-it-mlx","messages":[{"role":"user","content":"hi"}],"max_tokens":10}'
```

## Hermes Integration
See `references/hermes-provider-quirks.md` for LM Studio provider configuration.

**⚠️ Context Window Warning:** Most small local models have context windows below Hermes' 64K minimum. Either:
1. Override with `hermes config set model.context_length 4096`
2. Load a model with ≥64K context (Qwen2.5-7B, Mistral 7B, Llama 3 8B)

## SSH Tunnel Access
When LM Studio only listens on localhost but you need remote access:
```bash
# From screen Mac — forward port
ssh -L 1234:localhost:1234 -N admin@headless-mac &
# Now localhost:1234 talks to LM Studio on headless Mac
```
