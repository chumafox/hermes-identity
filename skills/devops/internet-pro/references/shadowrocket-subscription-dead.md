# Shadowrocket Subscription Diagnosis (2026-06-29)

## Симптомы

- inpro туннель работает (статус АКТИВЕН), порты слушают
- Скорость к китайским сайтам через туннель: 2.3 MB/s (норма)
- Скорость к зарубежным сайтам через туннель: 50 KB/s (curl httpbin.org)
- На pro Mac (admin-remote): Google API работает быстро (0.7s), GitHub Releases — 14 B/s

## Первоначальный (неверный) диагноз

Подписка Shadowrocket `nnbin.com` / `零点云` / `ccbbss.com` мертва — на основе:
- URL подписки возвращает заглушки `客户端版本太旧了`
- Все сервера в ServerManager используют один host `dv2.wowodekuku.com`
- curl к httpbin.org/GitHub Releases показывает 14-50 KB/s

## Реальность (скорректировано 29.06.2026)

**Speedtest (Ookla) на pro Mac через Shadowrocket показал:**
```
IP: 203.10.99.75 (GSL Networks) — выход через прокси, НЕ китайский
Download: 34.90 Mbit/s
Upload: 18.25 Mbit/s
```

**Вывод: Shadowrocket работает отлично.** Прокси живой, трафик идёт через японский узел.

## Почему curl тесты были обманчивы

- **httpbin.org** — может идти по правилу Direct в Shadowrocket (не в списке заблокированных)
- **GitHub Releases** — может быть под троттлингом на конкретном узле или идти через медленный fallback
- **Google API** (generativelanguage.googleapis.com) — работает быстро, т.к. в списке проксируемых доменов
- **Speedtest** использует свою инфраструктуру и показывает реальную пропускную способность прокси

**Правило:** curl к произвольным сайтам — ненадёжный индикатор скорости прокси. Использовать speedtest-cli (Ookla).

## Команды для диагностики

```bash
# Дефинитивный тест
ssh -S /tmp/internet_pro.socks admin@admin-remote \
  'SSL_CERT_FILE=/opt/homebrew/lib/python3.14/site-packages/certifi/cacert.pem speedtest --secure'

# Проверить подписку
curl -s "http://43.135.28.238/link/2SpPwMZaaLEJ1NoJ?list=shadowrocket" | base64 -d

# Список серверов
ssh -S /tmp/internet_pro.socks admin@admin-remote \
  'plutil -convert xml1 ~/Library/Group\ Containers/group.com.liguangming.Shadowrocket/ServerManager -o /tmp/servers.plist && python3 -c "
import plistlib
with open(\"/tmp/servers.plist\", \"rb\") as f:
    data = plistlib.load(f)
for obj in data.get(\"\$objects\", []):
    if isinstance(obj, str) and len(obj) > 5 and not obj.startswith(\"http\") and not obj.startswith(\"ss:\"):
        print(obj)
"'

# Выбранный сервер
ssh -S /tmp/internet_pro.socks admin@admin-remote \
  'plutil -p ~/Library/Group\ Containers/group.com.liguangming.Shadowrocket/Library/Preferences/group.com.liguangming.Shadowrocket.plist | grep -i SelectedServer'

# Режим маршрутизации
ssh -S /tmp/internet_pro.socks admin@admin-remote \
  'plutil -p ~/Library/Group\ Containers/group.com.liguangming.Shadowrocket/Library/Preferences/group.com.liguangming.Shadowrocket.plist | grep -i GlobalRouting'
```
