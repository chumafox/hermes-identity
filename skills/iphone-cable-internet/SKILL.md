---
name: iphone-cable-internet
description: Настройка интернета на Mac через iPhone USB-кабельный тетеринг
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

## Если связь пропала

Если после переключения пропал SSH к безголовому Mac (через WiFi):
1. Подключи Type-C или Thunderbolt кабель напрямую
2. Подключись через mDNS: `ssh user@hostname.local`
3. Восстанови порядок служб: `sudo networksetup -ordernetworkservices "Wi-Fi" "iPhone USB" "Thunderbolt Bridge"`

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
