# Сканирование сети (когда nmap не установлен)

`brew install nmap` может не работать из Китая (скачивает Python 3.14 как зависимость).

## Python ping sweep (многопоточный)

Работает без установки — только Python и `ping` в системе:

```python
import subprocess, concurrent.futures

def ping(ip):
    try:
        r = subprocess.run(
            ["ping", "-c", "1", "-W", "1", ip],
            capture_output=True, text=True, timeout=3
        )
        if r.returncode == 0 and "round-trip" in r.stdout:
            return ip
    except:
        pass

def scan(network, start, end, workers=50):
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        results = ex.map(ping, [f"{network}.{i}" for i in range(start, end+1)])
    found = [r for r in results if r]
    return sorted(found)
```

**Использование:**
```bash
python3 -c "
import subprocess, concurrent.futures

def ping(ip):
    try:
        r = subprocess.run(['ping','-c','1','-W','1',ip],
            capture_output=True, text=True, timeout=3)
        if r.returncode == 0 and 'round-trip' in r.stdout:
            return ip
    except:
        pass

def scan(network, start, end):
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as ex:
        return sorted(r for r in ex.map(
            ping, [f'{network}.{i}' for i in range(start, end+1)]) if r)

print('=== WiFi (192.168.104.1-30) ===')
for ip in scan('192.168.104', 1, 30):
    print(f'  {ip}')
"
```

Сканирование всей подсети /24 (254 адреса) занимает ~8-10 сек с 50 потоками.

## Альтернативы

| Инструмент | Установка | Скорость |
|-----------|-----------|----------|
| `nmap -sn 192.168.0.0/24` | `brew install nmap` (~70MB, Python 3.14) | 20-30 сек |
| `arp-scan --local` | `brew install arp-scan` | 5 сек |
| `fping -g 192.168.0.0/24` | `brew install fping` | 10 сек |
| Python ping sweep (выше) | не нужна | 8-30 сек |

Все альтернативы brew могут не установиться из Китая (блокировка GitHub). Python скрипт — fallback.

## Быстрый чек ARP

```bash
arp -an      # быстро (без DNS-резолва)
# Показывает только устройства в кеше (с кем Mac уже общался)

arp -a       # может висеть на больших подсетях (делает DNS-запросы)
# Новые устройства НЕ видны — нужен ping sweep
```

## Когда ARP видит хост, но все порты таймаутятся

Если `arp -an` показывает хост (есть MAC), но `ping`, `nc` и `ssh` все отвечают
таймаутом — это не сетевая проблема, а **фаервол на целевом Mac**:

- **macOS Firewall + Stealth Mode** — молча отбрасывает все входящие пакеты
- **Speedify / VPN** — перехватывает трафик на уровне ядра

Решение: физический доступ к целевому Mac, выключить файрвол/Speedify.

```bash
# На целевом Mac:
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate off
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setstealthmode off
sudo systemsetup -setremotelogin on
```
