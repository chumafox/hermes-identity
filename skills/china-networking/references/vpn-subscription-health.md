# VPN/Proxy Subscription Health

## Признаки мёртвой подписки

- Скорость к зарубежным сайтам 14-50 KB/s при нормальной скорости к китайским (1+ MB/s)
- Google API может работать быстро (через VIP-узел), а GitHub Releases — нет
- Подписка возвращает base64-заглушки вместо реальных конфигов
- Трафик (download/upload) не растёт неделями
- Все сервера в клиенте показывают один и тот же мёртвый host

## Диагностика

```bash
# Проверить скорость к зарубежным сайтам
curl -r 0-10485760 -o /dev/null -w "Foreign Speed: %{speed_download} B/s\n" \
  --max-time 30 "https://httpbin.org/bytes/10485760"

# Проверить скорость к китайским (для сравнения)
curl -r 0-10485760 -o /dev/null -w "CN Speed: %{speed_download} B/s\n" \
  --max-time 30 "https://mirrors.aliyun.com/ubuntu/ls-lR.gz"

# Проверить Google API (обычно идёт через VIP)
curl -I -w "Google API Time: %{time_total}s\n" \
  https://generativelanguage.googleapis.com/v1beta/models

# Проверить GitHub Releases (обычно блокируется сильнее всего)
curl -L -o /dev/null -w "GitHub Speed: %{speed_download} B/s\n" \
  --max-time 30 "https://github.com/cli/cli/releases/download/v2.40.1/gh_2.40.1_macOS_amd64.tar.gz"
```

## Что делать

1. **Обновить подписку** — вставить новый URL в прокси-клиент
2. **Переключиться на другой сервис** — LetsVPN, другой провайдер
3. **Tailscale exit node** — если есть сервер за границей с Tailscale
4. **Локальный прокси** — включить LetsVPN/Shadowrocket напрямую на машине, минуя туннель

## Подробнее

Для Shadowrocket: см. `internet-pro` skill → `references/shadowrocket-subscription-dead.md`
