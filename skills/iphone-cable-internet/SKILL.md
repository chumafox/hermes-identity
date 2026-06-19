---
name: iphone-cable-internet
description: "Настройка интернета на Mac через iPhone USB-кабельный тетеринг"
tags: ["uncategorized"]
---

# iPhone USB Cable Internet

Настройка Mac на использование iPhone USB-тетеринга как основного интернета.

## Когда использовать

- Пользователь просит подключить интернет через iPhone по кабелю
- Нужно переключить Mac на мобильный интернет через iPhone
- Пользователь подключил iPhone USB-кабелем и хочет чтобы трафик шёл через него

## Проверка и настройка

1. **Проверить, виден ли iPhone USB интерфейс:**
   ```
   networksetup -listallnetworkservices
   ```
   Должен быть пункт "iPhone USB" (если iPhone подключён кабелем).

2. **Проверить IP на интерфейсах:**
   ```
   ifconfig en5 2>/dev/null | grep "inet "
   ```
   iPhone USB обычно на en5, IP в диапазоне 172.20.10.x.

3. **Сделать iPhone USB первым в приоритете:**
   ```
   sudo networksetup -ordernetworkservices "iPhone USB" <остальные службы в текущем порядке>
   ```

4. **Проверить default route:**
   ```
   netstat -rn -f inet | grep default
   ```
   Активный шлюз (флаг `g`) должен идти через iPhone USB (en5, 172.20.10.1).

5. **Проверить интернет:**
   ```
   ping -c 2 -W 3 8.8.8.8
   curl -s --max-time 5 ifconfig.me
   ```

## Диагностика default route

После включения iPhone USB, проверь куда идёт default route:

```bash
netstat -rn -f inet | grep default
```

Ожидаемый вывод:
```
default            172.20.10.1        UGScg                 en5
default            192.168.2.1        UGScIg            bridge0
```

Флаг `g` = gateway (активный шлюз). Флаг `I` = interface-scoped (не используется для внешнего трафика).

## Примечания

- IP iPhone USB: 172.20.10.x, шлюз 172.20.10.1 (iPhone)
- Интерфейс обычно en5, может меняться
- Wi-Fi можно выключить — связь не потеряется через iPhone USB
- Thunderbolt Bridge (192.168.2.x) для локальной связи между Mac — не зависит от интернета
- В Китае провайдер China Mobile, внешний IP из диапазона 223.x.x.x
- Скорость через iPhone USB тетеринг: ~9 Mbps download, ~3 Mbps upload (типично для China Mobile)
- Пинг до 8.8.8.8: ~100-200ms

## Интернет через iPhone + WiFi для локального SSH

Когда нужно, чтобы **интернет** шёл через iPhone USB, но **локальный доступ** (SSH к безголовому Mac) оставался через WiFi.

### Проверка — скорее всего уже работает

MacOS автоматически выбирает активный шлюз через флаг `g`. Если iPhone USB первый в порядке служб, default route уже идёт через него, а WiFi остаётся для локальной сети:

```
netstat -rn -f inet | grep default
# default  172.20.10.1        UGScg    en5   (интернет — iPhone)
# default  192.168.102.1      UGScI    en0   (WiFi — только локальный)
```

Флаг `g` = активный шлюз. Флаг `I` = interface-scoped (не участвует во внешнем трафике).

### Диагностика

```
# 1. Интернет через iPhone?
curl -4 -s --max-time 5 ifconfig.me   # должен показать China Mobile IP

# 2. SSH к безголовому через WiFi работает?
ssh -i ~/.ssh/key admin@192.168.x.x "hostname"

# 3. Если SSH не доходит — найди безголовый в этой WiFi сети
arp -a | grep en0
ping -c 2 192.168.x.x
```

### Если SSH не работает — найди безголовый

1. Найди безголовый Mac в WiFi сети:
   ```
   arp -a | grep "на en0"
   dns-sd -G v4 admin.local
   ```
2. Попробуй старый IP (может быть в другой подсети)
3. Не отвечает — нужен физический доступ или резервный кабель

### Важно: не отключай WiFi

`sudo networksetup -ordernetworkservices` иногда отключает WiFi. Порядок служб: iPhone USB на 1-м месте, WiFi где-то в списке. Если WiFi отключился:

```
sudo networksetup -setnetworkserviceenabled "Wi-Fi" on
sudo networksetup -setairportpower en0 on
```

## Статический IP на безголовом Mac через WiFi

Если IP безголового меняется (DHCP), закрепи его через SSH:

```
# 1. Узнать текущие настройки
ssh -i ~/.ssh/key admin@192.168.x.x \
  "networksetup -getinfo Wi-Fi; echo '---'; networksetup -getdnsservers Wi-Fi"

# 2. Назначить статический IP
ssh -i ~/.ssh/key admin@192.168.x.x \
  "sudo networksetup -setmanual 'Wi-Fi' 192.168.x.x 255.255.254.0 192.168.x.1 && \
   sudo networksetup -setdnsservers 'Wi-Fi' 1.1.1.1 8.8.8.8"

# 3. Проверить
ssh -i ~/.ssh/key admin@192.168.x.x \
  "networksetup -getinfo Wi-Fi; echo '==='; networksetup -getdnsservers Wi-Fi"
```

**Маска подсети:** из `ifconfig en0` на безголовом. Для /23: `0xfffffe00` = `255.255.254.0`.

**При смене сети** — вернуть DHCP:
```
ssh -i ~/.ssh/key admin@<текущий_ip> \
  "sudo networksetup -setdhcp 'Wi-Fi'; sudo networksetup -setdnsservers 'Wi-Fi' empty"
```

## macOS 25 TCC блокирует доступ к Downloads через SSH

**Критическое ограничение:** на macOS 25 (Sequoia) SSH/терминал **не имеют доступа** к `~/Downloads/` и sandbox-контейнерам (`~/Library/Containers/`) — **даже через sudo**.

### Что НЕ работает для обхода TCC через SSH

| Метод | Результат |
|-------|-----------|
| `ls /Users/admin/Downloads/` | `Operation not permitted` |
| `sudo ls ...` | то же самое |
| `ditto /path /tmp/` | `Operation not permitted` |
| `sudo sqlite3 /Library/.../TCC.db` | `authorization denied` |
| `tccutil reset All` | прошёл, но требует logout/reboot |
| `sudo launchctl asuser 501 ls ...` | `Operation not permitted` |
| `sandbox-exec` с кастомным sb | не обходит TCC |
| `python3 os.listdir()` | `PermissionError` |
| `authopen` | не сработал |
| `mdfind` | ничего не находит |
| AppleScript через Finder | может сработать на Mac с GUI, но ненадёжно |
| через Python внутри sandbox-приложения | только если приложение имеет доступ |

### Что может сработать (частично)

- **Finder AppleScript** — если на Mac работает GUI и Finder имеет Full Disk Access:
  ```osascript
  tell application "Finder" to duplicate folder "qwen3-models" of folder "Downloads" ...
  ```
- **Запуск с GUI-сессией** — через launchd LaunchAgent (задача выполняется в контексте GUI пользователя)

### Как обойти (рекомендации)

1. **Не класть файлы в Downloads.** Если нужно работать с файлами через SSH — сохранять в `/tmp/`, `/Users/admin/`, или `~/shelf/`.
2. **Скачать заново через CLI.** Если модель/файл в Downloads и TCC не пускает — быстрее скачать через curl/wget в `/tmp/` (интернет через ZTE будет быстрее, чем возня с TCC).
3. **Копировать через само приложение.** Если файлы внутри sandbox-контейнера (OpenVox) — использовать кнопку Export в приложении (через AppleScript).

### Почему это важно

TCC-блокировка на macOS 25 — не баг, а фича безопасности. SSH-сессии **не имеют** Full Disk Access по умолчанию. Это распространяется на:
- `~/Downloads/`
- `~/Desktop/`
- `~/Documents/`
- sandbox-контейнеры (`~/Library/Containers/`)
- системные базы данных (`TCC.db`, `ExecPolicy` и др.)

`ssh -D` (SOCKS5) туннели **не работают** для проксирования Hermes Agent (Python httpx/requests игнорируют ALL_PROXY=socks5h://). Для приложений, которым нужен интернет через другой Mac, используй HTTP-прокси (`proxy.py` или tinyproxy), а не SOCKS5.

## Если связь пропала

Если после переключения пропал SSH к безголовому Mac (через WiFi):
1. Подключи Type-C или Thunderbolt кабель напрямую
2. Подключись через mDNS: `ssh user@hostname.local`
3. Восстанови порядок служб: `sudo networksetup -ordernetworkservices "Wi-Fi" "iPhone USB" "Thunderbolt Bridge"`

## ⚠️ КРИТИЧЕСКИЙ ПИТФОЛЛ: не удаляй default route руками

**НИКОГДА** не делай:
```bash
sudo route delete default 192.168.102.1
sudo route add default 172.20.10.1
```

Если вторая команда (`route add`) не выполнится (таймаут, ошибка, разрыв SSH), Mac останется **БЕЗ default route вообще**. Пинг и SSH перестают работать. Единственный выход — физический доступ к Mac (перезагрузка или подключение кабеля).

### `networksetup -ordernetworkservices` тоже может сломаться (macOS 25+)

На macOS Sequoia (25.x) `networksetup -ordernetworkservices` **часто не срабатывает** с ошибкой:

```
Wrong number of network services... No changes have been made.
Note: Quotes must be used around service names which contain spaces.
** Error: The parameters were not valid.
```

**Причина:** macOS 25+ изменила синтаксис или добавила скрытые символы в имена служб. Команда отказывается принимать список, даже если указать все службы из `listallnetworkservices`.

**Правильный способ (без netserviceorder):**

```bash
# 1. Понизить метрику WiFi (чтобы он стал неактивным)
sudo route delete default 192.168.102.1   # Удалить WiFi default
sudo route add default 172.20.10.1         # Добавить iPhone USB default

# 2. НО: делай это ПОШАГОВО с проверкой между шагами:
#    — Сначала проверь что интерфейс iPhone USB жив:
ifconfig en5 | grep "inet "               # или en7/en9
#    — Проверь шлюз:
netstat -rn -f inet | grep 172.20.10.1
#    — ТОЛЬКО ПОТОМ удаляй WiFi route
sudo route delete default 192.168.102.1
#    — СРАЗУ проверь что новая сессия SSH жива
#    (в другом окне терминала)
ping -c 2 192.168.103.70                  # тест связи
#    — Добавь новый default:
sudo route add default 172.20.10.1
```

**Лучший способ (безопасный, если есть второй SSH-канал):**
```bash
# Открыть вторую SSH сессию через резервный канал (Thunderbolt/USB-C)
# ИЛИ запустить команду с хостом через резервный интерфейс:
sudo route add default 172.20.10.1 -ifscope en5
# Затем удалить старый:
sudo route delete default 192.168.102.1
```

**Если всё сломалось (нет ни одного default):**
- Единственный выход — физический доступ: перезагрузить Mac
- Или подключиться через прямой кабель (Thunderbolt Bridge, USB-C)
- На безголовом Mac без монитора — только кнопка питания или отключение/включение питания

### После reboot порядок служб сбрасывается

macOS при перезагрузке восстанавливает порядок сетевых служб по умолчанию. Если до перезагрузки iPhone USB был первым — после ребута WiFi снова станет активным. План действий после каждой перезагрузки:

```bash
# 1. Проверить default route:
netstat -rn -f inet | grep default

# 2. Если активный шлюз (флаг g) идёт через WiFi (192.168.102.1),
#    а не через iPhone USB (172.20.10.1) — переключить:
sudo route delete default $(netstat -rn -f inet | grep "^default" | grep "g " | awk '{print $2}')
sudo route add default 172.20.10.1

# 3. Проверить:
netstat -rn -f inet | grep "^default"
curl -4 -s --max-time 10 ifconfig.me  # должен показать China Mobile IP
```

**Решение:** добавить в cron или LaunchDaemon скрипт, который после загрузки проверяет активный шлюз и переключает на iPhone USB если нужно. Или через launchd:

```bash
# /Library/LaunchDaemons/com.user.iphoneroute.plist
# Runs once at boot: checks if iPhone USB is available, makes it default
```

### Почему это происходит

- SSH-сессия держится через текущий default route. Если удалить его — SSH рвётся.
- Новая команда `route add` может не успеть выполниться (зависнуть из-за отсутствия маршрута).
- `networksetup -ordernetworkservices` может зависнуть на macOS 25+ при смене активного интерфейса.

**Симптомы:**
- Пинг перестаёт проходить (100% loss)
- SSH: `Operation timed out`
- Mac висит в сети, но не отвечает

**Решение (только физический доступ):**
- Подойти к Mac, перезагрузить (кнопка питания или крышка)
- Или подключить прямой кабель (Thunderbolt/USB-C) к другому Mac
- Или подождать — DHCP может перевыдать IP на другом интерфейсе автоматически

## Важные предостережения

### WiFi может отключиться после смены приоритета

`sudo networksetup -ordernetworkservices "iPhone USB" "Thunderbolt Bridge" "Wi-Fi"` может привести к отключению WiFi интерфейса (даже если он в списке). Существующие SSH сессии через старый WiFi IP оборвутся.

**Решение:** всегда иметь запасное подключение (Thunderbolt Bridge или USB-C кабель).

### Приоритет: Thunderbolt Bridge

Для подключения к другому Mac (SSH/Screen Sharing) Thunderbolt Bridge (192.168.2.x, <1ms) быстрее и стабильнее WiFi. После переключения интернета на iPhone USB Thunderbolt Bridge остаётся рабочим для Mac-to-Mac связи.

### Пересечение с другими скиллами

Более полная документация по настройке iPhone USB как единственного источника интернета (с отключением WiFi, проверкой флагов route, решением проблем) — в `china-networking` → iPhone USB as Sole Internet Source.

## Статический IP для USB-C (Mac-to-Mac)

Если нужно прямое соединение между Mac по USB-C кабелю (для SSH/Screen Sharing без интернета),
можно назначить статический IP, который не меняется после переподключения кабеля.

**На безголовом Mac:**
```bash
# Создать сетевую службу для интерфейса (обычно en6)
sudo networksetup -createnetworkservice "USB-C Ethernet" en6
sudo networksetup -setmanual "USB-C Ethernet" 192.168.3.2 255.255.255.0 192.168.3.1
sudo ifconfig en6 down && sleep 1 && sudo ifconfig en6 up
```

**На экранном Mac (если интерфейс не регистрируется как служба):**
```bash
# Назначить IP напрямую через ifconfig
sudo ifconfig en7 inet 192.168.3.1 netmask 255.255.255.0

# Для сохранения после перезагрузки — создаём launchd plist:
sudo tee /Library/LaunchDaemons/com.local.usb-c-ip.plist > /dev/null << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.local.usb-c-ip</string>
    <key>ProgramArguments</key>
    <array>
        <string>/sbin/ifconfig</string>
        <string>en7</string>
        <string>inet</string>
        <string>192.168.3.1</string>
        <string>netmask</string>
        <string>255.255.255.0</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
PLIST
sudo launchctl load -w /Library/LaunchDaemons/com.local.usb-c-ip.plist
```

**Проверка:**
```bash
ssh -i ~/.ssh/id_ed25519_hermes admin@192.168.3.2
```

**Важно:**
- en6 и en7 могут меняться — проверь через `ifconfig | grep "169.254"` перед настройкой
- Link-Local адреса (169.254.x.x) меняются при каждом подключении кабеля
- Статический IP в подсети 192.168.3.0/24 не пересекается с Thunderbolt (192.168.2.0/24) и iPhone USB (172.20.10.0/28)
