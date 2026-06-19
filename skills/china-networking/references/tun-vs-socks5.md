# TUN vs SOCKS5 Proxy

На безголовом Mac в Китае часто работает **TUN-режим** (Shadowrocket, V2rayU) — перехват трафика на уровне ядра. SOCKS5-порт может не работать.

## Диагностика

```bash
# Проверка TUN:
ifconfig utun4 | grep "inet "    # если есть IP — TUN активен

# Прямой доступ (через TUN):
curl -s -o /dev/null -w "%{http_code}" --max-time 10 https://github.com

# Проверка SOCKS5:
curl -x socks5h://127.0.0.1:1082 -s -o /dev/null -w "%{http_code}" --max-time 5 https://github.com
```

## Правило

Если прямой доступ (через TUN) даёт 200 — **не используй git proxy вообще**. TUN сам перехватывает трафик. `git config --global --unset http.proxy` и `git pull` пойдёт напрямую.

## Признаки мёртвого SOCKS5 при живом TUN

- `lsof -i :1080` пусто
- `curl -x socks5h://127.0.0.1:1082` → 000 (timeout)
- Но `curl https://github.com` → 200 (идёт через TUN)

## TUN жив, ICMP проходит, но TCP/HTTPS не работает

Самый хитрый кейс — Shadowrocket TUN активен, ping до 8.8.8.8 проходит (0.3ms), но curl на любой HTTPS сайт даёт `000` timeout или `SSL_ERROR_SYSCALL`.

**Причина:** VPN-нода Shadowrocket отвалилась, но TUN интерфейс (utun4) остался висеть. ICMP пакеты проходят через TUN напрямую, а TCP перехватываются TUN и пытаются уйти через мёртвую ноду.

**Диагностика:**
```bash
# Если это даёт 000, а ping работает — нода отвалилась
curl -s --max-time 10 https://github.com

# Проверить статус подключения Shadowrocket
scutil --nc status "Shadowrocket" 2>/dev/null | head -3
```

**Фикс:** переподключить Shadowrocket (через GUI или CLI):
```bash
scutil --nc restart "Shadowrocket" 2>/dev/null
sleep 5
# Проверить
curl -s --max-time 10 https://github.com
```

## Туннель висит но порты не слушают

SSH-туннель (`ssh -D 1080`) может показывать "Master running" через `ssh -S /tmp/internet_pro.socks -O check`, но порт 1080 не слушает. Причина: удалённый хост (admin-remote) сменил IP или DNS перестал резолвиться.

Фикс — перезапуск:
```bash
ssh -S /tmp/internet_pro.socks -O exit admin@admin-remote
rm -f /tmp/internet_pro.socks
ssh -M -S /tmp/internet_pro.socks -f -N -D 1080 \
  -o ServerAliveInterval=15 -o ServerAliveCountMax=3 \
  admin@admin-remote
```
