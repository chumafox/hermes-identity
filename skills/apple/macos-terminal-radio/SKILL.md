---
name: macos-terminal-radio
description: Играть интернет-радио через терминал macOS — ffplay/mpv. Поиск рабочих стрим-URL, запуск в фоне, остановка.
---

# macos-terminal-radio

## Когда использовать
Пользователь просит включить радио / музыку / smooth jazz / любой интернет-стрим в терминале.

## Проверка инструментов

```bash
which ffplay mpv afplay 2>/dev/null
```

`ffplay` (из ffmpeg) — предпочтительный. Если нет:
```bash
brew install ffmpeg
```

## Проверка стрима перед запуском

Всегда проверяй что стрим отвечает и отдаёт аудио, прежде чем запускать в background:

```bash
ffprobe -v quiet -print_format json -show_streams "<URL>"
```

Должен вернуть JSON с `codec_name` (mp3, aac, ogg и т.д.) и `sample_rate`.

Если стрим не отвечает из Китая (таймаут), пробовать альтернативы.

## Известные рабочие стрим-URL (доступны из Китая)

### SomaFM станции
- Space Station (lounge): `https://ice3.somafm.com/spacestation-128-mp3`
- Sonic Universe (ambient/jazz): `https://ice3.somafm.com/sonicuniverse-128-mp3`
- Groove Salad (chillout): `https://ice3.somafm.com/groovesalad-128-mp3`
- GS Classic: `http://ice1.somafm.com/gsclassic-128-mp3`

### Smooth Jazz
- Smooth Jazz 24/7 (RadioNav): `http://naxos.cdnstream.com/1255_128`
  (128kbps MP3, 44100 stereo)

### Не работают из Китая
- Sky.fm / sky.fm/smoothjazz — CDN таймаутит
- radioparadise.com — таймаутит

## Запуск

```bash
ffplay -nodisp -volume 30 "<URL>"
```

Параметры:
- `-nodisp` — без видеоокна, только звук
- `-volume 30` — громкость (0-100)

Запускай в **background** через `terminal(background=true)`:

```bash
ffplay -nodisp -volume 30 "<URL>" 2>/dev/null
```

Сохранённый `session_id` позволяется остановить:
```
process action=kill session_id=proc_xxx
```

## Остановка

Убить процесс через process tool или:
```bash
pkill ffplay
```

## Если ffplay нет, но есть mpv
```bash
mpv --no-video --volume=30 "<URL>"
```

## Pitfalls
- SomaFM некоторые станции могут быть недоступны из Китая — проверять через ffprobe перед запуском
- Sky.fm CDN не работает из Китая (таймаут) — не предлагать
- Некоторые стримы на HTTP (не HTTPS) — пользователь может получить security warning от системы, но ffplay работает
- Не запускать в foreground — блокирует терминал. Всегда background=true
- `2>/dev/null` чтобы не засорять вывод (ffplay шумит в stderr информацией о буфере)
