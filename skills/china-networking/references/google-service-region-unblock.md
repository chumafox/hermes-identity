# Unblocking Google Services by Account Region

When a Google service (e.g. Gemini) shows "not supported in your country" despite US IP and US Play Store settings.

## Root Cause

Google determines service availability by the **home region** of the Google Account, not by:
- IP address / geolocation
- Play Store country setting
- Timezone
- Browser language
- SOCS cookies

Home region is set when the account is created. In China, many accounts get associated with Vietnam, Russia, or China itself depending on the creation path.

## Diagnosis

1. **Check IP** — `curl -s https://ipinfo.io/json` shows country/city
2. **Check Play Store country** — `https://play.google.com/settings` → "Country and profiles"
3. **Check Google Terms country** — `https://policies.google.com/terms` shows "Country version: XX"
   - **Logged in**: shows your account's home region
   - **Not logged in**: shows region by IP
4. **Check Gemini directly** — `https://gemini.google.com/app` while logged in

## Fix: Country Association Form

1. Go to `https://policies.google.com/country-association-form`
2. Sign in with the affected account
3. Select the correct country (United States, Japan, Singapore — where the service is available)
4. Select state if applicable
5. Choose reason: **"I live here"** or **"I moved here in the past year"**
6. Submit — you'll get a confirmation email at the account's email address
7. Wait (minutes to hours) for Google to process
8. After confirmation email: log out and back into the service

## Notes

- **Family group** blocks Play Store country changes but does NOT block the country-association form
- Changing home region resets the Google company responsible for the account (e.g. Google Ireland → Google LLC)
- After the change, SOCS cookies and cached session may still show old region — clear cookies or use a fresh browser session
- Safari (without automation) works better for initial login after region change than Brave with CDP, because CDP automation sessions may interfere with Google auth flows

## API-Level Error vs Account-Level Error

Не путать два разных типа блокировки:

| Тип | Ошибка | Кто блокирует | Причина |
|-----|--------|---------------|---------|
| **Account region** | "Gemini not available in your country" | Веб-интерфейс (gemini.google.com) | Account home region не US |
| **API location** | `HTTP 400 FAILED_PRECONDITION: User location is not supported for the API use.` | Google Cloud API (`daily-cloudcode-pa.googleapis.com`, `generativelanguage.googleapis.com`) | Billing account / G1 Credits region |

### macOS: timeout command not available

macOS не имеет `timeout` (из GNU coreutils). Если нужно принудительно завершить зависший gcloud/agy:

```bash
# Установить coreutils (даст gtimeout)
brew install coreutils

# Или использовать perl:
perl -e 'alarm 15; exec @ARGV' gcloud beta billing accounts list

# Или python:
python3 -c "import subprocess,sys; subprocess.run(sys.argv[1:],timeout=15)"
```

## gcloud beta hangs (China firewall)

`gcloud components install beta` может зависнуть из-за GFW. Использовать REST API напрямую:

```bash
# Токен
TOKEN=$(gcloud auth print-access-token)

# Список billing accounts
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://cloudbilling.googleapis.com/v1/billingAccounts"

# Статус billing проекта
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://cloudbilling.googleapis.com/v1/projects/<PROJECT_ID>/billingInfo"
```

## API-Level Error Diagnostics

Ошибка `"User location is not supported for the API use."` с кодом `400 FAILED_PRECONDITION` приходит от Google Cloud API Gateway (сервер `ESF`). Это **не** блокировка по IP — запрос доходит до Google и валидируется.

**Типичные сценарии:**
- `agy` / `antigravity` CLI (Gemini Code Assist) — шлют запрос к `daily-cloudcode-pa.googleapis.com/v1internal:loadCodeAssist`
- Gemini API напрямую через `generativelanguage.googleapis.com`
- Google AI Studio через SDK

**Причины (по убыванию вероятности):**
1. Нет G1 Credits (Gemini Code Assist subscription) у Google Cloud проекта
2. Billing account привязан к региону China
3. API не включён в Google Cloud Console для проекта

**Что делать:**

```bash
# 1. Проверить проекты и billing
gcloud projects list
gcloud billing accounts list
gcloud billing projects list

# 2. Создать проект с US billing
gcloud projects create my-us-project
gcloud billing projects link my-us-project --billing-account=XXXXXX

# 3. Включить API
gcloud services enable cloudaicompanion.googleapis.com --project=my-us-project

# 4. Использовать этот проект
gcloud config set project my-us-project
gcloud auth application-default login
```

**Обходные пути, если billing недоступен:**
- Использовать API-ключ (Gemini API) вместо OAuth:
  ```bash
  GOOGLE_API_KEY="AIza..." agy --model "gemini-2.5-flash" -p "prompt"
  ```
- Использовать другого провайдера (OpenRouter, DeepSeek) через Hermes

## Test After Change

```bash
# Check Google Terms shows new country
curl -s https://policies.google.com/terms | grep -i "country version"

# Open in browser and check
https://gemini.google.com/app
```
