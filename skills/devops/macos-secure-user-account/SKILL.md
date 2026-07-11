---
name: macos-secure-user-account
description: "Create a new macOS user with IP-geo-check (block China), SOCKS5 proxy, disabled geolocation, and automatic proxy-env setup. One-shot script + launchd watchdog."
category: devops
tags: [macos, user-account, proxy, geolocation, ip-check, launchd, security, china-firewall]
---

# macOS Secure User Account Setup

Создание нового пользователя macOS с принудительной проверкой IP-геолокации при входе. Если IP из Китая — сеть блокируется до перезапуска.

## Когда использовать

- Нужен чистый браузер без утечек (новый пользователь = новая изолированная песочница macOS)
- Пользователь будет работать из Китая через SOCKS5/туннель
- Нужна гарантия, что трафик не уйдёт напрямую в китайский интернет
- Google, agy и другие сервисы блокируются из-за определения региона

## Что делает

1. Создаёт пользователя с админ правами
2. Отключает геолокацию macOS
3. Ставит системный SOCKS5 прокси (127.0.0.1:1080)
4. Создаёт скрипт `/Users/<user>/check_ip.sh`:
   - Ждёт сеть (30 сек)
   - Проверяет внешний IP через `ifconfig.me` + `ipinfo.io`
   - Если страна **CN** → отключает Wi-Fi (`ifconfig en0 down`) + уведомление
   - Если не CN → уведомление с флагом
5. Launchd plist `com.<user>.ipcheck` — запуск при каждом входе + при изменении сети
6. `.zshrc` — авто-экспорт `HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY` через `socks5h://127.0.0.1:1080`

## Шаги

### 1. Создать пользователя

```bash
sudo sysadminctl -addUser <username> -fullName "<name>" -password "<password>" -admin

# Добавить в FileVault (если включён) — требуется пароль текущего админа:
sudo sysadminctl -secureTokenOn <username> -password "<password>" -adminUser <current_admin> -adminPassword "<current_password>"
```

### 2. Отключить геолокацию

```bash
sudo -u <username> defaults write /Users/<username>/Library/Preferences/com.apple.locationd.plist LocationServicesEnabled -bool false
```

### 3. Включить системный SOCKS5 прокси

```bash
sudo -u <username> networksetup -setsocksfirewallproxy Wi-Fi 127.0.0.1 1080
sudo -u <username> networksetup -setsocksfirewallproxystate Wi-Fi on
```

### 4. Создать скрипт проверки IP

Скрипт: `/Users/<username>/check_ip.sh`
Launchd plist: `/Users/<username>/Library/LaunchAgents/com.<username>.ipcheck.plist`

```bash
sudo mkdir -p /Users/<username>/Library/LaunchAgents
```

Шаблон скрипта (см. `scripts/check_ip.sh.template`) — заменить `<username>`.

### 5. Экспорт прокси в .zshrc

```bash
sudo tee -a /Users/<username>/.zshrc > /dev/null << 'SHELL'

# Прокси через SSH SOCKS
export HTTP_PROXY=socks5h://127.0.0.1:1080
export HTTPS_PROXY=socks5h://127.0.0.1:1080
export ALL_PROXY=socks5h://127.0.0.1:1080
export no_proxy="localhost,127.0.0.1,192.168.0.0/16,10.0.0.0/8"
SHELL
```

## Pitfalls

- **FileVault пароль:** `sysadminctl -addUser` может ругаться на отсутствие secure token. Нужен пароль текущего админа для `-secureTokenOn`.
- **`fdesetup add` через скрипт:** stdin не передаётся корректно при пайпе паролей — использовать `sysadminctl -secureTokenOn`.
- **Имя нового пользователя НЕ пароль:** `sysadminctl` путает аргументы при неправильном порядке — передавать `-addUser` ДО `-adminUser`.
- **Geolocation:** отключать через `defaults write` от имени нового пользователя (`sudo -u <user> defaults write`), иначе файл создаётся от root и не читается.
- **Проверка IP:** два источника (`ifconfig.me` + `ipinfo.io`) для надёжности. Если один недоступен — второй сработает.
- **`ifconfig en0 down`:** на M1 с BCM4378 драйвер ломается на уровне IOKit. После `down` нужен `up` и переподключение к WiFi. Если интерфейс не поднимается — только ребут. Учитывать в скрипте повторную проверку после `up`.

## Reference Files

- `scripts/check_ip.sh.template` — шаблон скрипта проверки IP
- `templates/ipcheck.plist.template` — шаблон launchd plist
