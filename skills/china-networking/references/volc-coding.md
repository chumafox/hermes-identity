# Volc Engine / Volc Coding (火山引擎)

## Provider Config

Провайдер для моделей Volc Engine через API Coding.

```yaml
# В config.yaml
custom_providers:
  - name: volc-coding
    base_url: https://ark.cn-beijing.volces.com/api/coding/v3/v1
    api_key_env: VOLC_CODING_API_KEY
    api_mode: chat_completions
    skip_model_validation: true
    models:
      - deepseek-v4-flash
      - deepseek-v4-pro
```

## Важно: активация моделей

Модели нужно **активировать в консоли** Volc Engine, иначе — 404:
```
{"error":{"code":"ModelNotOpen","message":"Your account X has not activated the model Y."}}
```

**Где активировать:** https://console.volcengine.com/ark/region:ark+cn-beijing/model
→ Найти модель → **Try now** → активировать.

## Title Generation 404

При переключении на volc-coding модель, title_generation посылает aux-запрос на тот же endpoint и получает 404. **Решение:** отключить title_generation или настроить на другой провайдер:

- Отключить: `auxiliary.title_generation.provider: ''`
- Или настроить на `custom:deepseek-fallback` (sk-ключ)

## Эндпоинты

- **API Coding:** `https://ark.cn-beijing.volces.com/api/coding/v3/v1` — кастомный, может не поддерживать все OpenAI операции
- **Standard Ark API:** `https://ark.cn-beijing.volces.com/api/v3` — стандартный OpenAI-совместимый

## Тестирование

```bash
NO_PROXY="*" curl -s https://ark.cn-beijing.volces.com/api/v3/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $VOLC_CODING_API_KEY" \
  -d '{"model":"<model-name>","messages":[{"role":"user","content":"ok"}],"max_tokens":5}'
```
