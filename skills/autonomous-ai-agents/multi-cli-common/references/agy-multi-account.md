# Agy (Antigravity CLI) — несколько Google аккаунтов

## Как работает аутентификация

agy использует Google-аутентификацию через gcloud Application Default Credentials (ADC).
Токены хранятся в `~/.config/gcloud/`.

Один аккаунт по умолчанию — `gcloud auth list` показывает активный.

## Два аккаунта в двух сессиях agy

### Шаг 1: Добавить оба аккаунта в gcloud

```bash
# Сначала убедись что прокси работает (Google заблокирован в Китае)
# V2rayU: socks5h://127.0.0.1:1080

gcloud auth login
# → браузер, логиним первый аккаунт

gcloud auth login
# → браузер, логиним второй аккаунт

# Проверяем:
gcloud auth list
# Должны быть оба, один — активный (со звёздочкой)
```

**Важно:** `gcloud auth login` открывает браузер. На безголовом Mac — использовать
`gcloud auth login --no-browser` и скопировать код с https://google.com/device.

### Шаг 2: Запустить agy с разными аккаунтами

Терминал A:
```bash
CLOUDSDK_CORE_ACCOUNT=user1@gmail.com agy
```

Терминал B:
```bash
CLOUDSDK_CORE_ACCOUNT=user2@gmail.com agy
```

Переменная `CLOUDSDK_CORE_ACCOUNT` переопределяет активный аккаунт gcloud
для процесса и всех его дочерних потоков. agy подхватывает её автоматически
через ADC.

### Альтернатива: изоляция через HOME

Если agy не подхватывает CLOUDSDK_CORE_ACCOUNT (или для полной изоляции):

```bash
# Сессия A
HOME=/tmp/agy-a agy
# при первом запуске — gcloud auth login для аккаунта A

# Сессия B
HOME=/tmp/agy-b agy
# при первом запуске — gcloud auth login для аккаунта B
```

Каждая сессия имеет свой `~/.config/gcloud/` и свой токен.
Минус: нужно логиниться дважды.

## Проверка какой аккаунт используется

agy не имеет встроенной команды `whoami`. Быстрая проверка:

```bash
gcloud auth list 2>&1 | grep '*' | awk '{print $2}'
```

Или через env до запуска agy:

```bash
echo "Using account: ${CLOUDSDK_CORE_ACCOUNT:-$(gcloud config get account)}"
```

## Управление аккаунтами gcloud

```bash
# Сделать аккаунт активным по умолчанию
gcloud config set account user1@gmail.com

# Выйти из аккаунта
gcloud auth revoke user1@gmail.com

# Список всех
gcloud auth list
```

## Китай-специфичные нюансы

- Google заблокирован — `gcloud auth login` требует активный прокси
- V2rayU на utun4: `export https_proxy=socks5h://127.0.0.1:1080` перед `gcloud auth login`
- Git proxy для agy update: socks5h://127.0.0.1:1080 (из памяти)

## Примечание

У пользователя на этой машине зарегистрирован `vdubay@gmail.com`.
Второй аккаунт ещё не добавлен.
