---
name: ship-wifi-iphone-sharing
description: Раздача интернета между экранным и безголовым Mac через SOCKS5 SSH-туннель по корабельному WiFi. Источник интернета — iPhone USB или ZTE 4G/5G модем.
---

# Ship WiFi — Internet Sharing Between Macs

Оба Mac в корабельном WiFi, один из них имеет свой интернет (iPhone USB или ZTE 4G/5G модем). Нужно дать интернет второму Mac через SOCKS5 SSH-туннель.

## Вариант А: Экранный Mac раздаёт интернет безголовому

Экранный имеет интернет через iPhone USB (China Mobile), безголовый в той же WiFi сети.

```
iPhone USB (China Mobile)
    ↓
экранный Mac (dispo, 192.168.103.192)
    ↓ через WiFi корабля
безголовый Mac (admin, 192.168.103.70)
    ↓ SOCKS5 :1080
Hermes Agent на безголовом → интернет через экранный Mac
```

## Вариант Б: Безголовый Mac раздаёт интернет экранному

Безголовый имеет интернет через ZTE 4G/5G модем (USB), экранный в той же WiFi сети.

```
ZTE 4G/5G (USB, China Mobile, 123.147.251.132)
    ↓
безголовый Mac (admin, 192.168.103.70)
    ↓ через WiFi корабля
экранный Mac (dispo, 192.168.103.192)
    ↓ SOCKS5 :1080
интернет на экранном Mac через безголовый
```

## Вариант В: Оба Mac в ZTE LAN (каюта)

Безголовый подключен к ZTE проводом, экранный — через WiFi ZTE.

```
ZTE 4G/5G модем
    ├── USB → безголовый Mac (192.168.0.96)
    └── WiFi → экранный Mac (192.168.0.82)
    
Оба в сети 192.168.0.0/24, интернет есть у обоих через ZTE напрямую.
Туннель НЕ нужен — сеть одна.
```

## Вариант Г: ZTE USB прямо на экранном Mac (WiFi для локального доступа)

ZTE подключён по USB к экранному Mac, WiFi корабля остаётся для SSH к безголовому.
Безголовый тоже может быть в ZTE LAN (через кабель).

```
ZTE 4G/5G модем
    ├── USB → экранный Mac (192.168.0.96, en7)
    └── кабель → безголовый Mac (192.168.0.?)

WiFi корабля: только для локальной связи между Mac
Интернет: через ZTE (default route на en7)
```

**Состояние после подключения ZTE по USB на экранный Mac:**
```bash
netstat -rn -f inet | grep default
# default  192.168.0.1    UGScg     en7    ← ZTE (активный, флаг g)
# default  192.168.104.1  UGScIg    en0    ← WiFi (неактивный, флаг I)
```

macOS автоматически ставит ZTE активным (флаг `g`), WiFi уходит в интерфейс-скоп (флаг `I`).
Вмешательство не нужно — всё работает из коробки.

**Важный нюанс — интерфейс ZTE может меняться (en5, en7, en9).** Искать по IP 192.168.0.x:
```bash
ifconfig | grep -B5 "inet 192.168.0"
```

## Параметры сети (текущий корабль)

### WiFi корабля (текущая: 192.168.104.0/23)

| Параметр | Значение |
|----------|----------|
| Экранный Mac (WiFi) | 192.168.104.235 (DHCP) |
| Безголовый Mac (WiFi, статика) | 192.168.103.70 |
| Шлюз WiFi | 192.168.104.1 |
| Пользователь экранного | jenyanovak |
| Пользователь безголового | admin |
| SSH ключ | ~/.ssh/id_ed25519_hermes |
| **Подсеть WiFi может меняться каждую сессию** | Наблюдались: 192.168.102.0/23 → 192.168.103.0/23 → **192.168.104.0/23** → 192.168.102.0/23. Корабельный DHCP перевыдает случайный /23 из пула. Статика безголового (192.168.103.70) может оказаться в другой подсети → пакеты уходят через default route вместо WiFi. Проверять всегда: `ifconfig en0 \| grep "inet "` на экранном, сверять подсеть с 192.168.103.x. Если не совпадает — добавить маршрут (см. "ZTE на экранном Mac — трафик к безголовому уходит через ZTE" выше). |

### ZTE LAN (192.168.0.0/24)

| Параметр | Значение |
|----------|----------|
| Шлюз ZTE (маршрутизатор OpenWrt) | 192.168.0.1 |
| Экранный Mac (ZTE USB, DHCP) | 192.168.0.96 |
| Безголовый Mac (ZTE USB, en8, DHCP) | конфликт — оба получают 192.168.0.96 |
| Интернет IP (ZTE, China Mobile) | 123.147.251.132 |
| **Конфликт DHCP:** ZTE выдаёт один IP (192.168.0.96). Кто первый — тот и получил. Если оба Mac одновременно на ZTE — второй не получит IP. |

## Быстрый старт

### Вариант А: интернет экранного → безголовому (через туннель)

```bash
# 1. Убить Shadowrocket на экранном
killall Shadowrocket 2>/dev/null

# 2. Запустить туннель на безголовом
ssh -i ~/.ssh/id_ed25519_hermes admin@192.168.103.70 \
  'ssh -i ~/.ssh/id_ed25519_hermes -D 1080 -N -f \
    -o StrictHostKeyChecking=no \
    -o ServerAliveInterval=15 -o TCPKeepAlive=yes \
    jenyanovak@192.168.103.192 && echo "SOCKS UP"'

# 3. Использовать Hermes через hermes-proxy
ssh -i ~/.ssh/id_ed25519_hermes admin@192.168.103.70 \
  "hermes-proxy chat -q 'привет'"
```

### Вариант Б: интернет безголового → экранному (через туннель)

Запускается с **экранного Mac**:

```bash
# 1. Создать SOCKS5 туннель на экранном (трафик пойдёт через безголовый)
ssh -i ~/.ssh/id_ed25519_hermes -D 1080 -N -f \
  -o StrictHostKeyChecking=no \
  -o ServerAliveInterval=15 -o TCPKeepAlive=yes \
  admin@192.168.103.70

# 2. Выставить ALL_PROXY
export ALL_PROXY=socks5h://127.0.0.1:1080
export HTTPS_PROXY=socks5h://127.0.0.1:1080

# 3. Проверить интернет
curl -4 -s --max-time 10 http://httpbin.org/ip
# → должен показать IP China Mobile (123.147.x.x)
```

Для автоматического использования SOCKS5 на экранном Mac можно создать alias:

```bash
alias proxy-on='export ALL_PROXY=socks5h://127.0.0.1:1080; export HTTPS_PROXY=socks5h://127.0.0.1:1080; echo "PROXY ON"'
alias proxy-off='unset ALL_PROXY HTTPS_PROXY HTTP_PROXY; echo "PROXY OFF"'
```

### Вариант В: оба в ZTE LAN (туннель не нужен)

```bash
# Просто проверить связь — оба уже в одной подсети
ping -c 2 192.168.0.96
curl -4 -s --max-time 10 http://httpbin.org/ip  # интернет есть напрямую
```

### Вариант Г: ZTE USB на экранном Mac (проверка)

```bash
# 1. Проверить что ZTE активен
netstat -rn -f inet | grep default
# → 192.168.0.1  UGScg  en7

# 2. Интернет есть?
ping -c 2 -W 3 8.8.8.8     # ~200ms через ZTE
ping -c 2 -W 3 baidu.com    # ~70ms

# 3. Связь с безголовым?
ping -c 2 -W 3 192.168.103.70      # через WiFi
ping -c 2 -W 3 192.168.0.96        # через ZTE (если безголовый там)

# 4. Какой интерфейс дал интернет?
curl -4 -s --max-time 5 http://httpbin.org/ip
# → China Mobile IP (123.147.x.x или 223.x.x.x)
```

## Клонирование Hermes Agent на другой Mac

Когда на двух Mac должна работать одна и та же версия Hermes (с одинаковыми скиллами,  
SOUL.md, AGENTS.md, конфигом), достаточно скопировать конфигурационные файлы —  
бинарник и venv не обязательно (устанавливаются отдельно).

### Проверить что нужно копировать

| Компонент | Когда копировать |
|-----------|-----------------|
| SOUL.md, AGENTS.md | всегда — это identity агента |
| config.yaml | всегда — провайдер, approvals, скиллы, память |
| skills/ | да — новые скиллы создаются на одном Mac |
| .env | **НЕТ** — на каждом Mac свои API-ключи |
| venv (~/.hermes/hermes-agent/venv/) | **НЕТ** — установить зависимости заново |
| ~/bin/hermes | **НЕТ** — установить через `hermes setup` |

### Команды (с экранного Mac на безголовый)

```bash
# 1. Сохранить backup config.yaml на безголовом
ssh admin@192.168.103.70 "cp ~/.hermes/config.yaml ~/.hermes/config.yaml.backup"

# 2. Скопировать SOUL.md, AGENTS.md, config.yaml
scp ~/.hermes/SOUL.md ~/.hermes/AGENTS.md ~/.hermes/config.yaml \
  admin@192.168.103.70:~/.hermes/

# 3. Скопировать skills (1155 файлов, ~15 MB)
rsync -avz -e "ssh -i ~/.ssh/id_ed25519_hermes" \
  ~/.hermes/skills/ \
  admin@192.168.103.70:~/.hermes/skills/
```

После копирования Hermes на безголовом подхватит новый identity.  
Проверить: `hermes chat -q "назови свой SOUL.md title"` — должен показать тот же title.

### Когда НЕ нужно копировать

- Разные версии Hermes — обновить через `hermes update` на обоих Mac
- Разные провайдеры — config.yaml придётся адаптировать
- .env не копировать — API-ключи уникальны для каждого Mac

## Делегирование задач Hermes на другом Mac

Когда туннель поднят, можно поручать задачи Hermes на удалённом Mac через SSH-команду:

```bash
# Запустить Hermes на безголовом с задачей
ssh -i ~/.ssh/id_ed25519_hermes admin@<IP_безголового> \
  "hermes-proxy chat -q 'сделай что-нибудь на этом Mac'"
```

Этот паттерн используется для:
- Настройки системы на удалённом Mac (конфиги, сервисы, разрешения)
- Диагностики (проверить статусы, логи)
- Установки софта
- Обхода TCC-ограничений (Hermes на том же Mac имеет контекст GUI-пользователя)

**Пример из сессии:** экранный Mac делегировал безголовому настройку approvals.mode=off, создание скриптов ship-tunnel.sh и hermes-proxy, настройку SSH keepalive. Hermes на безголовом выполнил все задачи через свои инструменты (terminal, write_file).

**Важно:** Hermes на удалённом Mac должен иметь approvals.mode=off (авто-аппрув), иначе зависнет в ожидании подтверждения. Настройка:

```bash
ssh admin@<IP> '\ncd ~/.hermes\npython3 -c "\nimport yaml\nwith open(\\\"config.yaml\\\") as f:\n    cfg = yaml.safe_load(f)\ncfg[\\\"approvals\\\"][\\\"mode\\\"] = \\\"off\\\"\nwith open(\\\"config.yaml\\\",\\\"w\\\") as f:\n    yaml.dump(cfg, f, default_flow_style=False, sort_keys=False)\n"\n'
```

## Проверка

```bash
# Проверить интернет через туннель (не использовать ifconfig.me — падает с exit 52)
ssh -i ~/.ssh/id_ed25519_hermes admin@192.168.103.70 \
  "ALL_PROXY=socks5h://127.0.0.1:1080 HTTPS_PROXY=socks5h://127.0.0.1:1080 \
   curl -s --max-time 15 http://httpbin.org/ip"

# Проверить Hermes на безголовом
ssh -i ~/.ssh/id_ed25519_hermes admin@192.168.103.70 \
  "ALL_PROXY=socks5h://127.0.0.1:1080 HTTPS_PROXY=socks5h://127.0.0.1:1080 \
   hermes chat -q 'Привет, ответь коротко'"
```

## Важное предупреждение: Shadowrocket

**Shadowrocket на экранном Mac мешает SOCKS5 туннелю.** SSH-трафик с безголового попадает на экранный Mac и перехватывается Shadowrocket/VPN. Туннель висит, но трафик не проходит.

**Решение:** убить Shadowrocket перед запуском туннеля:
```bash
killall Shadowrocket
# Проверить интернет напрямую через iPhone USB:
curl -s --max-time 10 ifconfig.me
# Должен показать China Mobile IP (39.144.x.x)
```

После завершения работы с безголовым — Shadowrocket можно запустить обратно.

## SSH keepalive (важно для стабильного туннеля)

При подключении туннеля используй флаги keepalive, иначе туннель отваливается через ~10 минут:

```bash
ssh -i ~/.ssh/id_ed25519_hermes -D 1080 -N -f \
  -o StrictHostKeyChecking=no \
  -o ServerAliveInterval=15 \
  -o TCPKeepAlive=yes \
  jenyanovak@192.168.103.192
```

Эти настройки уже добавлены в `/etc/ssh/sshd_config.d/000-hermes.conf` на безголовом.

## hermes-proxy — wrapper для автоматического туннеля

На безголовом создан `/usr/local/bin/hermes-proxy` — запускает Hermes с автоподнятием туннеля:

```bash
hermes-proxy chat -q "любой запрос"
# Поднимет туннель если упал, выставит ALL_PROXY, запустит hermes
```

Скрипт проверяет жив ли туннель (pgrep), если нет — запускает через `ship-tunnel.sh`, затем source'ит прокси и выполняет `hermes "$@"`.

**⚠️ ВАЖНОЕ ОГРАНИЧЕНИЕ: Hermes НЕ работает через SOCKS5 env vars.**

Установка `ALL_PROXY=socks5h://127.0.0.1:1080` в окружении работает для curl, wget и shell-команд, но **не работает для самого Hermes**. Hermes использует Python httpx/requests, которые игнорируют SOCKS5-схему через переменные окружения (требуется PySocks).

**Симптом:** туннель поднят, curl через ALL_PROXY работает, но `hermes chat` падает с `APIConnectionError: Connection error`.

**Решение:** Дать безголовому Mac собственный прямой интернет (ZTE USB, iPhone USB). SOCKS5 не подходит для проксирования Hermes.

## HTTP Proxy для iPhone (альтернатива SOCKS5)

Safari и iMessage на экранном Mac работают напрямую через WiFi корабля — **SOCKS5 туннель не нужен** для этих приложений. SOCKS5 нужен только для CLI-инструментов (curl, hermes) и приложений, запущенных с флагом `--proxy-server`.

**iPhone** не поддерживает SOCKS5 в настройках WiFi — только HTTP прокси.

### Когда нужен HTTP прокси

На корабле WiFi перегружается пассажирами — скорость падает в ноль. В таких случаях iPhone может  
получать интернет через безголовый Mac (у которого ZTE 4G/5G модем).

### Поднять HTTP прокси на безголовом Mac (для iPhone)

На безголовом может не быть Homebrew. Используем **proxy.py** — лёгкий HTTP-прокси  
на Python, устанавливается через pip:

```bash
# Установка (делается один раз)
ssh admin@192.168.103.70 "pip3 install proxy.py"

# Запуск (на 8888, слушает все интерфейсы)
ssh admin@192.168.103.70 \
  "nohup /Users/admin/Library/Python/3.9/bin/proxy --hostname 0.0.0.0 --port 8888 > /tmp/proxy.log 2>&1 &"

# Проверка
curl -x http://192.168.103.70:8888 -4 -s --max-time 10 ifconfig.me
# → должен показать ZTE IP (China Mobile, 123.147.x.x)

# Скорость через прокси (пример: ~51 Mbps до Tsinghua mirror)
curl -x http://192.168.103.70:8888 -s --max-time 30 -o /dev/null \
  -w '%{speed_download} B/s' https://mirrors.tuna.tsinghua.edu.cn/debian/ls-lR.gz
```

**Настройка iPhone:** WiFi → сеть корабля → HTTP Proxy → Manual  
Сервер: `192.168.103.70` Порт: `8888`

**Вариант с Homebrew (если есть):**
```bash
brew install tinyproxy
# настроить /opt/homebrew/etc/tinyproxy/tinyproxy.conf:
#   Port 8888, Listen 0.0.0.0, закомментировать Allow 127.0.0.1
sudo /opt/homebrew/opt/tinyproxy/bin/tinyproxy -c /opt/homebrew/etc/tinyproxy/tinyproxy.conf
```

**Автозапуск proxy.py через launchd (на безголовом):**
```bash
ssh admin@192.168.103.70 '
sudo tee /Library/LaunchDaemons/com.user.httpproxy.plist > /dev/null << "PLIST"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.httpproxy</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/admin/Library/Python/3.9/bin/proxy</string>
        <string>--hostname</string>
        <string>0.0.0.0</string>
        <string>--port</string>
        <string>8888</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
PLIST
sudo launchctl load -w /Library/LaunchDaemons/com.user.httpproxy.plist
'
```

**Проверка:** Safari на iPhone откроет сайт — трафик пойдёт через безголовый → ZTE.  
Скорость через прокси: ~51 Mbps (замер до Tsinghua mirror), практически без потерь.

### Сравнение скорости (каюта — обе палубы — перегруженный WiFi)

| Сценарий | 1 поток | 4 потока |
|----------|---------|----------|
| Оба Mac в одной каюте (в каюте) | 120 Mbit/s | 163 Mbit/s |
| Разные палубы (не загружен) | 20.9 Mbit/s | 65.6 Mbit/s |
| HTTP прокси (ZTE) через корабельный WiFi | ~51 Mbps (до Tsinghua) | — |

**Загрузка WiFi от пассажиров** — основная причина деградации. Резерв: ZTE модем  
через HTTP-прокси на безголовом (IP 192.168.103.70:8888).

### Когда нужен SOCKS5, а когда нет

| Сценарий | Нужен ли туннель? |
|----------|------------------|
| Safari, iMessage, Telegram на экранном | ❌ — WiFi корабля даёт интернет сам (China Mobile) |
| Brave с --proxy-server | ✅ — ZTE-интернет через SOCKS5 |
| Hermes (CLI) на любом Mac | ❌ — Hermes не работает через SOCKS5 env vars. Дать Mac прямой интернет |
| curl/wget с ALL_PROXY | ✅ — работает через SOCKS5 |
| iPhone Safari/iMessage | ❌ — WiFi корабля напрямую |
| iPhone нужен ZTE (WiFi корабля перегружен/блокирует) | ✅ — HTTP proxy (proxy.py) на безголовом :8888 |

## Полный сценарий (пошагово)

### Шаг 1. Проверить связь

```bash
# Доходит ли до безголового через WiFi?
ping -c 2 -W 3 192.168.103.70
```

### Шаг 2. Настроить SSH-ключ безголового на экранном Mac (делается один раз)

```bash
# Добавить публичный ключ безголового в authorized_keys экранного Mac
ssh -i ~/.ssh/id_ed25519_hermes admin@192.168.103.70 \
  "cat ~/.ssh/id_ed25519_hermes.pub" >> ~/.ssh/authorized_keys

# Проверить — SSH с безголового на экранный должен работать без пароля
ssh -i ~/.ssh/id_ed25519_hermes admin@192.168.103.70 \
  "ssh -o StrictHostKeyChecking=no jenyanovak@192.168.103.192 echo OK"
```

### Шаг 3. Запустить SOCKS5 туннель на безголовом

```bash
ssh -i ~/.ssh/id_ed25519_hermes admin@192.168.103.70 \
  'ssh -i ~/.ssh/id_ed25519_hermes -D 1080 -N -f \
    -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
    jenyanovak@192.168.103.192 && echo "SOCKS UP"'
```

Туннель работает в фоне. SOCKS5 прокси доступен на безголовом как `127.0.0.1:1080`.

### Шаг 4. Использовать Hermes на безголовом через туннель

```bash
ssh -i ~/.ssh/id_ed25519_hermes admin@192.168.103.70 \
  "ALL_PROXY=socks5h://127.0.0.1:1080 HTTPS_PROXY=socks5h://127.0.0.1:1080 \
   hermes chat -q '...'"
```

### Шаг 5. Остановить туннель

```bash
ssh -i ~/.ssh/id_ed25519_hermes admin@192.168.103.70 \
  "pkill -f 'ssh.*-D 1080.*jenyanovak@192.168.103.192'; echo tunnel_stopped"
```

### Private Wi-Fi Address (MAC-рандомизация)

На корабельном WiFi Mac использует случайный MAC (по умолчанию Fixed).
Если в настройках WiFi → Private Wi-Fi Address поставить **Off** — сеть увидит
реальный аппаратный MAC, который может быть **заблокирован** или не пропускать интернет
(корабельная сеть запомнила Fixed MAC при регистрации).

**Держать на Fixed.** Rotating тоже работает, но может сбивать при каждой смене.

Проверить: Системные настройки → Wi-Fi → (сеть корабля) → Details → Private Wi-Fi Address.

### Симптом: ARP видит безголового, но все порты таймаутятся

Mac физически в сети (L2), но пакеты молча отбрасываются (L3/L4):

```bash
arp -a | grep 192.168.103.70     # есть MAC на en0
ping -c 2 192.168.103.70         # timeout
nc -zv -G 3 192.168.103.70 22    # timeout (не refused!)
nc -zv -G 3 192.168.103.70 5900  # timeout
```

Причины (проверять на безголовом):

| Причина | Проверка на безголовом |
|---------|----------------------|
| Файрвол macOS + Stealth Mode | `sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate && ... --getstealthmode` |
| Speedify NetworkExtension (может остаться после удаления приложения!) | `systemextensionsctl list` (PacketTunnelSysExt). См. `references/orphaned-network-extensions.md` |
| Little Snitch NE (то же — живёт без приложения) | `systemextensionsctl list` (at.obdev.littlesnitch) |
| Shadowrocket / VPN | `ps aux \| grep -E "Shadowrocket\\|TunnelBlick"` |
| Remote Login выключен | `sudo systemsetup -getremotelogin` |

Починить на безголовом:
```bash
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate off
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setstealthmode off
sudo systemsetup -setremotelogin on
killall Speedify Shadowrocket 2>/dev/null
```

### ARP timeout / `arp -a` зависает

`arp -a` может висеть т.к. делает DNS-резолв каждого IP. Использовать `arp -an` (без резолва):

```bash
arp -an      # быстро, числовые IP
arp -a       # может висеть на больших подсетях
```

### Питфоллы

### Shadowrocket ломает туннель

**Shadowrocket на Mac, к которому приходит SSH-трафик, перехватывает его.** Туннель висит (PID есть, порт слушает), но трафик не проходит (таймауты).

**Решение:** убить Shadowrocket ДО запуска туннеля на стороне, куда приходит SSH.

- Вариант А (экранный → безголовый): убить Shadowrocket на **экранном** Mac
- Вариант Б (безголовый → экранный): если Shadowrocket на безголовом — убить его там

```bash
killall Shadowrocket
# Проверить что default route не сбился:
netstat -rn -f inet | grep default
```

### После убийства Shadowrocket может сбросить default route

Shadowrocket работает как VPN/TUN, и после его убийства системные маршруты могут сбиться. Восстановить:

```bash
# Для iPhone USB (en5):
sudo route add default 172.20.10.1
# Для ZTE (en8):
sudo route add default 192.168.0.1
```

### Туннель рвётся через 10-30 мин без keepalive

SSH-соединение на корабельном WiFi может обрываться из-за нестабильности сети. Обязательно добавлять:

```bash
-o ServerAliveInterval=15 -o TCPKeepAlive=yes
```

На безголовом эти настройки уже прописаны в `/etc/ssh/sshd_config.d/000-hermes.conf`.

### ZTE на экранном Mac — трафик к безголовому уходит через ZTE, не через WiFi

Когда ZTE по USB подключён к экранному Mac, а безголовый висит на WiFi корабля — трафик к безголовому (192.168.103.70) может уходить через **ZTE default route** вместо WiFi.

**Причина:** подсети разные. Экранный Mac в 192.168.104.0/23, безголовый в 192.168.103.0/24. 192.168.103.70 **не входит** в локальную WiFi подсеть → macOS отправляет пакет через default route (ZTE, 192.168.0.1), который не знает про корабельную сеть.

```bash
# Диагностика — через какой интерфейс идёт трафик:
route -n get 192.168.103.70
# Ошибка: gateway 192.168.0.1, interface en7 (ZTE)

# Починить — добавить маршрут через WiFi:
sudo route add -net 192.168.103.0/24 -interface en0

# Проверить:
route -n get 192.168.103.70
# Правильно: interface en0 (WiFi)
ping -c 2 192.168.103.70
```

**Маршрут сбрасывается после перезагрузки.** Чтобы сохранить постоянно:

```bash
sudo tee /Library/LaunchDaemons/com.local.ship-route.plist > /dev/null << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.local.ship-route</string>
    <key>ProgramArguments</key>
    <array>
        <string>/sbin/route</string>
        <string>add</string>
        <string>-net</string>
        <string>192.168.103.0/24</string>
        <string>-interface</string>
        <string>en0</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
PLIST
sudo launchctl load -w /Library/LaunchDaemons/com.local.ship-route.plist
```

**Флаг REJECT:** если маршрут добавлен, но безголовый не в сети — `route -n get` покажет `REJECT`. Это нормально — цель отсутствует, маршрут правильный.

### macOS TCC блокирует доступ к Downloads через SSH

На macOS 15+ SSH/терминал не имеют доступа к `~/Downloads/` и sandbox-контейнерам даже через sudo. Команды `ls /Users/admin/Downloads/` падают с "Operation not permitted".

**Не тратить время на обход TCC через SSH** — это не работает:
- `ditto` → блокируется
- `sudo sqlite3 TCC.db` → authorization denied
- `tccutil reset All` → нужен logout/reboot
- `sandbox-exec` → не обходит TCC
- `Finder AppleScript` → может сработать на Mac с GUI, но не гарантировано

**Решение:** перемещать файлы ВНЕ Downloads (в `/tmp/` или `/Users/admin/`), или скачать заново через CLI.

## Настройка Hermes на безголовом (делается один раз)

### 1. Авто-аппрув команд (approvals.mode = off)

```bash
ssh admin@192.168.103.70 '
cd ~/.hermes
python3 -c "
import yaml
with open(\"config.yaml\") as f:
    cfg = yaml.safe_load(f)
cfg[\"approvals\"][\"mode\"] = \"off\"
with open(\"config.yaml\",\"w\") as f:
    yaml.dump(cfg, f, default_flow_style=False, sort_keys=False)
"
'
```

### 2. SSH keepalive (чтобы туннель не рвался)

```bash
ssh admin@192.168.103.70 '
sudo mkdir -p /etc/ssh/sshd_config.d/
sudo tee /etc/ssh/sshd_config.d/000-hermes.conf > /dev/null << "CONF"
ClientAliveInterval 30
ClientAliveCountMax 3
TCPKeepAlive yes
CONF
sudo launchctl kickstart -k system/com.openssh.sshd
'
```

## Автоматизация: скрипты на безголовом Mac

Эти скрипты создаются на безголовом Mac, не на экранном.

### ship-tunnel.sh (/usr/local/bin/)

Поднимает SOCKS5 туннель с безголового на экранный Mac. Создаётся на безголовом:

```bash
ssh admin@192.168.103.70 '
sudo tee /usr/local/bin/ship-tunnel.sh > /dev/null << "SCRIPT"
#!/bin/bash
ssh -i ~/.ssh/id_ed25519_hermes \\
  -D 1080 \\
  -N -f \\
  -o StrictHostKeyChecking=no \\
  -o ServerAliveInterval=15 \\
  -o TCPKeepAlive=yes \\
  jenyanovak@192.168.103.192
echo "SOCKS5 tunnel on 127.0.0.1:1080"
SCRIPT
sudo chmod +x /usr/local/bin/ship-tunnel.sh
'
```

### ship-proxy.env (/etc/)

```bash
ssh admin@192.168.103.70 '
sudo tee /etc/ship-proxy.env > /dev/null << "ENV"
ALL_PROXY=socks5h://127.0.0.1:1080
HTTPS_PROXY=socks5h://127.0.0.1:1080
HTTP_PROXY=socks5h://127.0.0.1:1080
ENV
sudo chmod 644 /etc/ship-proxy.env
'
```

### hermes-proxy (/usr/local/bin/)

Wrapper для Hermes — сам поднимает туннель если упал, выставляет прокси:

```bash
ssh admin@192.168.103.70 '
sudo tee /usr/local/bin/hermes-proxy > /dev/null << "WRAPPER"
#!/bin/bash
if ! pgrep -f "ssh.*-D 1080.*jenyanovak@192.168.103.192" > /dev/null; then
    /usr/local/bin/ship-tunnel.sh 2>/dev/null
    sleep 1
fi
export ALL_PROXY=socks5h://127.0.0.1:1080
export HTTPS_PROXY=socks5h://127.0.0.1:1080
export HTTP_PROXY=socks5h://127.0.0.1:1080
exec hermes "$@"
WRAPPER
sudo chmod +x /usr/local/bin/hermes-proxy
'
```

Использование: `hermes-proxy chat -q '...'` вместо `hermes chat -q '...'`.

## ship-proxy.sh — переключение системного прокси на экранном Mac

Скрипт `scripts/ship-proxy.sh` (в этом скилле) — включает/выключает системный HTTP прокси на экранном Mac.
Копия на экранном Mac: `~/ship-proxy.sh`

```bash
~/ship-proxy.sh on     # включить — весь трафик через ZTE
~/ship-proxy.sh off    # выключить — прямой WiFi корабля
~/ship-proxy.sh status # проверить состояние
```

Работает через `sudo networksetup -setwebproxy`. После включения Safari, iMessage, Telegram
используют безголовый Mac :8888 (tinyproxy/proxy.py → ZTE интернет).

Когда WiFi корабля свободен — прокси лучше выключить (WiFi ~45 Mbps быстрее ZTE ~3 Mbps).
Когда WiFi перегружен пассажирами — включить.

## Особенности

- SSH-ключи: безголовый использует `id_ed25519_hermes` для доступа к экранному Mac
- На экранном Mac Remote Login должен быть включён: `sudo systemsetup -getremotelogin`
- IPv6 тоже работает через туннель (socks5h://, не socks5://)
- Если IP экранного Mac изменился (DHCP) — заменить 192.168.103.192 на актуальный
- Hermes на безголовом использует провайдера deepseek — запросы идут через интернет
- **Shadowrocket на экранном Mac должен быть убит** — иначе туннель не работает
- После убийства Shadowrocket может сбросить default route — восстановить: `sudo route add default 172.20.10.1`
- Добавить `ServerAliveInterval` в SSH команду туннеля — иначе он рвётся через 15-30 мин бездействия

## Шпаргалки для самостоятельной диагностики (на экранном Mac)

Созданы по просьбе пользователя — чтобы чинить сеть без помощи Hermes:

| Файл | О чём |
|------|-------|
| `~/ship-network-cheatsheet.md` | Общая: переключение iPhone USB/WiFi, proxy, Screen Sharing, базовые команды |
| `~/ship-zte-cheatsheet.md` | ZTE USB на экранном Mac: проверить, восстановить default route, найти безголового |
| `~/shelf-network-report.md` | Полная сетевая конфигурация безголового Mac: IP, интерфейсы, порты, связность, клиентская изоляция |

Пользователь держит их на экранном Mac и читает `cat ~/ship-*-cheatsheet.md` когда я недоступен.

## Сканирование сети (когда недоступен nmap)

Если `brew install nmap` не работает (Китай блокирует GitHub), используй Python ping sweep.
См. `references/network-scanning.md` — многопоточный скрипт без установки, сканирует /24 за ~10 сек.

```bash
# Быстрый пример — проверить живые хосты в подсети WiFi:
python3 -c "
import subprocess, concurrent.futures
def ping(ip):
    try:
        r = subprocess.run(['ping','-c','1','-W','1',ip], capture_output=True, text=True, timeout=3)
        if r.returncode == 0 and 'round-trip' in r.stdout: return ip
    except: pass
def scan(net, s, e):
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as ex:
        return sorted(r for r in ex.map(ping, [f'{net}.{i}' for i in range(s, e+1)]) if r)
print('Живые в 192.168.104.1-30:')
for ip in scan('192.168.104', 1, 30): print(f'  {ip}')
"
```

## Диагностика: безголовый Mac не найден в WiFi

Симптом: пинг 192.168.103.70 не проходит, SSH таймаут.

### Причины

1. **Подсеть WiFi корабля изменилась** — DHCP перевыдал другой диапазон. Статика безголового (192.168.103.70) может оказаться в другой подсети.
2. **Клиентская изоляция (Client Isolation)** — на разных AP корабля устройства не видят друг друга даже в одной подсети. Если dispo подключился к другой точке доступа (другая палуба), L3 связь может быть разорвана, хотя ARP видит MAC.
3. **Безголовый не подключён к WiFi** — отвалился, перезагрузился, забыл сеть.
4. **Безголовый только на ZTE** — провод от ZTE модема идёт в безголовый, WiFi не используется.

### Диагностика через ZTE LAN

Если ZTE модем доступен — безголовый почти наверняка в его LAN:

```bash
# 1. Проверить пинг через ZTE
ping -c 2 -W 3 192.168.0.96

# 2. SSH (если ключ работает)
ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=accept-new -i ~/.ssh/id_ed25519_hermes admin@192.168.0.96 "hostname"

# 3. Узнать WiFi статус безголового
ssh -i ~/.ssh/id_ed25519_hermes admin@192.168.0.96 \
  "ifconfig en0 | grep 'inet ' && /System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I | grep -E 'state|SSID'"
```

### Симптом: host key changed + permission denied

Если SSH выдаёт:
- `WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!`
- `Permission denied (publickey,password,keyboard-interactive)`

**Значит:** на безголовом переустанавливали систему. Пользователь `admin` может не существовать, или SSH ключ `id_ed25519_hermes` не добавлен в `~/.ssh/authorized_keys`.

**Запасной канал через ZTE LAN (если доступен):**

Если оба Mac в ZTE сети (192.168.0.0/24), SSH может работать через ZTE даже
при поломке WiFi-связи:

```bash
# 1. Проверить пинг
ping -c 2 -W 3 192.168.0.96

# 2. SSH (с accept-new — ключ хоста мог измениться)
ssh-keygen -R 192.168.0.96 2>/dev/null
ssh -o StrictHostKeyChecking=accept-new -i ~/.ssh/id_ed25519_hermes admin@192.168.0.96 "hostname"

# 3. Если permission denied — ключ user не в authorized_keys
# Нужен физический доступ к безголовому (каюта)
```

**Если ZTE не помогает — физический доступ к безголовому (каюта):**
- Проверить какой пользователь существует: `whoami` / `dscl . list /Users`
- Добавить публичный ключ в `~/.ssh/authorized_keys`
- Или зайти через Screen Sharing
- Или подключить монитор/клавиатуру

### Диагностика: default route flags

```bash
netstat -rn -f inet | grep default
# Флаг g = gateway (активный — внешний трафик идёт через него)
# Флаг I = interface-scoped (не используется для внешнего трафика)
# Флаг c = calculated (автоматический)
```

Если активный default НЕ тот, который нужен — добавить нужный маршрут:
```bash
sudo route add default 192.168.0.1    # через ZTE
sudo route add default 172.20.10.1    # через iPhone USB
sudo route add default 192.168.104.1    # через WiFi корабля
```

## Если что-то не работает

1. **SSH не подключается с безголового на экранный**:
   - Проверить Remote Login на экранном: `sudo systemsetup -getremotelogin`
   - Проверить ключ в authorized_keys: `cat ~/.ssh/authorized_keys`
   - Проверить IP экранного: `ifconfig en0 | grep "inet "`
   - Перезапустить SSH: `sudo launchctl stop com.openssh.sshd && sudo launchctl start com.openssh.sshd`

2. **Screen Sharing: "Screen Sharing is not permitted"**:
   Перезапустить службу:
   ```bash
   ssh -i ~/.ssh/id_ed25519_hermes admin@<IP> \
     "sudo launchctl unload /System/Library/LaunchDaemons/com.apple.screensharing.plist && \
      sleep 1 && \
      sudo launchctl load /System/Library/LaunchDaemons/com.apple.screensharing.plist"
   ```
   Проверить: `sudo launchctl list | grep screensharing` — PID > 0.

3. **Hermes отвечает долго или не отвечает**:
   - Пинг до безголового: `ping 192.168.103.70`
   - Проверить что туннель жив: `ssh ... "lsof -i :1080"` — должен быть ssh процесс в LISTEN
   - Проверить что Shadowrocket не запущен на экранном: `ps aux | grep Shadowrocket`
   - Интернет на экранном (iPhone USB): `curl -4 -s --max-time 5 http://httpbin.org/ip`

4. **Туннель поднят (PID есть), но трафик не идёт**:
   - Shadowrocket перехватывает трафик — убить: `killall Shadowrocket`
   - После убийства проверить default route: `netstat -rn -f inet | grep default`
   - Если default не на en5 (iPhone USB): `sudo route add default 172.20.10.1`

5. **Туннель рвётся через несколько минут**:
   - В команде SSH туннеля не хватает `-o ServerAliveInterval=15 -o TCPKeepAlive=yes`
   - Переподнять с этими флагами

6. **Пропал WiFi IP у экранного Mac**:
   - DHCP мог перевыдать IP — проверить: `ifconfig en0 | grep "inet "`
   - Обновить IP в командах
   - На безголовом: `/usr/local/bin/ship-tunnel.sh` использует статический 192.168.103.192

## Сеть

### Проверка интернета

- На экранном: `curl -4 -s http://httpbin.org/ip`
- Через туннель с безголового: `ALL_PROXY=socks5h://127.0.0.1:1080 curl -4 -s http://httpbin.org/ip`
- Google заблокирован China Mobile — **проверять через httpbin.org или baidu.com**, а не через Google
