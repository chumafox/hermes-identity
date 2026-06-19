# git bundle — обновление Hermes на безголовом Mac

Когда `hermes update` не работает из-за отсутствия доступа к GitHub (Китай, нет прокси).

## Проблема
На безголовом Mac (pro) нет прямого доступа к github.com. `hermes update` падает с `CONNECT tunnel failed` или `SSL_ERROR_SYSCALL`.

## Решение: git bundle

### На машине с интернетом (dispo):
```bash
cd ~/.hermes/hermes-agent
git bundle create /tmp/hermes-update.bundle --since="7 days ago" HEAD
scp /tmp/hermes-update.bundle admin@192.168.103.70:/tmp/
```

### На безголовом Mac (pro):
```bash
cd ~/.hermes/hermes-agent

# если есть локальные изменения — застэшить
git stash

# применить bundle
git fetch /tmp/hermes-update.bundle
git merge FETCH_HEAD

# вернуть stash если был
git stash pop

# очистить
rm /tmp/hermes-update.bundle
```

## Важно
- `--since="7 days ago"` — подтянет коммиты за последние 7 дней. Можно менять интервал.
- Если git merge ругается на локальные изменения — сначала `git stash`
- После обновления проверить: `git log --oneline -3`

## Почему не работает обычный прокси
- git proxy должен быть очищен и глобально (`~/.gitconfig`) И локально (`.git/config` в репозитории). Если `git config --global --list` пуст, а ошибка `CONNECT tunnel failed` остаётся — проверь `git config --local --list` внутри `~/.hermes/hermes-agent/.git/config`
- Если Shadowrocket/V2rayU в TUN-режиме — `http.proxy` НЕ НУЖЕН. TUN перехватывает весь трафик на уровне ядра, прямой доступ работает
- SOCKS5 на порту 1082 Shadowrocket — SOCKS5 рукопожатие проходит, но CONNECT к внешним хостам таймаутится. Использовать только TUN, не SOCKS5
- При ошибке `CONNECT tunnel failed, response 503` — проверь локальный `.git/config` в `~/.hermes/hermes-agent/`, там может висеть `http.proxy=http://127.0.0.1:1082`
