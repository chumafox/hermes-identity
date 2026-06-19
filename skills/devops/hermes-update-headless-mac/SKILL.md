---
name: hermes-update-headless-mac
description: "Обновление Hermes Agent на безголовом Mac (pro, Китай, без прямого доступа к GitHub) через git bundle и SSH с экранного Mac (dispo)"
tags: ["devops", "hermes", "mac-to-mac", "china-networking"]
---

# Hermes Update на безголовом Mac (pro)

Безголовый Mac (pro, 192.168.103.70, Китай, пользователь `admin`). Прокси через Shadowrocket TUN (utun4), SOCKS5 на 1082 не работает. `hermes update` может падать с `CONNECT tunnel failed, response 503` или `SSL_ERROR_SYSCALL`.

## Pre-check: диагностика перед bundle

Сначала проверить, работает ли вообще интернет через TUN:

```bash
# Прямой доступ — Shadowrocket TUN перехватывает на уровне ядра
curl -s -o /dev/null -w "github: %{http_code} (%{time_total}s)\n" --max-time 10 https://github.com

# Если 200 — интернет есть, проблема в git прокси
```

### Главная ловушка: ЛОКАЛЬНЫЙ git config

Если прямой доступ работает (curl 200), но `hermes update` падает с 503 — проверь ЛОКАЛЬНЫЙ конфиг репозитория:

```bash
cd ~/.hermes/hermes-agent
git config --local --list | grep proxy
# Если показывает http.proxy — вот причина!
git config --local --unset http.proxy
git config --local --unset https.proxy
hermes update
```

**Локальный `.git/config`** переопределяет глобальный `~/.gitconfig` и env-переменные. На pro в `.git/config` висел `http.proxy=http://127.0.0.1:1082` — порт, на котором SOCKS5 не работает, и git пытался делать HTTP CONNECT через него, получая 503.

### Shadowrocket TUN: что работает, что нет

На pro **Shadowrocket** (не V2rayU), а не V2rayU:

| Механизм | Статус | Как проверить |
|----------|--------|--------------|
| TUN (utun4) — прямой доступ | **Работает** | `curl https://github.com` — 200 |
| SOCKS5 127.0.0.1:1082 | **Не работает** | `curl -x socks5h://127.0.0.1:1082` — CONNECT timeout |
| tinyproxy (homebrew) | Установлен | `ps aux \| grep tinyproxy` |

**Правило:** не ставить git proxy вообще — TUN сам перехватывает трафик. `hermes update` работает напрямую.

### Быстрая проверка через geoip

`geoip` на pro работает напрямую (ip-api.com доступен из Китая):

```bash
geoip github.com
# IP: 140.82.xxx.xxx
# Страна: United States (US)
# Провайдер: GitHub, Inc.
```

Если `geoip` отвечает — интернет есть, проблема в git proxy.

## Когда всё-таки нужен bundle

Если прямой доступ не работает (curl 000) — например, Shadowrocket выключен или TUN не активен. Решение — git bundle через SSH с dispo.

### 1. Создать bundle на dispo

```bash
cd ~/.hermes/hermes-agent
git bundle create /tmp/hermes-update.bundle --since="7 days ago" HEAD
# или --since="1 week ago" для более широкого захвата
```

### 2. Скопировать на pro

```bash
scp -i ~/.ssh/id_ed25519_headless /tmp/hermes-update.bundle admin@192.168.103.70:/tmp/
```

### 3. Применить на pro

```bash
ssh -i ~/.ssh/id_ed25519_headless admin@192.168.103.70 '
cd ~/.hermes/hermes-agent

# stash локальных изменений (если есть)
git stash

# fetch из bundle
git fetch /tmp/hermes-update.bundle

# merge
git merge FETCH_HEAD

# очистка
rm /tmp/hermes-update.bundle
'
```

## Pitfalls

- **Локальные изменения**: `git merge` упадёт с "Your local changes would be overwritten". Перед merge делать `git stash`.
- **Stash**: После обновления stash висит — нужно зайти на pro и `git stash pop` если изменения ещё актуальны.
- **Proxy в git config**: `git config --global http.proxy` может указывать на мёртвый порт. Сбросить: `git config --global --unset http.proxy && git config --global --unset https.proxy`. Но это не влияет на bundle — bundle работает через SSH, не через HTTP.
- **Bundle слишком старый**: Если прошло >недели, bundle может не содержать всех нужных коммитов. Увеличить `--since`.
- **SSH ключ**: На dispo ключ `~/.ssh/id_ed25519_headless`, на pro пользователь `admin`.

## Когда bundle не нужен

Если `curl https://github.com` выдаёт 200 (через TUN), а `hermes update` падает — проблема в git proxy. Удали локальный proxy из `.git/config` и `hermes update` сработает напрямую:

```bash
cd ~/.hermes/hermes-agent
git config --local --unset http.proxy 2>/dev/null
git config --local --unset https.proxy 2>/dev/null
hermes update
```
