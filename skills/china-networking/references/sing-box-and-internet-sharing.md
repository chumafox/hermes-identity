# Sing-box & Internet Sharing Tools

## Sing-box — Lightweight CLI Proxy

**Repo:** `SagerNet/sing-box` (★34.7k) — https://github.com/SagerNet/sing-box

Open-source Go-based proxy platform. One binary, subscription URL support, TUN mode. Ideal for headless Mac.

### Установка
```bash
brew install sing-box
```

### Запуск
```bash
# Ручной запуск
sing-box run -c ~/.config/sing-box/config.json

# Как сервис (безголовый Mac)
brew services start sing-box
```

### Проверка
```bash
curl -x socks5h://127.0.0.1:1080 https://www.google.com
```

### Конвертация подписки Shadow Rocket
```bash
# Через sub-store
npx sub-store parse -o singbox -i SUBSCRIPTION_URL
```

## Internet Pro — SSH Tunnel TUI

**Файл:** `~/internet_pro.py` (на pro)

TUI-утилита для проброса интернета с безголового Mac на локальный через SSH dynamic tunnel.

**Схема:**
```
dispo (нет интернета) → SSH -D 1080 → pro (есть прокси) → интернет
```

**Установка на dispo:**
```bash
scp admin@192.168.103.70:~/internet_pro.py ~/internet_pro.py
chmod +x ~/internet_pro.py
```

**Использование:**
```bash
python3 ~/internet_pro.py
```

**TUI Controls:**
- `P` — toggle SSH tunnel (connect/disconnect)
- `Y` — toggle macOS system proxy (требует пароль)
- `N` — cycle network interface (Wi-Fi/Ethernet)
- `S` — spawn subshell with proxy env vars
- `C` — configure gateway (user/IP/port)
- `Q` — quit

**Manual CLI alternative:**
```bash
ssh -D 1080 -f -N admin@192.168.103.70
export ALL_PROXY=socks5h://127.0.0.1:1080
export http_proxy=socks5h://127.0.0.1:1080
export https_proxy=socks5h://127.0.0.1:1080
```
