---
name: opencode
description: "Delegate coding to OpenCode CLI (features, PR review)."
version: 1.2.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Coding-Agent, OpenCode, Autonomous, Refactoring, Code-Review]
    related_skills: [claude-code, codex, hermes-agent]
---

# OpenCode CLI

Use [OpenCode](https://opencode.ai) as an autonomous coding worker orchestrated by Hermes terminal/process tools. OpenCode is a provider-agnostic, open-source AI coding agent with a TUI and CLI.

## When to Use

- User explicitly asks to use OpenCode
- You want an external coding agent to implement/refactor/review code
- You need long-running coding sessions with progress checks
- You want parallel task execution in isolated workdirs/worktrees

## Prerequisites

- OpenCode installed: `npm i -g opencode-ai@latest` or `brew install anomalyco/tap/opencode`
- Auth configured: `opencode auth login` or set provider env vars (OPENROUTER_API_KEY, etc.)
- Verify: `opencode auth list` should show at least one provider
- Git repository for code tasks (recommended)
- `pty=true` for interactive TUI sessions

## Binary Resolution (Important)

Shell environments may resolve different OpenCode binaries. If behavior differs between your terminal and Hermes, check:

```
terminal(command="which -a opencode")
terminal(command="opencode --version")
```

If needed, pin an explicit binary path:

```
terminal(command="$HOME/.opencode/bin/opencode run '...'", workdir="~/project", pty=true)
```

## Version Compatibility

| Feature | v0.0.55 (old) | v1.16.2+ (current) |
|---------|---------------|-------------------|
| One-shot | `opencode -p "prompt"` | `opencode run "prompt"` |
| Debug | `opencode -d` | `opencode debug` or `--print-logs` |
| Providers | N/A | `opencode providers list / login` |
| Agents | `agents.coder.model` in config | Configuration via `/connect` in TUI |
| JSON output | `-f json` | N/A (use `opencode run -f json`) |

**Если мигрируешь с 0.0.55 на 1.16.2:**
- Флаг `-p` больше не существует — используй `opencode run "prompt"`
- Флаг `-d` заменён на `opencode debug` или `--print-logs`
- Секция `agents` в opencode.json вызывает ошибку **"Unrecognized key: agents"** — удали её полностью
- Модель задаётся через `"model": "provider/model-id"` в opencode.json
- Провайдеры управляются через `opencode providers login` или `/connect` внутри TUI

## One-Shot Tasks

Use `opencode run "prompt"` for bounded, non-interactive tasks:

\`\`\`
terminal(command="opencode run 'Add retry logic to API calls and update tests'", workdir="~/project")
\`\`\`

Attach context files with `-f`:

\`\`\`
terminal(command="opencode run 'Review this config for security issues' -f config.yaml -f .env.example", workdir="~/project")
\`\`\`

JSON output format:

\`\`\`
terminal(command="opencode run 'Explain context in Go' -f json", workdir="~/project")
\`\`\`

**Note:** `opencode -p` (v0.0.55 syntax) does NOT work in v1.16.2+ — use `opencode run` instead.

## Interactive Sessions (Background)

For iterative work requiring multiple exchanges, start the TUI in background:

```
terminal(command="opencode", workdir="~/project", background=true, pty=true)
# Returns session_id

# Send a prompt
process(action="submit", session_id="<id>", data="Implement OAuth refresh flow and add tests")

# Monitor progress
process(action="poll", session_id="<id>")
process(action="log", session_id="<id>")

# Send follow-up input
process(action="submit", session_id="<id>", data="Now add error handling for token expiry")

# Exit cleanly — Ctrl+C
process(action="write", session_id="<id>", data="\x03")
# Or just kill the process
process(action="kill", session_id="<id>")
```

**Important:** Do NOT use `/exit` — it is not a valid OpenCode command and will open an agent selector dialog instead. Use Ctrl+C (`\x03`) or `process(action="kill")` to exit.

### TUI Keybindings

| Key | Action |
|-----|--------|
| `Enter` | Submit message (press twice if needed) |
| `Tab` | Switch between agents (build/plan) |
| `Ctrl+P` | Open command palette |
| `Ctrl+X L` | Switch session |
| `Ctrl+X M` | Switch model |
| `Ctrl+X N` | New session |
| `Ctrl+X E` | Open editor |
| `Ctrl+C` | Exit OpenCode |

### Resuming Sessions

After exiting, OpenCode prints a session ID. Resume with:

```
terminal(command="opencode -c", workdir="~/project", background=true, pty=true)  # Continue last session
terminal(command="opencode -s ses_abc123", workdir="~/project", background=true, pty=true)  # Specific session
```

## Common Flags

| Flag | Use | Version |
|------|-----|---------|
| `-p "prompt"` | One-shot execution and exit | v0.0.55 only |
| `run "prompt"` | One-shot execution and exit | v1.16.2+ |
| `--continue` / `-c` | Continue the last OpenCode session | all |
| `--session <id>` / `-s` | Continue a specific session | all |
| `--agent <name>` | Choose OpenCode agent (build or plan) | all |
| `--model provider/model` | Force specific model | all |
| `-f json` | Machine-readable output/events (one-shot) | all |
| `--file <path>` / `-f` | Attach file(s) to the message | all |
| `--thinking` | Show model thinking blocks | all |
| `--variant <level>` | Reasoning effort (high, max, minimal) | all |
| `--title <name>` | Name the session | all |
| `--attach <url>` | Connect to a running opencode server | all |
| `-d` / `--debug` | Debug logging to stderr | v0.0.55 |
| `--print-logs` | Print logs to stderr | v1.16.2+ |
| `-q` / `--quiet` | Hide spinner in non-interactive mode | all |

## Procedure

1. Verify tool readiness:
   - `terminal(command="opencode --version")`
   - Check env vars: OPENAI_API_KEY, ANTHROPIC_API_KEY, OPENROUTER_API_KEY, or GITHUB_TOKEN
2. For bounded tasks, use `opencode -p '...'` (no pty needed).
3. For iterative tasks, start `opencode` with `background=true, pty=true`.
4. Monitor long tasks with `process(action="poll"|"log")`.
5. If OpenCode asks for input, respond via `process(action="submit", ...)`.
6. Exit with `process(action="write", data="\x03")` or `process(action="kill")`.
7. Summarize file changes, test results, and next steps back to user.

## PR Review Workflow

OpenCode has a built-in PR command:

```
terminal(command="opencode pr 42", workdir="~/project", pty=true)
```

Or review in a temporary clone for isolation:

```
terminal(command="REVIEW=$(mktemp -d) && git clone https://github.com/user/repo.git $REVIEW && cd $REVIEW && opencode -p 'Review this PR vs main. Report bugs, security risks, test gaps, and style issues.' -f $(git diff origin/main --name-only | head -20 | tr '\n' ' ')", pty=true)
```

## Parallel Work Pattern

Use separate workdirs/worktrees to avoid collisions:

```
terminal(command="opencode -p 'Fix issue #101 and commit'", workdir="/tmp/issue-101", background=true, pty=true)
terminal(command="opencode -p 'Add parser regression tests and commit'", workdir="/tmp/issue-102", background=true, pty=true)
process(action="list")
```

## Session & Cost Management

List past sessions:

```
terminal(command="opencode session list")
```

Check token usage and costs:

```
terminal(command="opencode stats")
terminal(command="opencode stats --days 7 --models anthropic/claude-sonnet-4")
```

## Pitfalls

- Interactive `opencode` (TUI) sessions require `pty=true`. The `-p` one-shot does NOT need pty.
- `/exit` is NOT a valid command — it opens an agent selector. Use Ctrl+C to exit the TUI.
- PATH mismatch can select the wrong OpenCode binary/model config.
- If OpenCode appears stuck, inspect logs before killing:
  - `process(action="log", session_id="<id>")`
- Avoid sharing one working directory across parallel OpenCode sessions.
- Enter may need to be pressed twice to submit in the TUI (once to finalize text, once to send).
- **TUI не открывается, хотя `which opencode` показывает 1.16.2**: проверь `which -a opencode` — может быть старый бинарник 0.0.55 в `~/.opencode/bin/`. Решение: `rm ~/.opencode/bin/opencode` или используй полный путь `/opt/homebrew/bin/opencode`.
- **`opencode run` зависает с `session.prompt loop` в логах**: ждёт ответа от модели. Проверь `opencode providers list` и модель в конфиге. Запусти `opencode --print-logs run 'test'` для диагностики.
- **"agent coder not found" (v0.0.55)**: the `agents.coder` block is missing from `~/.opencode.json`. Run `opencode` interactively once to generate the config, or add it manually (see Config Troubleshooting below). **v1.16.2+ fix**: удалить секцию `agents` из конфига — она не поддерживается.
- **"Unrecognized key: agents" (v1.16.2+)**: opencode 1.16.2 не поддерживает ключ `agents` в конфиге. Удали его из `~/.config/opencode/opencode.json` и `~/.opencode.json`.
- **"no valid provider available"**: the provider's apiKey is empty/missing, or no supported env var (OPENAI_API_KEY, ANTHROPIC_API_KEY, OPENROUTER_API_KEY, GROQ_API_KEY, GITHUB_TOKEN) is set. Проверь через `opencode providers list`.
- **No custom base URL support**: opencode hardcodes API endpoints per provider (api.openai.com, api.anthropic.com, etc.). OpenAI-compatible proxies like Bailian/DashScope, Azure custom endpoints, or local LLM servers CANNOT be used as providers. If the user needs an OpenAI-compatible proxy, opencode is the wrong tool — use Hermes directly or a different CLI agent.
- opencode does NOT work without internet access to the provider's actual API endpoint. China users without proxy will get connection failures.

## Config Troubleshooting

Config lives at `~/.opencode.json` (project) and `~/.config/opencode/opencode.json` (global). If `opencode` was run interactively at least once, it auto-generates `~/.opencode.json` with default structure.

Minimal working `~/.opencode.json`:

```json
{
  "data": {},
  "providers": {
    "openai": {
      "apiKey": "sk-...",
      "disabled": false
    }
  },
  "agents": {
    "coder": {
      "model": "openai/gpt-4.1",
      "maxTokens": 0,
      "reasoningEffort": ""
    }
  },
  "tui": { "theme": "opencode" },
  "shell": {}
}
```

Supported provider names: `openai`, `anthropic`, `gemini`, `groq`, `openrouter`, `azure`, `copilot`, `vertex`, `bedrock`.

Diagnose with: `opencode -d -p "hello"` — the `-d` flag enables debug logging to stderr.

## Verification

Smoke test:

```
terminal(command="opencode -p 'Respond with exactly: OPENCODE_SMOKE_OK'")
```

Success criteria:
- Output includes `OPENCODE_SMOKE_OK`
- Command exits without provider/model errors
- For code tasks: expected files changed and tests pass

## Rules

1. Prefer `opencode -p` for one-shot automation — it's simpler and doesn't need pty.
2. Use interactive background mode only when iteration is needed.
3. Always scope OpenCode sessions to a single repo/workdir.
4. For long tasks, provide progress updates from `process` logs.
5. Report concrete outcomes (files changed, tests, remaining risks).
6. Exit interactive sessions with Ctrl+C or kill, never `/exit`.
7. If user has no OPENAI/ANTHROPIC/OPENROUTER API key, opencode won't work — suggest Hermes directly or check if they have a supported provider key set.
