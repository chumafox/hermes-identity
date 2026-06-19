# Aliyun Bailian (阿里云百炼) — Setup & Free Quota

Aliyun Bailian = Alibaba Cloud Model Studio (DashScope). Даёт бесплатные квоты новым пользователям.

## Free Tier

- Регистрация: бесплатно, квота после первого входа в консоль
- Срок: 90 дней (для новых после 2025-09-08)
- Лимит: ~1M токенов на модель
- **165 моделей с квотой, 35 без квоты** (платные, обновлено июнь 2026)
- "用完即停" (стоп при исчерпании) **ВЫКЛЮЧЕН** по умолчанию
- **Отслеживание квоты:** только через консоль (`#/model-usage/free-quota`). API-эндпоинта нет.

## ⚠️ Ключевое: deepseek-v4-flash НЕ бесплатный

deepseek-v4-flash — модель №1 по использованию, но у неё **НЕТ бесплатной квоты** на Bailian. Каждый запрос идёт через post-paid (pay-as-you-go). Использование через Hermes (custom:bailian-cn) → деньги.

**Как не платить:** использовать qwen3.6-plus, qwen3.6-flash или qwen3.7-max — у них есть 1M бесплатных токенов.

## Полный список платных моделей (без free quota) — 35 шт

| Модель | Примечание |
|--------|-----------|
| deepseek-v4-flash | Самая частая ошибка |
| vanchin/deepseek-v4-pro | сторонний провайдер |
| kimi/kimi-k2.6 | сторонний провайдер |
| kimi/kimi-k2.5 | сторонний провайдер |
| MiniMax/MiniMax-M3 | платный, без free quota |
| MiniMax/MiniMax-M2.7 | платный, без free quota |
| MiniMax/MiniMax-M2.5 | платный, без free quota |
| MiniMax/MiniMax-M2.1 | платный, без free quota |
| qwen-deep-research | платный |
| qwen-deep-research-2025-12-15 | платный |
| ZHIPU/GLM-5 | ПЛАТНЫЙ (с префиксом ZHIPU/) |
| ZHIPU/GLM-5.1 | ПЛАТНЫЙ (с префиксом ZHIPU/) |
| + ~23 остальных | siliconflow/* и прочие сторонние |

**Правило быстрой проверки:** модели с префиксом `vanchin/`, `siliconflow/`, `kimi/`, `MiniMax/`, `ZHIPU/` — почти всегда платные. Модели `qwen-*` и `glm-*` (без префикса) — почти всегда бесплатные.

## Текущее состояние free quota (актуализируй через CDP каждый раз)

Для актуальных данных всегда проверяй консоль через CDP (старые цифры устаревают за дни):

```javascript
// Извлечь таблицу → Bailian console tab "大语言模型" + "免费额度":
JSON.stringify(Array.from(document.querySelectorAll('table tbody tr'))
  .map(tr => Array.from(tr.children).map(c => c.innerText.replace(/\n/g,' ').trim())));
```

Сортировка таблицы — клик по заголовку столбца «免费额度剩余量».
Поиск по модели — текстовое поле перед таблицей.

### Основные модели с квотой (июнь 2026)
- **qwen3.7-plus**: 926K/1M (~7%)
- **qwen3.6-plus**: 984K/1M (~2%)  
- **qwen3.6-flash-2026-04-16**: 894K/1M (~11%)
- **glm-5, glm-4.7, glm-5.1, glm-4.6**: все 1M
- **qwen-max, qwen-plus, qwen-math-turbo**: все 1M

### ⚠️ qwen3.7-max — частая путаница
Метка статуса: **«不支持开启»** (не поддерживает авто-стоп), НО квота ЕСТЬ (1M). 
Это значит "нет кнопки 用完即停", а не "нет free quota". Не путать с моделями где статус "无免费额度"!

## Расследование: что сожрало квоту/деньги

Когда API перестал работать, а free quota ещё есть:

### Шаг 1 — Проверить баланс
```
https://billing-cost.console.aliyun.com/home
```
Смотрим "账户可用额度" — если отрицательный, API заблокирован даже для free моделей.

### Шаг 2 — Проверить free quota
```
bailian.console.aliyun.com → tab=model → #/model-usage → вкладка "免费额度"
```

### Шаг 3 — Посмотреть usage stats
```
bailian.console.aliyun.com → tab=model → #/model-usage → вкладка "用量统计"
```
Показывает Top-10 моделей по количеству вызовов.

### Шаг 4 — Если баланс отрицательный
Пополнить через Alipay (支付宝), минимум ¥1. После пополнения API разблокируется.

## Логин через Brave

Аккаунт в Safari → сессия не переносится. Логин в Brave:

```javascript
browser_navigate(url='https://bailian.console.aliyun.com/?tab=model#/model-usage/free-quota')
// Нажать "立即登录", потом "主账号登录"
```

После логина: "模型免费额度正在发放" с progress bar. Ждать 10-30 сек.

## Навигация по SPA

Bailian — qiankun SPA. Контент в iframe'ах, Hash-роутинг.

**Техника извлечения данных из таблиц:**

```javascript
// 1. Получить все строки таблицы (без пагинации в таб-е "大语言模型")
var rows = document.querySelectorAll('table tbody tr');
JSON.stringify(Array.from(rows).map(tr => {
  return Array.from(tr.children).map(c => c.innerText.trim());
}));

// 2. Статус текущей страницы пагинации
document.querySelector('.arco-pagination-item-active')?.innerText;

// 3. Поиск React store (обычно null в qiankun SPA)
window.__INITIAL_STATE__; // обычно null
```

**Техника извлечения данных из iframe через CDP:**

```javascript
// 1. Найти iframe frame_id через browser_snapshot
// 2. Забрать контент iframe
browser_cdp(
  frame_id='<frame_id>',
  method='Runtime.evaluate',
  params={expression: "document.body.innerText.substring(0,5000)"}
)
```

## API Key

Сайдбар → API Key → "创建API Key" → скопировать ключ.

Ключ в `.env`:
```bash
echo 'DASHSCOPE_API_KEY=sk-...' >> ~/.hermes/.env
```

## Провайдеры в Hermes

### custom provider `bailian-cn`
```yaml
custom_providers:
  - name: bailian-cn
    base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
    api_key_env: DASHSCOPE_API_KEY
    api_mode: chat_completions
    skip_model_validation: true
    models:
      - qwen3.7-max
      - qwen3.6-plus
```

### Fallback цепочка
```yaml
fallback_providers: [
  {"provider": "custom:bailian-cn", "model": "qwen3.6-plus"},
  {"provider": "kimi", "model": "kimi-k2.6"},
  {"provider": "nous", "model": "stepfun/step-3.7-flash:free"}
]
```

## 用完即停 (Free Quota Stop) — механика

Страница: `#/model-usage` → вкладка «免费额度». Фиолетовая кнопка **«批量操作免费额度用完即停»** в правом верхнем углу таблицы моделей.

**Дропдаун (2 опции):**

| Опция | Действие |
|-------|---------|
| **批量开启** | Выключить «用完即停» для выбранных моделей → разрешить платный режим после исчерпания квоты |
| **批量关闭** | Включить «用完即停» для выбранных моделей → ТОЛЬКО бесплатная квота, 403 при исчерпании |

**⚠️ Ключевое предупреждение (из алерта на странице):**

> «免费额度用完即停：仅消耗平台赠送的免费额度，免费额度用尽后平台将自动停止服务（返回403错误：AllocationQuota.FreeTierOnly.），避免产生免费额度以外的费用。若您希望在免费额度用尽后仍继续使用模型服务，并根据实际产生的用量付费，请您保持本功能是关闭状态。」

> «重要提醒：当您账户内的免费额度未完全消耗时，您可以开启本功能。一旦功能开启，若您需要关闭本功能，需要在免费额度完全消耗后再进行关闭»

**Итог:**
- `批量关闭` = защита от платного режима. Включил → нельзя выключить пока квота не исчерпана.
- `批量开启` = разрешить платный режим (снимает защиту).
- По умолчанию **ВЫКЛЮЧЕНО** (модели могут уйти в платный режим).

**qwen3.7-max:** метка «不支持开启» — кнопка 用完即停 недоступна для этой модели. Квота ЕСТЬ (1M), но авто-стоп не поддержан.

## Pitfalls

- **Баланс -¥ блокирует API полностью**, включая free quota модели.
- **Минимальное пополнение** — ¥1 через Alipay.
- **Минутная задержка** обновления квот в консоли.
- **deepseek-v4-flash** — платный на Bailian. Не использовать через custom:bailian-cn.
- **qwen3.7-max** имеет free quota (1M), но метка "不支持开启" ≠ "нет квоты" = "нет авто-стопа".
- **ZHIPU/GLM-5** и **ZHIPU/GLM-5.1** — платные (с префиксом ZHIPU/). Бесплатные версии: `glm-5`, `glm-5.1`.
- **Модели сторонних провайдеров** (`vanchin/`, `siliconflow/`, `kimi/`, `MiniMax/`) — почти всегда платные.
- **Пагинация**: таблица "大语言模型" показывает все записи сразу (20+ строк). Для других категорий может быть пагинация.
- **用完即停 необратимо до исчерпания квоты** — включил → выключить можно только когда квота = 0.