# Hermes Cost Optimization

## DeepSeek Pricing (актуально на май 2026)

| Модель | Input (cache miss) | Input (cache hit) | Output |
|--------|-------------------|-------------------|--------|
| deepseek-v4-flash | $0.14/M | $0.0028/M (50x) | $0.28/M |
| deepseek-v4-pro | $1.74/M | $0.0145/M | $3.48/M |

`deepseek-chat` deprecated — теперь alias на v4-flash non-thinking mode.

## Стратегии экономии

### 1. Context Compression (уже включено)
- `compression.enabled: true`
- Сжимает историю при превышении 50% контекста
- Можно усилить: `threshold: 0.35`, `target_ratio: 0.15`

### 2. Context Caching
- DeepSeek автоматически кэширует повторяющиеся префиксы
- Cache hit: $0.0028/M (50x дешевле miss)
- Живёт ~5 минут без активности
- `prompt_caching.cache_ttl: 5m` — уже установлено

### 3. Отключение ненужных toolsets
Каждый включённый toolset добавляет схему в system prompt => больше токенов.
```bash
hermes tools disable <name>  # для неиспользуемых
```
Потенциально отключаемые: `spotify`, `image_gen`, `tts`, `vision`, `video`, `homeassistant`, `discord`, `yuanbao`

### 4. Auxiliary модели — на дешёвый провайдер
Заменить `auto` на конкретную дешёвую модель:
```yaml
auxiliary:
  compression:
    provider: deepseek
    model: deepseek-chat
```

### 5. `delegate_task` с дешёвой моделью для подзадач
```yaml
delegation:
  model: deepseek-chat
  provider: deepseek
```

### 6. Профили для разделения по сложности задач
```bash
hermes profile create cheap --clone  # дешёвая модель
hermes profile create pro --clone    # мощная для кода
```

### 7. Local model (0 токенов)
LM Studio на безголовом Mac — для простых рутин можно гонять локально:
```yaml
model:
  provider: openai
  base_url: http://192.168.2.2:1234/v1
```

### 8. `/compress` вручную
В середине длинной сессии — принудительная компрессия контекста.

### 9. `hermes chat -Q` (quiet mode)
Пропускает баннер, спиннер, превью тулов — меньше токенов в system prompt? (экономия незначительная)
