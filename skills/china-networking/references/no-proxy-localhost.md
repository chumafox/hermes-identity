# NO_PROXY для localhost

## Проблема

Когда `ALL_PROXY=socks5://127.0.0.1:1080` (или `http_proxy`/`https_proxy`) установлены, curl и другие инструменты пытаются маршрутизировать localhost-запросы через прокси.

## Симптомы

```bash
# curl ломится в SOCKS5 на localhost:1080 вместо localhost:9222
curl -v http://127.0.0.1:9222/json/version
* Uses proxy env variable ALL_PROXY == 'socks5://127.0.0.1:1080'
* connection to proxy closed
curl: (97) connection to proxy closed

# Hermes CDP (Brave DevTools) не может подключиться
# CDP discovery methods failed for 127.0.0.1:9222
```

## Решение

```bash
# Для curl: NO_PROXY="*" отключает прокси для всех хостов
NO_PROXY="*" curl -s http://127.0.0.1:9222/json/version

# Для Brave: запускать с NO_PROXY
NO_PROXY="*" /Applications/Brave\ Browser.app/Contents/MacOS/Brave\ Browser \
  --remote-debugging-port=9222

# Проверка: lsof -i :9222 покажет LISTEN
# Если nc -v localhost 9222 говорит connection refused — вероятно порт занят другим процессом
```

## Почему это важно

CDP (Chrome DevTools Protocol) WebSocket соединения также идут через ALL_PROXY если NO_PROXY не выставлен. Hermes не устанавливает NO_PROXY автоматически для CDP localhost.

## Настройка в Hermes

CDP URL конфигурируется:
```bash
hermes config set browser.cdp_url ws://127.0.0.1:9222/devtools/browser/<UUID>
```

UUID меняется при каждом перезапуске Brave. Можно получить через:
```bash
NO_PROXY="*" curl -s http://127.0.0.1:9222/json/version | grep -o 'ws://[^"]*'
```

## Альтернатива: другой порт

Если порт 9222 занят (другим Brave или процессом):
```bash
# Запустить на 9223
NO_PROXY="*" /Applications/Brave\ Browser.app/Contents/MacOS/Brave\ Browser \
  --remote-debugging-port=9223
# Потом обновить CDP URL в конфиге
```
