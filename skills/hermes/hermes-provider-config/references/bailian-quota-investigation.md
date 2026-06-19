# Bailian Quota Investigation

Как расследовать проблемы с квотой/балансом на Bailian (Alibaba Cloud DashScope).

## Симптомы

- API возвращает 403/ошибки
- В консоли Bailian значок `部分功能使用受限` (partial functionality restricted)
- Модели не отвечают, хотя бесплатная квота была

## Причина #1: Баланс в минусе (самое частое)

Даже копеечный долг (¥0.01+) блокирует ВСЕ API, включая бесплатные квоты.

**Проверка:**
1. Открыть `https://billing-cost.console.aliyun.com/home`
2. Смотреть карточку `账户可用额度` (Account Available Balance)
3. Если `¥ -X.XX 已欠费` — баланс в минусе

**Исправление:** пополнить через `充值汇款` (Recharge). Минимум ¥1 через Alipay.
После пополнения — обновить Bailian консоль (cache-busting: `&t=Date.now()`).

## Причина #2: Используется модель без бесплатной квоты

Bailian даёт 1M бесплатных токенов на ∼165 моделей, но **34 модели — платные** (post-paid). Если использовать их, каждый запрос списывает деньги.

**Проверка:**
1. Открыть `https://bailian.console.aliyun.com/cn-beijing?tab=model#/model-usage`
2. Вкладка `免费额度` (Free Quota)
3. Карточки: `额度充沛` (enough), `使用超50%`, `无免费额度模型` (NO free quota)
4. Нажать `查看详情` на карточке `无免费额度模型` — увидеть список платных моделей

**Модели БЕЗ бесплатной квоты (на июнь 2026):**
- `deepseek-v4-flash`
- `vanchin/deepseek-v4-pro`
- `kimi/kimi-k2.6`, `kimi/kimi-k2.5`
- `MiniMax/MiniMax-M3`, `MiniMax/MiniMax-M2.7`, `MiniMax/MiniMax-M2.5`, `MiniMax/MiniMax-M2.1`
- `qwen-deep-research`, `qwen-deep-research-2025-12-15`
- + ~24 других (всего 34)

**Безопасные модели (есть free quota 1M, expires 2026/09/04):**
- `qwen3.7-max` (осталось ~380K)
- `qwen3.7-plus` (осталось ~926K)
- `qwen3.6-plus/flash` (почти полные)
- `qwen3-vl-plus/flash`
- `glm-5`, `glm-4.7`
- `qwen-max`, `qwen-plus`
- и ~130 других

## Причина #3: Free quota исчерпана

Некоторые модели быстро расходуют квоту. `qwen3.7-max` на июнь 2026 использован на 62%.

**Проверка:** вкладка `免费额度` → таблица → колонка `免费额度剩余量`.

**Решение:** переключиться на модель с большим остатком (`qwen3.6-plus`, `qwen3.6-flash`).

## Профилактика

1. Включить `免费额度用完即停` (Stop when free quota exhausted) для каждой модели
2. Не использовать в списке `custom_providers` модели без free quota
3. Fallback providers — только на безопасные модели (qwen3.6-plus, glm-5)

## Использование в Hermes

```yaml
# config.yaml
custom_providers:
  - name: bailian-cn
    base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
    api_key_env: DASHSCOPE_API_KEY
    api_mode: chat_completions
    skip_model_validation: true
    models:
      - qwen3.7-max
      - qwen3.6-plus
      # НЕ добавлять: deepseek-v4-flash, kimi-k2.5, MiniMax-M2.5
```

## Техника: CDP для Bailian консоли

Bailian консоль грузит контент в iframe (`free.aliyun.com/smarter-engine`), невидимый для browser_snapshot. Использовать:

1. `browser_cdp(method='Target.getTargets')` — найти все вкладки
2. `browser_cdp(method='Target.activateTarget', params={'targetId': id})` — переключиться на вкладку Bailian
3. `browser_cdp(method='Runtime.evaluate', params={'expression': '...'}, target_id=id)` — выполнить JS внутри вкладки
4. Для кликов внутри iframe: `document.querySelector(...).dispatchEvent(new MouseEvent('click', {bubbles:true}))`
5. Для React controlled inputs: использовать `nativeInputValueSetter`
