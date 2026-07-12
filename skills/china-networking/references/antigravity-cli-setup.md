# Antigravity CLI — Gemini Code Assist Migration

Google deprecated `gemini` CLI (Gemini Code Assist for individuals) and migrated to **Antigravity** suite.

## Detection: gemini CLI is dead

```
$ gemini ...
Error authenticating: IneligibleTierError: This client is no longer supported
for Gemini Code Assist for individuals. To continue using Gemini, please migrate
to the Antigravity suite of products: https://antigravity.google
```

## Available Antigravity Products (macOS)

| Product | Path | Bundle ID | Type |
|---------|------|-----------|------|
| Antigravity.app | `/Applications/Antigravity.app` | `com.google.antigravity` | Desktop client (Gemini Code Assist) |
| Antigravity IDE.app | `/Applications/Antigravity IDE.app` | — | VS Code fork for Gemini |
| antigravity CLI | `/opt/homebrew/Caskroom/antigravity-cli/<version>/antigravity` | — | Go-based terminal CLI |

Data dir: `~/.gemini/antigravity/` and `~/.gemini/antigravity-cli/`

## CLI Differences: agy vs antigravity

CLI | `--model` flag | Config location | Notes
----|--------------|-----------------|------
`agy` | ✅ `--model "gemini-2.5-flash"` | `~/.gemini/antigravity-cli/settings.json` | Старый бинарник, всё ещё работает |
`antigravity` | ❌ **not supported** | `~/.gemini/antigravity/antigravity_state.pbtxt` | Новый бинарник, модель из `settings.json` |

`antigravity` определяет модель через `last_selected_agent_model` в `antigravity_state.pbtxt`. Флаг `--model` вызовет ошибку `"flags provided but not defined: -model"`.

У `agy` есть флаг `--model` и `-p` (print mode):
```bash
agy --model "gemini-2.5-flash" -p "prompt"
```

У `antigravity` нет `--model`, нужно задавать модель в настройках:
```bash
antigravity --print "prompt"
```

## Common auth flow

Both agy and antigravity use **gcloud ADC** (Application Default Credentials) and/or Keychain tokens.

```bash
# Check active account
gcloud auth list
gcloud config list account

# Login with a specific account
gcloud auth login jenyanovakpro@gmail.com --no-launch-browser
# → opens URL in browser, paste verification code back

# Switch to new account
gcloud config set account jenyanovakpro@gmail.com
```

## API endpoint

Both CLIs call:
```
POST https://daily-cloudcode-pa.googleapis.com/v1internal:loadCodeAssist
```

Requires **G1 Credits** (Gemini Code Assist subscription) in the Google Cloud project. If missing:
```
FAILED_PRECONDITION (code 400): User location is not supported for the API use.
```

See `references/google-service-region-unblock.md` for diagnostics.

## Path setup

antigravity CLI is installed via Homebrew Cask:
```bash
brew install --cask antigravity-cli
```

Binary lives at: `/opt/homebrew/Caskroom/antigravity-cli/<version>/antigravity`
Needs symlink to be in PATH:
```bash
ln -sf /opt/homebrew/Caskroom/antigravity-cli/*/antigravity /opt/homebrew/bin/antigravity
```

## Model routing: Gemini fail, Anthropic works

**Ключевое наблюдение:** Antigravity/agy используют **разные бэкенды** для разных провайдеров моделей.

```
Antigravity/agy CLI
├── Gemini модели → daily-cloudcode-pa.googleapis.com  → ❌ требует G1/US billing
└── Anthropic/Claude модели → api.anthropic.com          → ✅ работает без special setup
```

Это **не** проблема аккаунта. Если бы Google блокировал аккаунт — все модели были бы недоступны. Проблема в том, что Gemini API (`daily-cloudcode-pa.googleapis.com`) проверяет регион billing на своей стороне, а Anthropic API не проверяет.

**Что работает сразу (без billing):**
```bash
agy --model "claude-sonnet-4" -p "hello"
agy --model "claude-opus-4" -p "hello"
```

**Что требует US billing/G1 Credits:**
```bash
agy --model "gemini-2.5-flash" -p "hello"
# → FAILED_PRECONDITION: User location is not supported for the API use.
```

Ошибка приходит на **этапе аутентифицированного запроса** — неаутентифицированный curl к тому же endpoint получает 401 (UNAUTHENTICATED), а аутентифицированный запрос от CLI — 400 (FAILED_PRECONDITION). Google пропускает запрос после OAuth проверки, но перед выполнением проверяет billing region.

## Proxy quirks

Both are **Go binaries** — Go does **not** support SOCKS5 via env vars.  
See `references/go-cli-proxy.md` and `references/proxy-leak-verification.md` (Go CLI section).
