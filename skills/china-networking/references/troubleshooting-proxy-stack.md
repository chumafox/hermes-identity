# Диагностика многослойного прокси-стека

Когда у тебя sing-box (TUN) → SSH SOCKS5 → hysteria → pro → Shadowrocket → VPN, ошибка может быть на любом уровне.

## Как устроен стек

```
process (CLI/браузер)
  ├─ HTTP_PROXY=socks5h://127.0.0.1:1080 → SSH -D 1080 → pro→Shadowrocket→VPN→интернет
  │  (эксплицитный прокси для CLI, Go-тулов)
  └─ TUN (sing-box utun9) → SSH SOCKS5 :1080 → pro→Shadowrocket→VPN→интернет
     (системный трафик — браузеры, DNS, всё остальное)
```

## Пошаговая диагностика

### 1. Жив ли SSH SOCKS5?

```bash
lsof -i :1080 -P -n | grep LISTEN
# Если пусто — SSH туннель упал
# Если есть — смотрим дальше

curl -s --connect-timeout 5 -x socks5h://127.0.0.1:1080 https://httpbin.org/ip
# Если вернул IP не из Китая — прокси работает
```

### 2. Жив ли sing-box TUN?

```bash
pgrep -fl sing-box
# Должен быть процесс с `run -c /Users/.../sing-box-config.json`
# Если нет — перезапустить: sing-box run -c ~/sing-box-config.json

# Проверка TUN интерфейса
ifconfig utun9 2>/dev/null | grep "inet "
# Должен быть адрес 172.19.0.1/30
```

### 3. Почему CLI не видит интернет через TUN?

**Это нормально.** Sing-box в TUN-режиме не выставляет HTTP/SOCKS5 порт. CLI-тулы (особенно Go-бинарники) могут не проходить через TUN, потому что:
- Loopback трафик (127.0.0.1) не идёт через TUN
- Процессы, запущенные до старта TUN, не маршрутизируются
- Некоторые тулы используют свои DNS-резолверы, bypass TUN

**Решение:** всегда явно ставить `HTTP_PROXY=socks5h://127.0.0.1:1080` для CLI.

### 4. Почему `HTTP_PROXY=socks5h://` не всегда помогает?

Проверить что прокси доступен:
```bash
# Через SOCKS5 напрямую (самый надёжный способ)
curl --socks5-hostname 127.0.0.1:1080 https://httpbin.org/ip

# Через HTTP_PROXY
HTTP_PROXY=socks5h://127.0.0.1:1080 curl https://httpbin.org/ip

# Через HTTP-мост (если стоит tinyproxy/privoxy)
HTTP_PROXY=http://127.0.0.1:8888 curl https://httpbin.org/ip
```

Если `--socks5-hostname` работает, а `HTTP_PROXY` — нет, то это баг конкретного Go-бина (см. go-cli-proxy.md → issue #113).

### 5. Как проверить GitHub/Google доступ

```bash
# GitHub API (через socks5)
curl --socks5-hostname 127.0.0.1:1080 -s -o /dev/null -w "%{http_code}" https://api.github.com

# Google OAuth
curl --socks5-hostname 127.0.0.1:1080 -s -o /dev/null -w "%{http_code}" https://oauth2.googleapis.com/token

# Google Gemini API
curl --socks5-hostname 127.0.0.1:1080 -s -o /dev/null -w "%{http_code}" https://generativelanguage.googleapis.com
```

### 6. Проверка на pro (удалённая сторона)

```bash
ssh admin-remote "curl -s --max-time 10 https://github.com"
# Если таймаут — проблема в Shadowrocket на pro, не в туннеле
```

## Ошибка "token exchange failed"

```
token exchange failed: Post "https://oauth2.googleapis.com/token": dial tcp 172.217.216.95:443: i/o timeout
```

Означает что:
1. DNS резолв прошёл (172.217.216.95 — правильный IP Google)
2. TCP SYN отправлен на 443 порт
3. Ответа нет (таймаут)

**Причина:** процесс (agy) использует системный сокет, который не идёт через TUN (loopback), и не имеет HTTP_PROXY.

**Фикс:**
```bash
export HTTP_PROXY=socks5h://127.0.0.1:1080
export HTTPS_PROXY=socks5h://127.0.0.1:1080
# ИЛИ если не помогает:
export ALL_PROXY=socks5://127.0.0.1:1080
# Тогда запустить agy
```

## Общий чеклист

Если "интернет не работает":
- [ ] SOCKS5 порт 1080 слушается? `lsof -i :1080`
- [ ] sing-box запущен? `pgrep -f sing-box`
- [ ] shadowrocket на pro запущен? `ssh admin-remote 'sr status'`
- [ ] Доступ к Google через SOCKS? `curl --socks5-hostname 127.0.0.1:1080 -I https://google.com`
- [ ] Speedtest на pro? `ssh admin-remote 'speedtest --secure'`
