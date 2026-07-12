# Agy (Antigravity CLI) — Region Block Diagnostics

## Симптомы

### A. Region block

```
FAILED_PRECONDITION (code 400): User location is not supported for the API use.
```

agy аутентифицируется (OAuth, keyring), но API `daily-cloudcode-pa.googleapis.com` отвечает 400.

### B. HTTP_PROXY pollution (Go-специфично)

```
proxyconnect tcp: dial tcp 127.0.0.1:1083: connect: connection refused
```
или
```
proxyconnect tcp: dial tcp 192.168.103.70:8888: connect: no route to host
```

agy — Go-приложение, уважает `HTTP_PROXY`/`HTTPS_PROXY`. Если в окружении висит адрес несуществующего прокси, все запросы падают с `connection refused` (или `no route to host`), маскируя регион-блок.

**Hermes-gotcha: `source ~/.zshrc` — яд.** В одном `terminal()` вызове выполнение `source ~/.zshrc; proxy_on` оставляет `HTTP_PROXY`/`HTTPS_PROXY` во ВСЕХ последующих terminal() вызовах этой сессии. Если `.zshrc` содержит конфигурацию с неактивным прокси-адресом (например, `192.168.103.70:8888` — безголовый Mac), все последующие `terminal()` будут проваливаться с `no route to host`. Эффект сохраняется до конца сессии Hermes или до явного `unset`.

**Два источника ошибки:**
1. **Порт не слушает** (обычно 1083 — sing-box mixed-inbound не запущен) → `connection refused`
2. **Неверный хост/порт** (обычно 192.168.103.70:8888 — безголовый Mac pro) → `no route to host`. Этот порт 8888 может быть настроен в `.zshrc` для `proxy_on` или `alias` и просачивается в окружение через `source ~/.zshrc`.

**Решение:** перед любыми тестами agy явно сбросить прокси:
```bash
unset http_proxy https_proxy all_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY
# И только после этого установить нужный:
export HTTP_PROXY=http://127.0.0.1:1083
export HTTPS_PROXY=http://127.0.0.1:1083
```

**Диагностика:** если agy молча падает без логов — проверить:
```bash
echo "HTTP_PROXY=$HTTP_PROXY"
# Если показывает 192.168.103.70:8888 — оно! unset и заново.
```

### C. Неизвестное имя модели

```
model sonnet is not recognized as a known model or custom model in settings
```

Алиас `sonnet` не существует в этой версии Cloud Code API. В `settings.json` используется полное имя (`Claude Sonnet 4.6 (Thinking)`). При передаче нераспознанного имени — модель не резолвится, agy падает на fallback с тем же `FAILED_PRECONDITION`.

**Решение:** не использовать `--model sonnet`. Либо опустить флаг (будет взята модель из settings.json), либо указать точное имя из вывода `agy models`.

## Причина

agy (бывший Gemini CLI) использует **Google Cloud Code Assist API** (`cloudcode-pa.googleapis.com`), а не публичный Gemini API. Этот API:

- Проверяет регион не только по IP, но и по OAuth-аккаунту / billing-проекту
- Не поддерживается в ряде стран, включая Китай
- Может блокировать датацентровые IP (Datacamp, Hetzner и т.д.) даже если страна формально разрешена

### Provider routing: Anthropic ≠ Google

API `cloudcode-pa.googleapis.com` маршрутизирует модели **по-разному в зависимости от провайдера**:

| Провайдер | Модели | Работает из Китая? |
|-----------|--------|-------------------|
| Anthropic | Claude Sonnet 4.6 (Thinking), Claude Opus 4.6 (Thinking) | ✅ Да |
| Google | Gemini 3.5 Flash (Low/Medium/High), Gemini 3.1 Pro (Low/High) | ❌ Нет — FAILED_PRECONDITION |
| OSS | GPT-OSS 120B (Medium) | ✅ Да (предположительно) |

Anthropic-модели проходят через **партнёрский шлюз Google** (Vertex AI), который не проверяет регион. Google-модели идут через **нативный стек генерации** Cloud Code Assist с региональной проверкой.

**Диагностический приём:** если `agy models` показывает все модели, `loadCodeAssist` работает, но генерация падает — попробуй сменить модель на Anthropic. Если заработало — проблема именно в провайдер-специфичной маршрутизации, а не в OAuth или сети.

Полный список моделей (актуально на июль 2026):
```
Gemini 3.5 Flash (Medium)
Gemini 3.5 Flash (High)
Gemini 3.5 Flash (Low)
Gemini 3.1 Pro (Low)
Gemini 3.1 Pro (High)
Claude Sonnet 4.6 (Thinking)
Claude Opus 4.6 (Thinking)
GPT-OSS 120B (Medium)
```

### Shadow project model

Для каждого consumer-пользователя Google AI Pro/CLI Google автоматически создаёт невидимый GCP-проект (не отображается в Cloud Console). Если при первичной OAuth Google определил неподдерживаемую локацию — этот флаг «запекается» в метаданные проекта. Все последующие запросы с `x-goog-user-project` отклоняются, так как проект не имеет IAM-разрешений на `v1internal:generateContent`.

Anthropic-модели не подвержены этому — они идут через Vertex AI (`aiplatform.googleapis.com`), у которого независимая система управления проектами.

**Почему старый токен работал, а новый нет:** Если пользователь авторизовался до введения geo-блокировок, его теневой проект был создан без ограничений. После переавторизации (expiry токена) Google создаёт или перепривязывает проект уже с текущими политиками — и новый блокируется.

**Фундаментальное решение:** привязать agy к реальному GCP-проекту с billing (опция *Use a Google Cloud project* при OAuth). Это переводит запросы на корпоративный шлюз (`cloudaicompanion.googleapis.com`), где гео-валидация идёт по конфигурации проекта, а не по consumer-профилю.

## Диагностика

### 1. Логи agy CLI — единственный источник правды

agy **не имеет флагов `--debug` / `--verbose`**. Единственный способ получить детали HTTP-статусов и ошибок — читать файлы логов в `~/.gemini/antigravity-cli/log/`. Логи содержат URL'ы всех запросов и полное тело ошибки.

```bash
cat ~/.gemini/antigravity-cli/log/*.log | grep -i "FAILED_PRECONDITION\\|location\\|region\\|not supported"
```

### 2. Проверить, не мешает ли HTTP_PROXY

```bash
echo "HTTP_PROXY=$HTTP_PROXY"
unset http_proxy https_proxy all_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY
```

### 3. Проверить аутентификацию (аккаунт в keyring)

```bash
grep 'authenticated successfully as' ~/.gemini/antigravity-cli/log/*.log | tail -1
gcloud auth list
cat ~/.gemini/antigravity-cli/settings.json
```

### 4. Проверить доступность API

```bash
curl -sI "https://daily-cloudcode-pa.googleapis.com" -o /dev/null -w "%{http_code} %{time_total}s\\n"
# 404 = API существует (404 от Google, а не таймаут)
```

### 5. Проверить IP выхода

```bash
curl -s https://ipinfo.io/json
```

### 6. Эндпоинт-гранулярность

API `cloudcode-pa.googleapis.com` блокирует **не все эндпоинты одинаково**:

- `v1internal:loadCodeAssist` — работает (HTTP 200)
- `v1internal:fetchAvailableModels` — работает (HTTP 200)
- `v1internal:streamGenerateContent` — блокирует (HTTP 400)

Проверить в логах:

```bash
grep -E 'http_helpers|FAILED_PRECONDITION' ~/.gemini/antigravity-cli/log/*.log
```

### 7. Staging vs Production endpoint (известный баг v1.1.1)

**Известный баг** (https://discuss.ai.google.dev/t/bug-remote-servers-ssh-wsl-using-staging-endpoint-daily-cloudcode-pa-instead-of-production-fix-included/139412): agy и language_server хардкодят staging-эндпоинт `daily-cloudcode-pa.googleapis.com` вместо production `cloudcode-pa.googleapis.com`. OAuth-токены consumer-подписки (Google AI Pro) на staging не работают.

**Симптом:** в логах все запросы к `daily-cloudcode-pa.googleapis.com`:
```bash
grep 'http_helpers.*URL: https://daily-' ~/.gemini/antigravity-cli/log/*.log
```

**Основной фикс — `CLOUD_CODE_URL`:**  
Переменная была найдена через `strings` в бинарнике language_server/agy. Алгоритм поиска:  
`strings <binary> | grep -i "CLOUD_CODE\\|cloud_code"`

```bash
export CLOUD_CODE_URL=https://cloudcode-pa.googleapis.com
agy ...
```

**Подтверждение что фикс сработал:** в логах вместо `daily-cloudcode-pa.googleapis.com` появляется `cloudcode-pa.googleapis.com`:
```bash
grep 'http_helpers.*URL: https://daily-' ~/.gemini/antigravity-cli/log/*.log  # не должно быть
grep 'http_helpers.*URL: https://cloudcode-' ~/.gemini/antigravity-cli/log/*.log  # должно быть
```

**CNAME/SSL деталь:** сертификат `cloudcode-pa.googleapis.com` содержит `*.googleapis.com`, что покрывает оба домена (production и daily). DNS-редирект daily → production IP теоретически возможен, но бесполезен — Google маршрутизирует бэкенды по SNI/Host header, а не по IP.

**Не работает:** `ANTIGRAVITY_BASE_URL`, `jetski.cloudCodeUrl` в `settings.json` — оба игнорируются.

**Wrapper-фикс для language_server (альтернатива):**
```bash
# Только если найден отдельный language_server бинарник
LSDIR=$(dirname $(find /Applications/Antigravity*.app -name "language_server*" -type f | head -1))
cd "$LSDIR"
cp language_server language_server.orig
cat > language_server << 'WRAPPER'
#!/bin/bash
ARGS="${@//daily-cloudcode-pa.googleapis.com/cloudcode-pa.googleapis.com}"
exec "$(dirname "$0")/language_server.orig" $ARGS
WRAPPER
chmod +x language_server
```
**Ограничение:** на macOS `/Applications/` защищён SIP — `mv language_server language_server.orig` может не сработать (`Operation not permitted`). В таком случае — только `CLOUD_CODE_URL`.

**Добавить в ~/.zshrc** (навсегда):
```bash
export CLOUD_CODE_URL=https://cloudcode-pa.googleapis.com
```

### 8. Версия agy (регрессия)

```bash
grep 'Language server version' ~/.gemini/antigravity-cli/log/*.log
grep 'expired=' ~/.gemini/antigravity-cli/log/*.log | head -3
```

### 9. Системные прокси macOS

```bash
scutil --proxy
networksetup -getwebproxy Wi-Fi
networksetup -getsecurewebproxy Wi-Fi
networksetup -getsocksfirewallproxy Wi-Fi
```

## Решения

### A. Сменить exit location прокси на США

Google Cloud Code Assist официально поддерживается в US. Швейцария, Германия, Нидерланды — могут не работать.

### B. Использовать другой инструмент

Если регион не меняется — agy с Google-моделями не заработает. Альтернативы:
- Claude Code (`claude`)
- OpenCode (`opencode`)
- Hermes Agent

Anthropic-модели в agy при этом **работают** — можно использовать agy только с Claude.

### C. Keyring: сменить OAuth аккаунт

Удалить токены из macOS Keychain и переавторизоваться под другим Google-аккаунтом:

```bash
# 1. Удалить все токены agy
security delete-generic-password -s "Antigravity Safe Storage" -a "Antigravity" 2>/dev/null
security delete-generic-password -s "Antigravity Safe Storage" -a "Antigravity Key" 2>/dev/null
security delete-generic-password -s "gemini" -a "antigravity" 2>/dev/null
security delete-generic-password -s "Antigravity IDE Safe Storage" -a "Antigravity IDE" 2>/dev/null
security delete-generic-password -s "Antigravity IDE Safe Storage" -a "Antigravity IDE Key" 2>/dev/null
security delete-generic-password -s "Gemini Safe Storage" -a "Gemini Keys" 2>/dev/null

# 2. Очистить residual state
rm -rf ~/.gemini/antigravity-cli/conversations/* 2>/dev/null
rm -rf ~/.gemini/antigravity-cli/log/*.log 2>/dev/null

# 3. Запустить agy — откроется браузер, выбрать нужный аккаунт
agy

# 4. Проверить
grep 'authenticated successfully as' ~/.gemini/antigravity-cli/log/*.log | tail -1
```

**Важно:** agy использует macOS Keychain, а не gcloud auth. `gcloud auth login` НЕ влияет на agy.

### D. Cloudflare Warp — бесплатная замена Datacamp-прокси

Если используемый прокси (Datacamp, Hetzner и др.) блокируется Google по ASN — Cloudflare Warp решает проблему. Warp маскирует ASN на `13335 Cloudflare, Inc.`, который Google **не блокирует** (CDN, а не hosting-диапазон).

**Установка и настройка:**
```bash
# Установить (если нет)
brew install cloudflare-warp

# Запустить демон
open /Applications/Cloudflare\ WARP.app

# Зарегистрировать
warp-cli registration new

# Режим прокси (не VPN)
warp-cli mode proxy
warp-cli proxy port 40000
warp-cli connect

# Проверить
curl -s --proxy http://127.0.0.1:40000 https://ipinfo.io/json
# → org: "AS13335 Cloudflare, Inc."
```

**Использование с agy:**
```bash
export HTTP_PROXY=http://127.0.0.1:40000
export HTTPS_PROXY=http://127.0.0.1:40000
export CLOUD_CODE_URL=https://cloudcode-pa.googleapis.com
agy
```

**Сравнение прокси:**
| Тип | ASN | Блокируется Google? | Стоимость |
|-----|-----|-------------------|-----------|
| Datacamp | AS60068 | ✅ Да (hosting) | Есть |
| Hetzner | AS24940 | ✅ Да (hosting) | Есть |
| Cloudflare Warp | AS13335 | ❌ Нет (CDN) | Бесплатно |
| Резидентный прокси | ASN провайдера | ❌ Нет | Платно |

**Warp+ license key (если есть):**
```bash
warp-cli registration new      # если уже есть: registration delete → registration new
warp-cli registration license XXXXX-XXXXX-XXXXX
warp-cli mode proxy
warp-cli proxy port 40000
warp-cli connect
```

**Важно:** Warp требует регистрации (любой email). При первом `warp-cli connect` может открыться браузер для Teams-логина (можно пропустить — consumer режим работает без Teams).

**Ограничение: бесплатный Warp → China IP, Warp+ → всё ещё China IP.**
Даже с Warp+ ключом, Cloudflare подключает потребителя к ближайшему узлу. Из Китая это Chongqing. Google блокирует China IP независимо от ASN (Cloudflare). Чтобы получить US IP через Warp, нужна enterprise-лицензия с настройкой виртуальной сети (`warp-cli vnet`), которая недоступна consumer-аккаунтам.

### E. HTTP mixed inbound в sing-box (для Go-приложений)

Если в системе установлен sing-box (TUN), agy (Go) не видит TUN и требует `HTTP_PROXY`. Решение — **mixed inbound** (HTTP + SOCKS5 на одном порту):

```json
// В секцию "inbounds" ~/sing-box-config.json
{
  "type": "mixed",
  "tag": "mixed-in",
  "listen": "127.0.0.1",
  "listen_port": 1083
}
```

**Проверка:**
```bash
sudo lsof -iTCP:1083 -sTCP:LISTEN
HTTP_PROXY=http://127.0.0.1:1083 curl -s https://ipinfo.io/json
```

**Автозапуск (launchd):**
```bash
sudo launchctl bootstrap system /Library/LaunchDaemons/com.user.singbox.plist
sudo launchctl bootout system /Library/LaunchDaemons/com.user.singbox.plist
```

**Hermes-gotcha:** `source ~/.zshrc; proxy_on` в одном `terminal()` вызове оставляет `HTTP_PROXY` во всех последующих. Всегда чистить перед agy:

```bash
unset http_proxy https_proxy all_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY
```

### F. Warp + sing-box TUN — известный конфликт

Если sing-box TUN активен, Cloudflare Warp не может соединиться — WireGuard-пакеты (UDP к `162.159.198.0/24`) перехватываются TUN-интерфейсом, создавая петлю (loop). Симптом: `warp-cli status` показывает вечное `Connecting: Performing happy eyeballs`.

**Решения:**
- Остановить sing-box перед запуском Warp (и наоборот):
  ```bash
  # Стоп sing-box
  sudo launchctl bootout system /Library/LaunchDaemons/com.user.singbox.plist
  sudo pkill -9 sing-box
  # Запустить Warp
  warp-cli connect
  ```
- Либо использовать Warp в режиме VPN (не proxy) — переопределяет маршрутизацию на уровне ОС
- Добавить Cloudflare IP-диапазоны (`162.159.192.0/24`) в sing-box route rule с `action: "direct"`, но это не всегда помогает — петля может сохраняться на уровне сетевого стека macOS

**Важно: бесплатный Warp — China IP, не US.** В бесплатном режиме Cloudflare Warp подключается к ближайшему узлу Cloudflare. Для пользователей в Китае это означает IP из Китая (org: AS13335 Cloudflare, город: Chongqing). Даже Warp+ (платный) не меняет страну — enterprise-функция `warp-cli vnet` для выбора региона доступна только Teams/Enterprise аккаунтам.

**Ключевой урок:** изменение ASN (Datacamp → Cloudflare) **не помогает**, если страна остаётся Китай. Google Cloud Code Assist блокирует по геолокации IP, а не только по ASN-классификации hosting/CDN. Чтобы Gemini заработал через Cloudflare, нужен либо Warp Teams с US-выходом, либо другой прокси/VPN с US-резидентным IP (не Datacamp/Hetzner).

### G. Метод обнаружения CLOUD_CODE_URL

Переменная `CLOUD_CODE_URL` была найдена через `strings` в бинарнике language_server и agy. Алгоритм поиска неизвестных env-var/конфигов в Go-бинарниках:

```bash
# Поиск env var
strings /Applications/Antigravity.app/Contents/Resources/bin/language_server | grep -i "CLOUD_CODE\\|cloud_code\\|CLOUDCODE" | head -5

# Поиск флагов командной строки
strings /Applications/Antigravity.app/Contents/Resources/bin/language_server | grep "cloud_code_endpoint" | head -5
```

### H. Диагностический чеклист (быстрый старт)

Когда пользователь жалуется на `FAILED_PRECONDITION 400` в agy — проверять в этом порядке:

1. **Эндпоинт:** `grep 'http_helpers.*URL' ~/.gemini/antigravity-cli/log/*.log | sort -u | head -5` — daily- или cloudcode-?
2. **Прокси:** `echo $HTTP_PROXY` — не висит ли мёртвый адрес?
3. **Аккаунт:** `grep 'authenticated successfully as' ~/.gemini/antigravity-cli/log/*.log | tail -1` — кто?
4. **Модель:** какую модель пробует — Anthropic или Google?
5. **IP:** `curl -s --proxy ... https://ipinfo.io/json` — какой ASN/страна?

### I. Бинарный патчинг: open-antigravity-patcher (крайнее средство)

Если ни один из методов не помог — сообщество поддерживает **open-antigravity-patcher** (https://github.com/AvenCores/open-antigravity-patcher), который модифицирует бинарные файлы agy/language_server:

- Исправляет хардкод `daily-cloudcode-pa.googleapis.com` → `cloudcode-pa.googleapis.com` в бинарнике
- Снимает экран Eligibility Check
- Для macOS: ad-hoc переподпись бандла после патча

**Ограничение:** не исправляет серверную geo-блокировку OAuth-токена. Если проблема на стороне Google — патч бесполезен.

### J. Open-source прокси-ротация (замена Datacamp-ASN)

Если Datacamp/Hetzner ASN блокируется Google, но хочется self-hosted решение (не платить за Bright Data):

- **alpkeskin/rota** (https://github.com/alpkeskin/rota) — Go + Next.js, прокси-ротация с дашбордом, health-check, Docker. Нужен источник резидентных IP.
- **mattes/rotating-proxy** (https://github.com/mattes/rotating-proxy) — TOR-based ротация, бесплатно, но медленно.
- **abcloudio/iprotal** (https://github.com/abcloudio/iprotal) — self-hosted резидентный прокси-менеджер, HTTP/SOCKS5.

Cloudflare Warp — самый простой и бесплатный вариант (AS13335), но конфликтует с sing-box TUN (см. секцию F).

## Структура конфигов agy

| Путь | Назначение |
|------|-----------|
| `~/.gemini/antigravity-cli/` | CLI данные (conversations, brain, log) |
| `~/.gemini/antigravity-cli/settings.json` | Модель, trustedWorkspaces |
| `~/.gemini/antigravity/` | IDE данные (Electron-приложение) |
| `~/.gemini/config/` | Общие конфиги (MCP, plugins) |
| `~/Library/Application Support/Antigravity/` | Electron storage (Cookies, Local Storage) |

## Примечание

Проблема НЕ всегда в прокси/сети — Google может быть доступен. Проблема в политике Google Cloud Code Assist, который блокирует регионы на уровне API и OAuth-аккаунта, а не сети. Anthropic-модели обходят это через партнёрский шлюз Vertex AI.
