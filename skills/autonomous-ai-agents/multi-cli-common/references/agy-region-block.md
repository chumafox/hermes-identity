# Agy (Antigravity CLI) — Region Block Diagnostics

## Симптом

```
FAILED_PRECONDITION (code 400): User location is not supported for the API use.
```

agy аутентифицируется (OAuth, keyring), но API `daily-cloudcode-pa.googleapis.com` отвечает 400.

## Причина

agy (бывший Gemini CLI) использует **Google Cloud Code Assist API** (`cloudcode-pa.googleapis.com`), а не публичный Gemini API. Этот API:

- Проверяет регион не только по IP, но и по OAuth-аккаунту / billing-проекту
- Не поддерживается в ряде стран, включая Китай
- Может блокировать датацентровые IP (Datacamp, Hetzner и т.д.) даже если страна формально разрешена

## Диагностика

### 1. Проверить логи agy CLI

```bash
cat ~/.gemini/antigravity-cli/log/*.log | grep -i "FAILED_PRECONDITION\|location\|region\|not supported"
```

### 2. Проверить аутентификацию

```bash
# Токен в keyring
cat ~/.gemini/antigravity-cli/settings.json
# OAuth токен
cat ~/.gemini/antigravity/antigravity-oauth-token
# Аккаунт gcloud
gcloud auth list
```

Логи покажут: `OAuth: authenticated successfully as email@example.com`

### 3. Проверить доступность API

```bash
curl -sI "https://daily-cloudcode-pa.googleapis.com" -o /dev/null -w "%{http_code} %{time_total}s\n"
# 404 = API существует (404 от Google, а не таймаут)
# таймаут/0 = блокировка на уровне сети
```

### 4. Проверить IP выхода

```bash
curl -s https://ipinfo.io/json
```

### 5. Проверить, что именно блокирует

- **Google.com доступен (200), но Cloud Code API 400** → регион/аккаунт блок, не сеть
- **Google.com недоступен** → проблема прокси/VPN

## Решения

### A. Сменить exit location прокси на США

Google Cloud Code Assist официально поддерживается в US. Швейцария, Германия, Нидерланды — могут не работать.

### B. API key mode (если появится)

На данный момент agy **не поддерживает API ключи** — только OAuth через gcloud. Если в будущем добавят — можно будет использовать Gemini API напрямую без региональных ограничений.

### C. Использовать другой инструмент

Если регион не меняется — agy не заработает. Альтернативы:
- Claude Code (`claude`)
- OpenCode (`opencode`)
- Hermes Agent (текущий)

## Структура конфигов agy

| Путь | Назначение |
|------|-----------|
| `~/.gemini/antigravity-cli/` | CLI данные (conversations, brain, log) |
| `~/.gemini/antigravity-cli/settings.json` | Модель, trustedWorkspaces |
| `~/.gemini/antigravity/` | IDE данные (Electron-приложение) |
| `~/.gemini/config/` | Общие конфиги (MCP, plugins) |
| `~/Library/Application Support/Antigravity/` | Electron storage (Cookies, Local Storage) |

## Примечание

Проблема НЕ в прокси/сети — Google доступен. Проблема в политике Google Cloud Code Assist, который блокирует регионы на уровне API, а не сети.
