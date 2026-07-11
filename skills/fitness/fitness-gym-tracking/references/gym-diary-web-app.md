# Gym Diary Web App

Location: `~/Projects/active/gym-diary/`

A local web app companion to the markdown-based tracking system. Provides a visual calendar, dropdown-based exercise logging, volume calculation, and SVG progression charts.

## How to Use

```bash
cd ~/Projects/active/gym-diary
npm run dev       # Dev server on localhost:5173
npm run build     # Production build to dist/
```

Data is stored in browser localStorage under key `gym-diary-data`.

## Vite Bindings

If `rolldown` native binding fails on macOS 26.5+:

```bash
rm -rf node_modules package-lock.json && npm install
```

## Exercise List

Exercises are defined in `src/data.ts` → `EXERCISES` array, categorised by muscle group matching the ШРЕДЕР split:

- ГРУДЬ: Жим наклонный (штанга), Жим Смит грудь, Отжимания на кольцах (вертикальные), Отжимания на кольцах (горизонтальные)
- СПИНА: Тяга штанги в наклоне, Тяга к подбородку, Подтягивания на кольцах (обратным хватом)
- НОГИ: Приседания в Смите, Становая тяга
- ПЛЕЧИ: Армейский жим, Махи гантелями в наклоне (задние дельты)
- РУКИ: Бицепс штанга, Трицепс Смит
- ДОП: Пресс на скамье с блином

## Features

- Calendar with workout-day highlighting
- Day view with smart recommendation (last workout weight/reps)
- Weight dropdown 0-150 кг × 2.5 step
- Reps dropdown 1-20
- Rest dropdown: 30с, 60с, 90с, 2м, 2.5м, 3м, 4м, 5м
- Volume: weight × reps, per exercise and total per day
- SVG progression chart (click exercise name)
