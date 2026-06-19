---
name: fitness-gym-tracking
description: "Gym workout tracking: weekly plans, daily logs, progression tracking. Directory ~/shelf/gym/ with training_plan.md, daily YYYY-MM-DD.md logs, and weekly-YYYY-MM-DD.md plans."
tags: [fitness, gym, workout, tracking, progression, logging]
---

# Fitness / Gym Workout Tracking

Workout tracking system for the user's home gym. Logs live in `~/shelf/gym/`.

## Directory Structure

```
~/shelf/gym/
├── training_plan.md       # Полная программа: питание + тренировки (5 дней/нед)
├── weekly-YYYY-MM-DD.md   # Недельный план с прогрессией
├── YYYY-MM-DD.md          # Дневник конкретной тренировки
```

## Workflow

### 1. Weekly Plan

Create at start of week: `~/shelf/gym/weekly-YYYY-MM-DD.md`

Template:
```markdown
# Неделя DD-MM YYYY

**Прогрессия:** [что добавить вес на след. тренировке]

---

## ПН — НОГИ / ЯГОДИЦЫ (тяжёлый)
- [ ] Приседания Смит
- [ ] Румынская тяга
- [ ] Hip Thrust
- [ ] Становая тяга
- [ ] Выпады в проходке

## ВТ — ВЕРХ А (жимы + плечи)
- [ ]

## СР — КАРДИО (интервалы вело)
- [ ]

## ЧТ — НОГИ / ЯГОДИЦЫ (лёгкий)
- [ ]

## ПТ — ВЕРХ Б (спина + брусья)
- [ ]
```

### 2. Daily Log

File: `~/shelf/gym/YYYY-MM-DD.md`

Each exercise gets a table:

```markdown
## N. Упражнение
| Подход | Вес | Повторения | Тип |
|--------|-----|------------|-----|
| 1 | XX кг | N | Разминка |
| 2 | XX кг | N | Рабочий |
| 3 | XX кг | N | Рабочий |
```

For walking lunges with dumbbells:
```markdown
## N. Выпады в проходке (гантели)
| Подход | Вес (каждая) | Шагов | На ногу | Тип |
|--------|-------------|-------|---------|-----|
| 1 | 10 кг | 12 | 6 | Рабочий |
```

### 3. Progression Tracking

Add at bottom of daily log:
```markdown
- **Прогрессия:** след. тяжёлый день ног — приседания XX кг, румынская XX кг, выпады XX кг
- **Пропущено:** [какие упражнения не делал]
```

### Progression Rules (from training_plan.md)

- **Силовые (4-6 повторений):** все подходы по 6 → +2.5 кг на след. тренировке
- **Хотя бы один подход <4 повторений** → остаёшься на этом весе
- **Приседания Смит:** +2.5 кг каждые 1-2 недели
- **Румынская тяга:** +5 кг когда все 4×6 чисто
- **Выпады:** +2 кг на гантель

### Training Plan Reference

The full plan is at `~/shelf/gym/training_plan.md`. Key schedule:
- ПН — НОГИ / ЯГОДИЦЫ (тяжёлый)
- ВТ — ВЕРХ А (жимы + плечи) + кардио
- СР — КАРДИО (интервалы вело)
- ЧТ — НОГИ / ЯГОДИЦЫ (лёгкий)
- ПТ — ВЕРХ Б (спина + брусья) + кардио
- СБ/ВС — отдых

### Smith Machine Note

Вес грифа Смита не учитывается в записях — только вес блинов.
