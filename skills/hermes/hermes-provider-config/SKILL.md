---
name: hermes-provider-config
description: Настройка, проверка и восстановление провайдеров/моделей в конфиге Hermes — диагностика, explicit providers, fallback, верификация после смены модели.
tags: [hermes, providers, config, model, setup, troubleshooting]
related_skills: [hermes-self-maintenance, hermes-agent]
---

# Hermes Provider Config

Управление провайдерами в `~/.hermes/config.yaml`. Когда модель переключается runtime (через `/model` или `hermes model`), конфиг может не обновиться — это надо проверять вручную.

## Bailian: Arrearage при наличии free quota (диагностика и фикс)

Когда API возвращает `"type":"Arrearage"` / 400, но GET /v1/models работает:

### 1. "免费额度用完即停" ВЫКЛЮЧЕН (главная причина)

**Симптомы:**
- В консоли 模型用量 → 免费额度 остатки квоты есть
- Приходят уведомления "免费额度量用尽通知"
- После этого — "阿里云百炼大模型推理服务欠费提醒"

**Причина:** guard ВЫКЛЮЧЕН ПО УМОЛЧАНИЮ для новых аккаунтов! Когда free quota исчерпалась, Bailian автоматически переключился на postpaid → списал с prepaid → баланс в минус → Arrearage.

Поддержка Aliyun подтвердила: "默认情况下，免费额度耗尽后继续调用会直接按量扣费，而非返回 403 错误"
(По умолчанию, после исчерпания free quota запросы продолжаются с поштучной оплатой, не возвращая 403.)

**Фикс:**
1. Bailian консоль → 模型用量 → 免费额度
2. Нажать **"批量操作免费额度用完即停"** → открывается выпадающий список
3. Выбрать "全选" → нажать "开启" (или включить для отдельных моделей)
4. Для разблокировки API: пополнить баланс (хотя бы ¥10)

**Важно:** 
- После включения guard, когда free quota кончится — API вернёт 403 `AllocationQuota.FreeTierOnly` вместо списания. Это норма, просто переключи модель.
- Guard нельзя выключить, пока free quota не исчерпана полностью (分钟级出账, есть задержка).
- Если у тебя 165+ моделей — надо проверять ВСЕ вкладки (大语言模型, 视觉模型, 全模态模型, 语音模型, 向量模型).

### 2. Баланс реально в минусе

Billing Console показывает "已欠费" (баланс отрицательный). Решение — пополнить.

### 3. Аккаунт ограничен (редко)

Баннер "部分功能使用受限" — нажать, прочитать что требуется. Может требовать верификации или принятия условий.

### Быстрая диагностика: центр уведомлений

Открыть `https://notifications2.console.aliyun.com/innerMsg/unread/0`
Типичная хронология Arrearage-сценария (по уведомлениям):

| Время | Уведомление | Что произошло |
|-------|-------------|--------------|
| 08:56 | **免费额度量用尽通知** | Free quota кончилась у модели (guard был OFF) |
| 09:00 | **可用额度不足提醒** | Начались списания с prepaid |
| 09:03 | **欠费提醒** | Баланс в минусе, API заблокирован |
| 10:06 | **恢复服务提醒** | Баланс пополнен/восстановлен |
| 10:52 | **免费额度量用尽通知** | У другой модели кончилась квота |
| 15:17 | **可用额度不足提醒** | Снова списания |
| 15:21 | **欠费提醒** | Снова баланс в минусе |

В колокольчике отображается количество непрочитанных. Всего есть категории: 账户资金消息 (баланс), 产品消息 (модели), 服务消息.

### Коды ошибок Bailian API

| HTTP | error.type | Причина | Guard нужен? |
|------|-----------|---------|-------------|
| 400 | `Arrearage` | Баланс в минусе. Free quota кончилась, guard был OFF → пошли списания | Включить guard + пополнить |
| 401 | `invalid_request_error` | API ключ не передан или неверный | Проверить key |
| 403 | `AllocationQuota.FreeTierOnly` | Free quota исчерпана, guard ON — нормальная остановка | ON ✓, просто переключи модель |
| 404 | — | Модель не найдена | — |

**Ключевое отличие:** `AllocationQuota.FreeTierOnly` (403) — норма, guard работает, просто переключи модель. `Arrearage` (400) — баланс в минусе, надо пополнить.

### Что не является причиной (частые ложные диагнозы)

- ❌ "Я не использовал платные модели" — неважно. Списания идут с prepaid ПОСЛЕ того как free quota кончилась, даже на бесплатных моделях, если guard OFF.
- ❌ "Free quota ещё есть (803K/1M)" — У КАКОЙ-ТО модели кончилась. 165+ моделей, проверять все вкладки.
- ❌ "Счёт в порядке, ¥9.79" — был ¥9.79, стал -¥3.6. Guard OFF → free quota кончилась → пошло списание.
- ❌ "GET /v1/models работает" — список моделей всегда доступен, это не признак здоровья аккаунта.

## Быстрая диагностика

```bash
# Текущая модель и провайдер
grep -A3 '^model:' ~/.hermes/config.yaml

# Какие провайдеры прописаны явно
grep -A10 '^providers:' ~/.hermes/config.yaml | head -15

# Провайдер есть в /model пикере, но показывает 0 моделей?
# Проверить дублирующиеся ключи в custom_providers:
grep -n 'models:' ~/.hermes/config.yaml

# Проверка связности всех провайдеров
hermes doctor | grep -E '✓|⚠|✗'
```

## Bailian diagnostics (прямая проверка)

Когда Bailian падает с непонятной ошибкой — проверить напрямую через curl. Это исключает проблемы с Hermes маршрутизацией и показывает ответ API как есть.

```bash
# Шаг 1: проверить имя env var
echo "BAILIAN_API_KEY: ${BAILIAN_API_KEY:-(empty)}"
echo "DASHSCOPE_API_KEY: ${DASHSCOPE_API_KEY:-(empty)}"

# Шаг 2: прямой запрос — видно статус, код и тело ошибки
curl -s -w "\nHTTP_CODE:%{http_code}" https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions \
  -H "Authorization: Bearer $BAILIAN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen3.6-plus","messages":[{"role":"user","content":"test"}],"max_tokens":10}'
```

**Известные коды ответов Bailian:**
| HTTP Code | error.type | Значение |
|-----------|-----------|----------|
| 400 | `Arrearage` | Аккаунт заблокирован за неуплату. Даже free quota не работает. Пополнить баланс в консоли. |
| 401 | `invalid_request_error` | API ключ не передан или неверный. Проверить `api_key_env` в config.yaml. |
| 404 | — | Модель не найдена или не развёрнута. |
| 429 | — | Rate limit. Кинуть fallback. |

При "Arrearage" Hermes будет фолбечиться на fallback_providers/fallback_model при каждом запросе, т.к. Bailian стабильно возвращает 400 на любой запрос. Выход — пополнить счёт или переключиться на другой провайдер через `hermes-use`.

## Когда нужно настраивать вручную

1. **После `/model deepseek-v4-flash`** — runtime-смена модели НЕ обновляет `model.default` и `model.provider` в config.yaml. Они остаются старыми.
2. **После клонирования конфига на другой Mac** — провайдеры и base_url могут отличаться.
3. **Если `providers: {}`** — Hermes полагается на model_catalog (фетчится с `hermes-agent.nousresearch.com`). Из Китая это может не грузиться → провайдеры не резолвятся.
4. **После смены API-ключа** — проверить что `.env` и `providers` согласованы.

## Настройка explicit providers

Вместо `providers: {}` (зависимость от model_catalog) прописать явно:

```bash
# model section — текущая модель
hermes config set model.default deepseek-v4-flash
hermes config set model.provider deepseek
hermes config set model.base_url ''  # built-in провайдеры знают свой endpoint

# providers section — явные base_url
hermes config set providers.deepseek   '{"base_url": "https://api.deepseek.com/v1"}'
hermes config set providers.kimi       '{"base_url": "https://api.moonshot.cn/v1"}'
hermes config set providers.anthropic  '{"base_url": "https://api.anthropic.com"}'
hermes config set providers.openrouter '{"base_url": "https://openrouter.ai/api/v1"}'
```

**Важно:** `hermes config set` сериализует вложенные объекты как JSON-строки в YAML:
```yaml
providers:
  deepseek: '{"base_url": "https://api.deepseek.com/v1"}'
```
Hermes это корректно парсит, но визуально выглядит не как вложенный YAML. Это нормально.

## Fallback-цепочка (multi-tier)

Hermes поддерживает 3-уровневую цепочку фалбеков:

```
primary (model.provider / model.default)
  → fallback_providers[] (первый фалбек)
    → fallback_model (второй фалбек)
```

### fallback_providers (первый фалбек)

Массив JSON с одним или несколькими провайдерами. Активируется при ошибках первичного провайдера (401, 429, timeout).

```bash
# Установка
hermes config set fallback_providers '[{"provider": "kimi", "model": "kimi-k2.6"}]'

# Проверка
grep -A1 '^fallback_providers:' ~/.hermes/config.yaml
```

Формат в config.yaml (сериализуется как JSON-строка):
```yaml
fallback_providers: '[{"provider": "kimi", "model": "kimi-k2.6"}]'
```

### fallback_model (второй фалбек)

Единичная модель, активируется если и `fallback_providers` тоже сдох.

```bash
# Установка
hermes config set fallback_model.provider nous
hermes config set fallback_model.model stepfun/step-3.7-flash:free
# Опционально — base_url для фалбека (если провайдер не built-in)
hermes config set model.base_url https://inference-api.nousresearch.com/v1

# Проверка
grep -A2 '^fallback_model:' ~/.hermes/config.yaml
```

Формат:
```yaml
fallback_model:
  provider: nous
  model: stepfun/step-3.7-flash:free
```

### Пример полной конфигурации — внимание на model.base_url

**ВАЖНО:** `model.base_url` — это base_url ДЕФОЛТНОЙ модели, не fallback_model. Built-in провайдеры (deepseek/kimi) игнорируют его. НО `model.base_url` влияет на `/model` — если поставить сюда nous portal, `/model` будет стучаться туда и виснуть, даже если дефолтный провайдер — deepseek.

```yaml
model:
  default: deepseek-v4-flash
  provider: deepseek
  # model.base_url НЕ СТАВИТЬ — сломает /model. Built-in nous знает свой endpoint.
fallback_providers: '[{"provider": "kimi", "model": "kimi-k2.6"}]'
fallback_model:
  provider: nous
  model: stepfun/step-3.7-flash:free
```

Если nous fallback падает — проблема в `NOUS_API_KEY`, не в `model.base_url`.

### Pitfalls (fallback)
- `fallback_providers` — строка JSON-массива. `hermes config set` сериализует как YAML-строку, это нормально.
- **`model.base_url` ломает `/model`.** Если `/model` висит, а default провайдер не nous — удали `model.base_url`: `hermes config set model.base_url ''`.
- Fallback `nous` — built-in, ему **НЕ нужен** `model.base_url`. Использует `NOUS_API_KEY` из окружения.
- `model.base_url` не влияет на built-in провайдеры (deepseek/kimi), но влияет на `/model`.
- Fallback активируется на auth-ошибки и 429, НЕ на ReadTimeout или обрывы стрима.
- `/model` может виснуть и из-за model_catalog. Решение: `hermes config set model_catalog.enabled false` или прокси.
- Быстрое переключение — см. "Быстрое переключение провайдеров" ниже.

## Верификация

```bash
hermes doctor               # проверить связность всех провайдеров
hermes chat -q 'привет'     # проверить что модель отвечает
```

Ожидаемый вывод `hermes doctor` (содержательные строки):
```
✓ OpenRouter API
✓ Kimi / Moonshot
✓ DeepSeek
```

## Настройка multi-tier fallback с nous portal

При использовании nous portal (https://inference-api.nousresearch.com) как второго фалбека:

```bash
# 1. Основной провайдер
hermes config set model.default deepseek-v4-flash
hermes config set model.provider deepseek

# 2. Первый фалбек (kimi)
hermes config set fallback_providers '[{"provider": "kimi", "model": "kimi-k2.6"}]'

# 3. Второй фалбек (nous)
hermes config set fallback_model.provider nous
hermes config set fallback_model.model stepfun/step-3.7-flash:free
# НЕ ставить model.base_url — built-in nous знает свой endpoint.
# model.base_url только сломает /model команду.

# 4. Проверить
grep -A3 '^model:' ~/.hermes/config.yaml
grep -A2 '^fallback_' ~/.hermes/config.yaml
```

**Built-in провайдер "nous":** использует `NOUS_API_KEY` из окружения (не из `.env`). Аутентификация через Nous Research Portal (https://portal.nousresearch.com). При 401 ошибках — проверить ключ/баланс на портале.

### Если nous не работает как fallback (и ты уверен что NOUS_API_KEY валидный)

Проверить ручками:
```bash
hermes chat -m stepfun/step-3.7-flash:free --provider nous -q "test"
```
Если работает — fallback цепочка исправна. Если нет — проблема в API ключе или сети к nousresearch.com (в Китае может быть заблокирован).

### Удаление model.base_url (если он мешает /model)

`hermes config unset` НЕ СУЩЕСТВУЕТ. Альтернативы:

```bash
# Способ 1: через sed
sed -i '' '/^  base_url:/d' ~/.hermes/config.yaml

# Способ 2: через config set (пустая строка)
hermes config set model.base_url ''
```

## Быстрое переключение провайдеров (альтернатива `/model`)

Когда `/model` в TUI висит (из-за model_catalog или таймаута на одном из провайдеров):

```bash
# Ручное переключение (одна строка)
hermes config set model.provider deepseek && hermes config set model.default deepseek-v4-flash
hermes config set model.provider bailian && hermes config set model.default qwen3.6-plus
hermes config set model.provider kimi && hermes config set model.default kimi-k2.6
```

### Скрипт `hermes-use`

Установлен в `~/.hermes/scripts/hermes-use` + zsh-функция:

```bash
hermes-use list                       # показать провайдеры
hermes-use deepseek                   # deepseek-v4-flash
hermes-use bailian                    # qwen3.6-plus
hermes-use bailian qwen3.7-plus       # любая модель
```

**Провайдеры в скрипте:** deepseek, kimi, nous, bailian.
Bailian по умолчанию: `qwen3.6-plus` (free quota 1M).

**Установка функции в `.zshrc`:**
```bash
hermes-use() { bash ~/.hermes/scripts/hermes-use "$@"; }
```

## Custom providers (`custom_providers:`)

Секция `custom_providers:` в config.yaml — для провайдеров, которых нет в built-in каталоге. Добавляется вручную в конец файла:

```yaml
custom_providers:
  - name: my-provider
    base_url: https://api.example.com/v1
    api_key_env: MY_API_KEY      # env var name
    api_mode: chat_completions
    skip_model_validation: true  # ⚠️ см. ниже
    models:                      # опционально — список доступных моделей
      - model-a
      - model-b
```

После добавления появляется в `/model` пикере как `custom:my-provider`.

### `skip_model_validation: true` — когда нужно

Bailian/DashScope и некоторые другие провайдеры **не реализуют `GET /v1/models`** (OpenAI-совместимый эндпоинт). Без этого флага Hermes при переключении модели пытается её валидировать, получает 404 и отказывает.

**Ставь `true` для:** DashScope (Bailian), китайских провайдеров, любых кастомных gateway.

### Пример: Alibaba Bailian CN

```yaml
custom_providers:
  - name: bailian-cn
    base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
    api_key_env: BAILIAN_API_KEY   # ⚠️ Имя твоей env var. У разных пользователей может отличаться (BAILIAN_API_KEY или DASHSCOPE_API_KEY). Проверить: echo $BAILIAN_API_KEY
    api_mode: chat_completions
    skip_model_validation: true
    models:
      - qwen3.7-max
      - qwen3.6-plus
      - qwen3-coder-plus
      - glm-5
      # НЕ добавлять: deepseek-v4-flash, kimi-k2.5, MiniMax-M2.5 — нет free quota
```

**Alibaba/Alibaba-CN в `/model` пикере — внимание!**

В built-in model_catalog есть два провайдера:
- `alibaba` (51 модель) → `dashscope-intl.aliyuncs.com` — **международный**, твой CN ключ НЕ работает
- `alibaba-cn` (83 модели) → `dashscope.aliyuncs.com` — **китайский**, работает с DASHSCOPE_API_KEY

Проблема: `alibaba-cn` может НЕ появляться в `/model` пикере из-за фильтрации. Решение — создать `custom:bailian-cn` через `custom_providers:` как выше.

## Vision analysis fallback (browser_vision)

`vision_analyze` tool может падать когда провайдер не поддерживает формат `image_url` в messages. Известные случаи:

- **DeepSeek** — rejected: `"unknown variant 'image_url', expected 'text'"`
- **Bailian (DashScope)** — может не поддерживать vision через chat/completions
- **qwen3.6-flash** — Gemini API: `models/qwen3.6-flash is not found for generateContent`

### Fallback: browser_vision

Когда `vision_analyze` падает, а изображение доступно локально — использовать `browser_vision` через браузер:

```
1. browser_navigate(url="file:///path/to/image.png")     # открыть в браузере
2. browser_vision(question="описать что на скриншоте")    # анализировать
```

Браузер рендерит PNG как `<img>` и `browser_vision` делает скриншот через CDP — этот путь работает даже когда прямой vision API провайдера не поддерживает формат.

### macOS native OCR (если браузер недоступен)

```python
# Vision framework через osascript/PyObjC
# Требует PyObjC: pip3 install pyobjc-framework-Vision
```

Но проще и надёжнее — `browser_vision`.

## Auxiliary task provider mapping

Вспомогательные задачи (title generation, compression, vision) могут уходить на другой провайдер и падать с ошибками. Явно зафиксировать их:

```bash
hermes config set auxiliary.compression.provider custom:bailian-cn
hermes config set auxiliary.compression.model qwen3.6-plus
hermes config set auxiliary.title_generation.provider custom:bailian-cn
hermes config set auxiliary.title_generation.model qwen3.6-plus
```

### Когда провайдер вспомогательной задачи сломан

Симптом: `⚠ Auxiliary title generation failed: HTTP 400: Access denied...` (или `Auxiliary compression failed`, `Auxiliary vision failed`) — притом что основная модель работает.

Это значит, что в `auxiliary.<task>.provider` прописан конкретный провайдер (например, `custom:bailian-cn`), а его аккаунт в arrears.

**Диагностика — какие auxiliary задачи привязаны к конкретным провайдерам:**
```bash
grep -A2 'title_generation\|compression\|vision\|triage_specifier' ~/.hermes/config.yaml
```

**Фикс — переключить на `auto` (использует дефолтный провайдер):**
```bash
hermes config set auxiliary.title_generation.provider auto
hermes config set auxiliary.title_generation.model ''
hermes config set auxiliary.compression.provider auto
hermes config set auxiliary.compression.model ''
hermes config set auxiliary.vision.provider auto
hermes config set auxiliary.vision.model ''
hermes config set auxiliary.triage_specifier.provider auto
hermes config set auxiliary.triage_specifier.model ''
```

`auto` — безопасный выбор. Hermes использует текущий `model.provider` для этих задач, так что они автоматически следуют за переключением основной модели.

## Fallback цепочка с custom provider

```bash
hermes config set fallback_providers '[
  {"provider": "custom:bailian-cn", "model": "qwen3.6-plus"},
  {"provider": "nous", "model": "stepfun/step-3.7-flash:free"}
]'
```

## Pitfalls

- **Auxiliary задачи падают с 400, когда основная модель работает** — проверь `auxiliary.*.provider`. Если они хардкодят `custom:bailian-cn` (аккаунт в arrears), фикс: переключить на `auto`.
- **Runtime switch не персистится** — `/model deepseek-v4-flash` меняет модель в текущей сессии, но не пишет в config.yaml. После `/reset` или нового запуска вернётся старая.
- **model_catalog из Китая** — если `model_catalog.url` недогрузился, built-in провайдеры могут не разрешиться. Явные `providers:` в config.yaml решают проблему.
- **model.base_url как мусор** — если сменил провайдера, а старый `model.base_url` остался (например, от nousresearch), built-in провайдер игнорирует его, но лучше зачистить: `hermes config set model.base_url ''`.
- **Провайдер есть в `.env`, но не в `providers:`** — built-in провайдеры (deepseek, kimi, anthropic) работают и без явного `providers:` блока, если model_catalog доступен. Для надёжности всё равно прописать явно.
- **`hermes config set` ломает nested YAML** — если нужно именно вложенное YAML-дерево (а не JSON-строка), редактировать config.yaml вручную через `hermes config edit`.
- **`hermes config set custom_providers` → JSON-строка, не YAML-список.** `hermes config set custom_providers '[{...}]'` пишет `custom_providers: '[{...}]'` — JSON-строку. Hermes ожидает YAML-список (`custom_providers:\n  - name: ...`). Симптом: провайдер не появляется в `/model` пикере, хотя `model.provider` указывает на него. Фикс: `hermes config edit` → вручную записать YAML-список с `- name:` элементами и удалить JSON-строку.
- **Custom provider env var** — Hermes ищет `<PROVIDER_NAME>_API_KEY` (в верхнем регистре). Если ключ лежит в другой переменной (например, `DASHSCOPE_API_KEY`), используй `api_key_env:` в custom config или добавь alias в `.env`.
- **api_key_env не совпадает с реальной env var** — Если в `custom_providers` указан `api_key_env: DASHSCOPE_API_KEY`, а в окружении переменная называется `BAILIAN_API_KEY`, Hermes передаёт пустой ключ → 401. Проверить: `echo "$YOUR_ENV_VAR"` и сверить с `api_key_env` в config.yaml. Если не совпадает — исправить config.yaml через `sed` (patch tool заблокирован).
- **Дублирующиеся ключи в custom_providers → 0 моделей** — Если часть конфига добавлена через `hermes config set` (создаёт JSON-строку), а другая часть вручную (YAML-список), в файле может оказаться ДВА `models:` под одним провайдером. YAML-парсер берёт ПОСЛЕДНИЙ ключ → JSON-строка перезаписывает YAML-список → Hermes видит не те модели или 0 моделей. Диагностика: `grep -n 'models:' ~/.hermes/config.yaml` — если строк больше чем провайдеров с models, есть дубликат. Фикс: `sed -i '' 'N,Nd' ~/.hermes/config.yaml` (N = номер строки с дубликатом, определить по `grep -n`). patch заблокирован для config.yaml — только sed.
- **Arrearage на Bailian** — Bailian возвращает HTTP 400 с `error.type: Arrearage`. Причина: free quota закончилась, а "免费额度用完即停" был выключен → пошли списания с prepaid. Фикс: пополнить счёт (разблокирует API) + включить guard для всех моделей (чтобы не повторилось). Подробности в `references/bailian-billing-investigation.md`.
- **Alibaba vs Alibaba-CN в `/model`** — `Alibaba` в пикере = международный эндпоинт (`dashscope-intl`). CN ключ там не работает. Выбирай `custom:bailian-cn` или используй `hermes-use bailian`.
- **`/model` висит?** — проверь `model.base_url` (удали через sed), `model_catalog.enabled` (отключи), или сетевую доступность `hermes-agent.nousresearch.com`.
- **Aliyun Bailian как провайдер** — см. `references/aliyun-bailian-setup.md`.
  - **Управление защитой от платного режима (用完即停):** `references/bailian-free-quota-guard.md` — batch enable/disable, необратимость, проверка статуса через CDP.
  - **Рекомендуется:** `custom:bailian-cn` с `skip_model_validation: true` или built-in `alibaba-cn` (если виден в пикере).
  - **165 моделей с бесплатной квотой** (1M токенов каждая, ~90 дней), **35 моделей БЕЗ квоты** — платные.
  - **⚠️ deepseek-v4-flash НЕ входит в бесплатную квоту Bailian!** Если через Bailian вызывается deepseek-v4-flash (через custom:bailian-cn), каждый запрос идёт post-paid. Используй qwen3.6-plus/flash для бесплатного инференса через Bailian.
  - **Платные модели (без free quota):** deepseek-v4-flash, vanchin/deepseek-v4-pro, kimi/kimi-k2.5, kimi/kimi-k2.6, MiniMax/MiniMax-M2.5/M2.7/M2.1/M3, qwen-deep-research, qwen-deep-research-2025-12-15, ZHIPU/GLM-5, ZHIPU/GLM-5.1 и ~24 других сторонних провайдеров (всего 35). Полный список — в `references/aliyun-bailian-setup.md`.
  - **qwen3.7-max** — метка "不支持开启" ≠ "нет free quota". Квота есть (1M), но нет авто-стопа. Не путать со статусом "无免费额度"! Для актуального остатка проверяй консоль через CDP.
  - **Быстрая проверка платности модели:** префиксы `vanchin/`, `siliconflow/`, `kimi/`, `MiniMax/`, `ZHIPU/` = почти всегда платные. Модели без префикса (`qwen-*`, `glm-*`) = почти всегда бесплатные.
  - Все Coding Plan модели доступны через обычный API ключ — Coding Plan не нужен пока есть free quota.
  - **Проверка расходов:** см. `references/bailian-quota-investigation.md`.
  - **Диагностика Arrearage (400):** см. `references/bailian-billing-investigation.md` — полный трейс расследования: консоль биллинга, остатки квоты, баннер 部分功能使用受限.
- **Bailian Coding Plan** — см. `references/bailian-coding-plan.md`.

## Volcengine Coding Plan (火山引擎)

Альтернатива Bailian — ByteDance's Volcengine подписка для AI coding инструментов.

**Планы (июнь 2026):** Lite (40元/мес), Pro (200元/мес).

### Volcengine Coding Plan config

```bash
# Сохранить ключ в .env
echo 'export VOLC_CODING_API_KEY=ark-xxxx-xxxxx' >> ~/.hermes/.env

# Добавить в custom_providers вручную через hermes config edit
# ⚠️ НЕ использовать hermes config set custom_providers — он сериализует
#    массив в JSON-строку, Hermes не парсит, провайдер не появляется в /model
#    Вместо этого открыть конфиг:
hermes config edit
# И добавить блок вручную (см. формат YAML-списка ниже)

# Переключить
hermes config set model.provider custom:volc-coding
hermes config set model.default deepseek-v4-flash
```

**Формат YAML (вставить через `hermes config edit`):**
```yaml
custom_providers:
  - name: volc-coding
    base_url: https://ark.cn-beijing.volces.com/api/coding/v3
    api_key_env: VOLC_CODING_API_KEY
    api_mode: chat_completions
    skip_model_validation: true
    models:
      - deepseek-v4-flash
      - deepseek-v4-pro
      - doubao-seed-2.0-code
      - doubao-seed-2.0-pro
      - doubao-seed-2.0-lite
      - doubao-seed-code
      - minimax-m3
      - minimax-m2.7
      - glm-5.1
      - kimi-k2.6
      # DeepSeek-V3.2 — 即将下线, не добавлять
```

**Base URL:** `https://ark.cn-beijing.volces.com/api/coding/v3/v1` (OpenAI)

**Pitfall — `/v1` suffix обязателен.** Volcengine Coding API не имеет `/models` эндпоинта по пути `.../api/coding/v3/models`. Hermes при старте пытается проверить модели через `GET /models` и падает с ошибкой `could not reach this custom endpoint's model listing`. Фикс: добавить `/v1` в base_url → `https://ark.cn-beijing.volces.com/api/coding/v3/v1`. Тогда `/v1/models` работает корректно.

Подробнее о моделях, лимитах и ценах — `references/volc-coding-plan.md`.

### Проверка всех эндпоинтов (массовая диагностика)

Когда нужно проверить ВСЕ настроенные провайдеры разом — ключи лежат в .env, но не в shell env. Правильный порядок:

```bash
source ~/.hermes/.env  # загрузить ключи

# DeepSeek
curl -s -w "\nHTTP:%{http_code}" https://api.deepseek.com/v1/chat/completions \
  -H "Authorization: Bearer $DEEPSEEK_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"test"}],"max_tokens":10}'

# Kimi
curl -s -w "\nHTTP:%{http_code}" https://api.moonshot.cn/v1/chat/completions \
  -H "Authorization: Bearer $KIMI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"kimi-k2.6","messages":[{"role":"user","content":"test"}],"max_tokens":10}'

# Volc-Coding (через SOCKS5 если в Китае)
curl -s -w "\nHTTP:%{http_code}" \
  --socks5 127.0.0.1:1080 \
  https://ark.cn-beijing.volces.com/api/coding/v3/chat/completions \
  -H "Authorization: Bearer $VOLC_CODING_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"test"}],"max_tokens":10}'
```

**Без `source ~/.hermes/.env`** ключи не загрузятся в shell, даже если Hermes их видит — curl упадёт с 401 за Authentication header.

**Pitfalls:**
- `hermes config set custom_providers` сериализует массив в JSON-строку (`custom_providers: '[{...}]'`), а Hermes ожидает YAML-список (`custom_providers:\n  - name: ...`). Провайдер не появится в `/model` пока формат неправильный. Фикс: `hermes config edit` → записать YAML-список вручную.
- `skip_model_validation: true` обязателен (нет GET /v1/models)
- Нельзя через прямой API — только через AI coding tools
- Сейчас (до 30.06.2026): DeepSeek-V4-Pro, Kimi-K2.6, GLM-5.1 со скидкой 60%
