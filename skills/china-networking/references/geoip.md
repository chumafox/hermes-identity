# geoip — Country by IP/Domain

**File:** `~/projects/tools/geoip`
**Alias:** `geoip` (zsh function in `.zshrc`)
**Language:** bash
**API:** ip-api.com (free, 45 req/min)

## Usage

```bash
geoip                    # свой внешний IP
geoip 8.8.8.8            # IP адрес
geoip google.com         # домен
```

## Proxy Auto-Detection

Scans ports in order:
1. `127.0.0.1:8888` — Internet Pro HTTP bridge
2. `127.0.0.1:1083` — Shadowrocket HTTP proxy
3. Direct (no proxy)

Uses the first responsive proxy for the API call.

## Dependencies

- curl (installed on macOS by default)

## Implementation

Bash script using curl + grep/sed for JSON parsing.
Originally Python3 but moved to bash because urllib had issues with HTTP proxy CONNECT.
