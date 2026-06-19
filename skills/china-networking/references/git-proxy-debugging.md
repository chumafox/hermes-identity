# Git Proxy Debugging (China)

Когда `hermes update` (или `git pull`) падает с `CONNECT tunnel failed, response 503`.

## Три места для проверки прокси

1. **Global git config:** `git config --global --get http.proxy`
2. **LOCAL git config** (внутри репозитория): `cd ~/.hermes/hermes-agent && git config --local --list | grep proxy`
3. **Environment:** `env | grep -i proxy`

**Критично:** локальный `.git/config` переопределяет глобальный. После `git config --global --unset http.proxy` в локальном может висеть `http.proxy=http://127.0.0.1:1082`.

## Фикс

```bash
cd ~/.hermes/hermes-agent
git config --local --unset http.proxy
git config --local --unset https.proxy
```

## Приоритет git proxy (высший → низший)

1. `-c http.proxy=` CLI флаг
2. `ALL_PROXY` / `http_proxy` env vars
3. Локальный конфиг репозитория (`git config --local`)
4. Глобальный конфиг пользователя (`git config --global`)
5. Системный конфиг (`git config --system`)

## Проверка

```bash
GIT_CURL_VERBOSE=1 git fetch --dry-run origin 2>&1 | head -20
# "Trying 127.0.0.1:1082" — прокси всё ещё активен
```

## GIT_TRACE диагностика

```
http.c:889  == Info:   Trying 127.0.0.1:1082...
http.c:889  == Info: Connected to 127.0.0.1 (127.0.0.1) port 1082
http.c:889  == Info: CONNECT tunnel: HTTP/1.1 negotiated
http.c:889  == Info: Establish HTTP proxy tunnel to github.com:443
http.c:848  => Send header: CONNECT github.com:443 HTTP/1.1
http.c:836  <= Recv header: HTTP/1.1 503 Service Unavailable
```

Если видишь `CONNECT tunnel: HTTP/1.1 negotiated` — git использует HTTP CONNECT прокси, а не SOCKS5. Причина: `http.proxy=http://...` а не `socks5h://...`.
