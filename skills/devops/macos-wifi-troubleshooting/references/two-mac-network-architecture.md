# Two-Mac Network Architecture (2026-07-08)

## Реальная схема (каюта, SJYH)

```
dispo (M1 Air, HK)                pro (M1 Pro, Китай)
IP: 192.168.104.10                IP: 192.168.103.70
    │                                   │
    │      ┌─────────────────────┐      │
    │      │  SJYH Wi-Fi         │      │
    │      │  192.168.104.0/23   │      │
    │      └─────────┬───────────┘      │
    │                │                  │
    │          Hysteria2                │
    │          (Shadowrocket            │
    │           на dispo →              │
    │           H2 server               │
    │           на pro:8889)            │
    │                │                  │
    │     sing-box TUN (utun6)          │
    │     ← весь трафик через H2        │
    │                │                  │
    │                └────── WAN ──────►│
    │                          Shadowrocket VPN
    │                                   │
    │                             ZTE USB modem (en8)
    │                             WAN: 2408:xxxx (China Mobile)
    │                                   │
    │    iPhone USB (en5)               │
    │    fallback WAN                   │
    └───────────────────────────────────┘
```

## Ключевые компоненты

### На pro (серверная сторона)

1. **ZTE Mobile Broadband (en8)** — физический WAN (DHCP, IPv6 automatic)
   - Шлюз: 192.168.0.1 (IPv4), SLAAC (IPv6)
   - Default route UGScg через en8

2. **Shadowrocket** — VPN-туннель для обхода блокировок
   - Включается вручную пользователем (не авто)
   - Default route через utun (поверх ZTE) когда активен

3. **Hysteria2 server (:8889/UDP)** — туннель для dispo
   - Конфиг: `~/.config/hysteria/server.yaml`
   - Самоподписанный сертификат (CN=bing.com)
   - Пароль: совпадает с Shadowrocket на dispo
   - QUIC настройки: keepAlive 10s, maxIdleTimeout 60s

4. **Wi-Fi (en0)** — только для локальной сети
   - Default route UGScIg (inferior, не используется для WAN)

### На dispo (клиентская сторона)

1. **Shadowrocket** — Hysteria2 клиент к H2 server на pro
   - Host: admin-admin.local (→ 192.168.103.70)
   - Port: 8889, Type: Hysteria2
   - Создаёт TUN-интерфейс (обычно utun6)

2. **sing-box** — TUN-режим, весь трафик через Shadowrocket
   - Конфиг: `~/sing-box-config.json`
   - Default route через utun (Hysteria2)

3. **iPhone USB (en5)** — fallback WAN
   - DHCP, шлюз 172.20.10.1
   - Используется когда dispo не в той же сети что pro
   - Default route UGScg (выше приоритет в Service Order)

## Приоритеты сервисов

### На pro
1. ZTE Mobile Broadband (WAN)
2. Wi-Fi (локальная сеть)
3. Thunderbolt Bridge
4. iPhone USB
5. Shadowrocket (VPN)

### На dispo (сейчас)
1. iPhone USB USB (основной интернет)
2. Shadowrocket (VPN → Hysteria2 → pro)
3. Wi-Fi (локальная сеть)

## Типовые проверки

```bash
# На pro
ssh admin@192.168.103.70 "netstat -rn -f inet | grep default"
# Ожидание: default 192.168.0.1 UGScg en8 (или utun если SR активен)

# На dispo
netstat -rn -f inet | grep default
# Ожидание: default 172.20.10.1 UGScg en5 (iPhone USB)
# Или: default link#XX UCSg utun6 (sing-box → H2 → pro)

# Интернет через sing-box на dispo
curl -s --connect-timeout 8 https://bing.com
curl -s --connect-timeout 8 https://www.google.com

# Hysteria2 на pro слушает?
ssh admin@192.168.103.70 "netstat -an | grep 8889"
# Ожидание: udp46 *.8889 *.*

# Shadowrocket статус на dispo
scutil --nc status "Shadowrocket"
# Connected = Hysteria2 туннель к pro работает
```
