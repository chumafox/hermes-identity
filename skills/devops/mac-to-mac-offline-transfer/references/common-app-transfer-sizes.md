# Common Mac App Sizes & Binary Paths for Offline Transfer

Use this to decide *what* to transfer and *how*.

| App | Path on Source | Size | Transfer Size | Notes |
|-----|---------------|------|---------------|-------|
| Zettlr | GitHub DMG | 154 MB | 154 MB | `vibe_3.0.19_aarch64.dmg` |
| OpenVox | `/Applications/OpenVox – Local Voice AI.app` | 726 MB | 488 MB (tar.gz) | GUI app |
| Cursor CLI | `/Applications/Cursor.app/Contents/Resources/app/bin/cursor` | 11 MB (bin) | 232 MB (full app) | CLI is bash wrapper, needs full app |
| Claude Code | `~/.local/share/claude/versions/X.X.X` | 380 MB | 113 MB (tar.gz) | Standalone Bun binary, headless OK |
| Goose (Block CLI) | `/Applications/Goose.app/Contents/Resources/bin/goosed` | 217 MB | 217 MB | Rust binary, headless OK. NOT `brew install goose` (that's a DB tool) |
| Node.js | brew formula or tarball | 73 MB | 73 MB (tar.gz) | From nodejs.org or /usr/local |
| Cursor IDE (GUI) | `/Applications/Cursor.app` | 756 MB | 232 MB (tar.gz) | Electron, GUI only |
| LM Studio | DMG from lmstudio.ai | 527 MB | 527 MB | Has `lms` CLI inside |
| Ollama | DMG from ollama.com | 484 MB | 157 MB (tar.gz) | CLI works headless |
| Hermes Agent (self) | `~/.hermes/hermes-agent/` (code + venv) | ~1.3 GB | 224 MB (tar.gz) | Needs portable Python + venv |

## Headless Compatibility

| App | Works Headless? | Notes |
|-----|-----------------|-------|
| Claude Code | Yes | Bun binary, no GPU needed |
| LM Studio / lms | Yes | CLI works, GUI optional |
| Ollama | Yes | CLI-only |
| Goose (goosed) | Yes | Rust server binary |
| Cursor CLI | Yes | tunnel/SSH mode |
| Vibe | Yes | Has `--server` HTTP API |
| Hermes Agent | Yes | Python CLI |
| Zettlr | No | Electron GUI |
| OpenVox | No | GUI app |
| Goose.app (cask) | No | Electron GUI — crash on headless |
| Cursor.app | No | Electron GUI |
