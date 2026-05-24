# WanGP Setup Session Reference

## Setup Summary (macOS Apple Silicon M4 Pro)

**Date:** May 23, 2026

### Steps taken

1. Cloned https://github.com/deepbeepmeep/Wan2GP to ~/Downloads/Wan2GP
2. Installed Python 3.11 via brew
3. Created `venv` with `/opt/homebrew/bin/python3.11 -m venv venv`
4. Installed PyTorch (CPU index): `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu`
5. Installed requirements.txt — worked on first try (no network issues)
6. **Patched Gradio** in `<venv>/lib/python3.11/site-packages/gradio/blocks.py`:
   - Line ~2711: replaced `httpx.get(...startup-events...)` with `self.run_startup_events()`
   - Line ~2748: replaced `url_ok()` check with `pass`
7. Started server: `python -u wgp.py --listen --server-name 0.0.0.0 --server-port 7860`
   - Background process via terminal tool
   - Used `-u` for unbuffered output
   - Required redirecting stderr to stdout (`2>&1`) to capture Gradio errors
8. Connected from Open Generative AI app on the same machine
   - Entered `http://localhost:7860` in Wan2GP settings
   - Models appeared ("Server offline" message gone)
   - LTX Video said "Not enough VRAM" initially

### What went wrong

- **Gradio 5.x SSL check on macOS LibreSSL** — blocks startup with 503 on `startup-events`
- **First connection to Gradio UI took ~30-60 seconds** — Gradio compiles templates on first load. Subsequent loads are fast (~200ms).
- **`venv/bin/python wgp.py` hung with no output** without `-u` flag — buffered output made it appear dead.

### Environment

- MacBook Pro M4 Pro (16" 2024), 24GB RAM
- macOS 14.8.5
- Python 3.11 (brew), LibreSSL 2.8.3

### Lessons

- Always use `-u` (unbuffered output) for long-running Python server processes
- Gradio SSL patch is required on any macOS with LibreSSL 2.8.3 (Apple's default)
- Run from within the Wan2GP directory — `wgp.py` uses relative paths
