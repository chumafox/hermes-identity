---
name: cloudflare
description: Управление Cloudflare — API токены, DNS записи, R2, Zones через Cloudflare API v4.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos, linux]
prerequisites:
  commands: [curl]
---

# Cloudflare API

Управление Cloudflare через REST API v4. Основные операции: зоны, DNS записи, R2, токены.

## API Credentials

Токен передаётся в заголовке:
```
Authorization: Bearer <token>
Content-Type: application/json
```

Базовый URL:
```
https://api.cloudflare.com/client/v4
```

## API Токены

### Типы токенов

| Тип | Уровень | Для чего |
|-----|---------|----------|
| Account API Token | Account-level | R2, Workers, Pages, Account Settings |
| Zone DNS Token | Zone-level (specific domain) | DNS-записи для конкретного домена |
| Global API Key | User-level | Full access (не рекомендуется) |

### Токен Account-level НЕ может редактировать DNS записи

Для DNS нужен **отдельный токен** с правами `Zone:DNS:Edit`.

**Важно:** Account API Token с кучей разрешений (включая "DNS View Write") может прочитать зоны (`GET /zones`), но DNS записи (GET/POST/PUT/DELETE `/zones/:id/dns_records`) вернут `Authentication error`.

### Страница создания токена
```
https://dash.cloudflare.com/profile/api-tokens
```

Там выбрать шаблон **"Edit zone DNS"** и ограничить зону конкретным доменом.

## Работа с Зонами (DNS)

### Проверить токен
```bash
curl -s -X GET "https://api.cloudflare.com/client/v4/user/tokens/verify" \
  -H "Authorization: Bearer TOKEN"
```

### Список зон (доменов)
```bash
curl -s -X GET "https://api.cloudflare.com/client/v4/zones" \
  -H "Authorization: Bearer TOKEN"
```

### Получить Zone ID по имени
```bash
curl -s -X GET "https://api.cloudflare.com/client/v4/zones?name=example.com" \
  -H "Authorization: Bearer TOKEN" | python3 -c "import sys,json; print(json.load(sys.stdin)['result'][0]['id'])"
```

### DNS Records

#### Список всех записей
```bash
curl -s -X GET "https://api.cloudflare.com/client/v4/zones/ZONE_ID/dns_records?per_page=100" \
  -H "Authorization: Bearer TOKEN"
```

#### Создать A запись
```bash
curl -s -X POST "https://api.cloudflare.com/client/v4/zones/ZONE_ID/dns_records" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"A","name":"example.com","content":"1.2.3.4","ttl":120,"proxied":true}'
```

#### Создать CNAME запись
```bash
curl -s -X POST "https://api.cloudflare.com/client/v4/zones/ZONE_ID/dns_records" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"CNAME","name":"subdomain","content":"target.com","ttl":120,"proxied":true}'
```

#### Обновить запись
```bash
curl -s -X PUT "https://api.cloudflare.com/client/v4/zones/ZONE_ID/dns_records/RECORD_ID" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"A","name":"example.com","content":"5.6.7.8","ttl":120,"proxied":true}'
```

#### Удалить запись
```bash
curl -s -X DELETE "https://api.cloudflare.com/client/v4/zones/ZONE_ID/dns_records/RECORD_ID" \
  -H "Authorization: Bearer TOKEN"
```

### Name Servers
При добавлении домена в Cloudflare, назначенные NS:
```bash
curl -s "https://api.cloudflare.com/client/v4/zones/ZONE_ID" | python3 -c "import sys,json; print(json.load(sys.stdin)['result'][0].get('name_servers',[]))"
```

Их нужно прописать в регистраторе домена.

## R2 (S3-compatible Storage)

### S3 Endpoint
```
https://ACCOUNT_ID.r2.cloudflarestorage.com
```

### Credentials
- Access Key: от API токена или отдельные S3 токены
- Secret Key: соответствующий секрет

### Пример curl (S3 API)
```bash
curl -X GET "https://ACCOUNT_ID.r2.cloudflarestorage.com/bucket/key" \
  -H "Authorization: Bearer TOKEN"
```

## Типичные ошибки

| Ошибка | Причина | Решение |
|--------|---------|---------|
| `Authentication error` на DNS | Токен account-level, не zone-level | Создать отдельный токен с Zone:DNS:Edit |
| `11000` token expired | Токен протух | Создать новый |
| `10003` invalid token | Токен невалидный | Проверить через `/tokens/verify` |
| Zone status `pending` | NS не обновлены у регистратора | Прописать неймсерверы у регистратора |

## Проверка разрешений токена
```bash
curl -s -X GET "https://api.cloudflare.com/client/v4/accounts/ACCOUNT_ID/tokens/TOKEN_ID" \
  -H "Authorization: Bearer TOKEN" | python3 -c "import sys,json; data=json.load(sys.stdin)['result']; [print(p['permission_groups'][0]['name']) for p in data['policies']]"
```

## Pitfalls

1. **Account Token ≠ Zone Token.** Для DNS записей нужен отдельный токен с правами Zone:DNS:Edit. Account токен (даже с кучей разрешений) не может читать DNS записи.
2. **TTL:** 1 = auto, 120+ в секундах. 120 — минимальное рекомендуемое для записей, которые могут меняться.
3. **Proxied (оранжевое облако):** включает CDN/DDoS защиту. Для API/прямых соединений лучше отключить (`proxied: false`).
4. **Zone status `pending`** — значит NS ещё не обновлены у регистратора. Страница может не грузиться пока статус не сменится на `active`.
5. **Per-page limit:** по умолчанию 50 записей. Для больших зон используй `per_page=100`.
