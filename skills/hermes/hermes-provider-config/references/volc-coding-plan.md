# Volcengine Coding Plan (火山引擎)

## Общая информация

- **Провайдер:** ByteDance's Volcengine (火山引擎)
- **Тип доступа:** Coding Plan подписка (не прямой API)
- **Endpoint:** `https://ark.cn-beijing.volces.com/api/coding/v3` (OpenAI-совместимый)
- **Альтернативный endpoint:** `https://ark.cn-beijing.volces.com/api/coding` (Anthropic-совместимый)
- **API key env:** `VOLC_CODING_API_KEY` (формат: `ark-xxxxxxxxxx`)
- **Требуется `skip_model_validation: true`** (нет GET /v1/models)
- **Работает через SOCKS5 прокси из Китая** (internet_pro порт 1080)

## Тарифы (июнь 2026)

| План | Цена | Для кого |
|------|------|----------|
| Coding Plan Lite | 40元/мес | Персональное, средняя интенсивность |
| Coding Plan Pro | 200元/мес | Высокая интенсивность, сложные проекты |

**Промо-код на 95折:** `36JPDTAT`

## Механика квот

В отличие от Bailian (общий месячный пул), Volcengine использует **rolling-окна**:

| Окно | Лимит Lite (~эквивалент) |
|------|--------------------------|
| 5-часовое | ~1200 запросов / ~10M токенов (rolling, от первого запроса) |
| Недельное | Сбрасывается каждый понедельник 00:00 |
| Месячное | Сбрасывается 1-го числа каждого месяца |

- При исчерпании 5-часового окна — сервис стоп до следующего окна
- Pay-as-you-go fallback НЕТ (в отличие от прямого API)
- Квота общая на все AI coding инструменты (Claude Code, OpenCode, Cursor и т.д.)

## Коэффициенты расхода квоты (抵扣系数)

Модели расходуют квоту с разной скоростью. От экономичных к прожорливым:

| Уровень | Модели | Комментарий |
|---------|--------|-------------|
| 🟢 Низкий | `deepseek-v4-flash`, `doubao-seed-2.0-lite`, `doubao-seed-code` | Повседневные задачи, 80% запросов |
| 🟡 Средний | `doubao-seed-2.0-code`, `doubao-seed-2.0-pro`, `minimax-m3` | Когда нужно качество получше |
| 🔴 Высокий | `deepseek-v4-pro`, `kimi-k2.6`, `glm-5.1`, `minimax-m2.7` | Только для сложных задач |

**Акция до 30.06.2026:** deepseek-v4-pro, kimi-k2.6, glm-5.1 — **4折 (60% скидка)** коэффициента. В период акции их расход = ~40% от обычного.

## Модели: подробно с бенчмарками

### Doubao-Seed-2.0-Code (ByteDance)
*Релиз:* 14.02.2026. *Контекст:* 128K. *Мультимодальная:* да.
- LiveCodeBench v6: **87.8**
- SWE-bench Verified: **76.5**
- Специализация: agentic programming, отладка, frontend, code review
- Сильная сторона: Seed 2.0 Agent + VLM, понимание изображений в контексте кода
- Расход: средний (🟡)

### Doubao-Seed-2.0-Pro (ByteDance)
*Флагманская универсальная.* *Мультимодальная:* да.
- AIME 2025: **98.3**
- Для сложных multi-step задач: длинные цепочки рассуждений, структурная генерация
- Мультимодальное понимание, длинный контекст
- Расход: средний (🟡)

### Doubao-Seed-2.0-Lite (ByteDance)
*Баланс качества и скорости.* *Мультимодальная:* да.
- AIME 2025: **93**
- Production-grade: неструктурированные данные, контент, поиск, аналитика
- Самая экономичная из Doubao-Seed 2.0
- Расход: низкий (🟢)

### Doubao-Seed-Code (ByteDance)
*256K контекст.* *Мультимодальная:* да.
- Оптимизирована для Agentic Programming
- Terminal-Bench, SWE-Bench-Verified-Openhands, Multi-SWE-Bench-Flash-Openhands
- Предшественник Doubao-Seed-2.0-Code, но всё ещё актуальна
- Расход: низкий (🟢)

### MiniMax-M3 🥇
*Релиз:* 01.06.2026. *Open-weights.* *Контекст:* **1M токенов.** *Мультимодальная:* да.
- SWE-bench Pro: **59.0%** (выше GPT-5.5 и Gemini 3.1 Pro по кодингу)
- BrowseComp: **83.5** (выше Claude Opus 4.5)
- AAI Coding Index: **лучшая open-source модель** — выше Kimi-K2.6, GLM-5.1, DeepSeek-V4-Pro
- Лучший выбор для сложного кодинга в рамках Coding Plan
- Расход: средний (🟡) — но качество оправдывает

### MiniMax-M2.7 (MiniMax)
- Agent Harness, Agent Teams, Skills, Tool calling
- Для сложных multi-agent сценариев
- M3 почти во всём лучше — используй M3 если доступен
- Расход: высокий (🔴)

### GLM-5.1 (Zhipu AI)
*Open-source.* *Контекст:* 200K токенов.
- Конкурент Kimi-K2.6
- Сильное reasoning, open-source сообщество
- До 30.06 — со скидкой 4折 (расход как у среднего уровня)
- Расход: высокий (🔴), со скидкой — средний (🟡)

### Kimi-K2.6 (Moonshot AI)
*Контекст:* 256K токенов.
- Конкурент GLM-5.1, чуть лучше по кодингу
- Сильное reasoning
- До 30.06 — со скидкой 4折
- Расход: высокий (🔴), со скидкой — средний (🟡)

### DeepSeek-V4-Flash
- **Сверхнизкий** коэффициент расхода (самая экономичная)
- Быстрый, подходит для 80% повседневных задач
- Default: thinking mode ON (можно отключить)
- Расход: очень низкий (🟢)

### DeepSeek-V4-Pro
- Agent-способности сильнее Flash, мировые знания
- Default: thinking mode ON
- До 30.06 — со скидкой 4折
- Расход: высокий (🔴), со скидкой — средний (🟡)

## Иерархия по качеству кодинга

```
1. MiniMax-M3 🥇
2. DeepSeek-V4-Pro / Kimi-K2.6
3. Doubao-Seed-2.0-Code / GLM-5.1 / MiniMax-M2.7
4. DeepSeek-V4-Flash / Doubao-Seed-2.0-Pro
5. Doubao-Seed-2.0-Lite / Doubao-Seed-Code (повседневка)
```

## Рекомендации по использованию

| Сценарий | Модель |
|----------|--------|
| Быстрые ответы, рефакторинг | `deepseek-v4-flash` |
| Сложный код, архитектура | `minimax-m3` |
| Agent-сценарии, tool calling | `minimax-m3` или `doubao-seed-2.0-code` |
| Reasoning, длинные контексты | `doubao-seed-2.0-pro` |
| Максимум качества (до 30.06) | `deepseek-v4-pro` (со скидкой) |

## Конфигурация Hermes

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
```

## Быстрая проверка

```bash
source ~/.hermes/.env
curl -s -w "\nHTTP:%{http_code}" \
  --socks5 127.0.0.1:1080 \
  https://ark.cn-beijing.volces.com/api/coding/v3/chat/completions \
  -H "Authorization: Bearer $VOLC_CODING_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"test"}],"max_tokens":10}'
```

## Известные проблемы

- **Дублирующиеся `models:` в custom_providers** — при смешивании ручного редактирования и `hermes config set` YAML-список может перезаписываться JSON-строкой. Симптом: провайдер виден в `/model` но с 0 моделей. Диагностика: `grep -n 'models:' ~/.hermes/config.yaml`. Фикс: `sed -i '' 'N,Nd' ~/.hermes/config.yaml` (N — строка с дубликатом).
- **Не запутать с Bailian Coding Plan** — Bailian тоже имеет Coding Plan (200元/мес), но с другой механикой квот (месячный пул) и другим набором моделей.
- **В Китае требуется SOCKS5** — Volcengine endpoint доступен, но для curl из терминала может потребоваться `--socks5 127.0.0.1:1080`.
