# Shared CLI Agent Context

## Communication
- Язык: русский (пользователь предпочитает русский)
- Стиль: кратко, технично, без лишнего
- Terminal-friendly: plain text, без markdown где возможно

## Environment
- macOS (M1 Air 8GB — не грузить LLM >4B локально)
- Location: China (PRC) — Google/YouTube/X заблокированы без VPN
- Proxy: V2rayU (utun4)
- Primary browser: Brave (CDP порт 9222)
- HF зеркало: hf-mirror.com

## Project Layout
- Активные проекты: ~/projects/active/
- Архив: ~/projects/archived/
- Shelved репозитории: ~/shelf/

## Conventions
- Python: use `uv` + venv, NOT pip directly
- Git: commit messages in English
- Secrets in code = BLOCKER. Use env vars
- AGENTS.md rules have priority over generic instructions

## CLI Tools Available
- Hermes Agent (primary)
- Claude Code (`claude`)
- OpenCode (`opencode`)
- Cursor CLI (`cursor-agent`)
