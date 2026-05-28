# aliyundrive-webdav Setup

## Installation

```bash
# Install via pip3 (npm package was removed from registry)
pip3 install aliyundrive-webdav

# Verify
aliyundrive-webdav --version
# → 2.3.3
```

## Usage

```bash
# Start WebDAV server
aliyundrive-webdav --refresh-token <REFRESH_TOKEN> --port 18080 --root /

# Server runs at http://127.0.0.1:18080
```

## Token Requirements

The `--refresh-token` argument expects a **plain string refresh_token** (32 hex chars from localStorage).

If the error `Invalid refresh token value` appears, the refresh_token may have expired. Get a fresh one:

```bash
# Refresh via API first:
curl -s -X POST 'https://api.aliyundrive.com/v2/account/token' \
  -H 'Content-Type: application/json' \
  -d '{"refresh_token":"OLD_TOKEN","grant_type":"refresh_token"}'

# The API returns the same refresh_token if still valid, or a new one if it rotated.
```

## Connect in Finder (macOS)

1. Start aliyundrive-webdav server in background
2. In Finder: Cmd+K → `http://127.0.0.1:18080`
3. Enter credentials: any username/password (server doesn't authenticate at WebDAV level)

## Alipan Official WebDAV (requires subscription)

Alipan has built-in WebDAV support at `https://www.alipan.com/drive/application/webdav`, but it requires **三方权益包** subscription (separate from 超级会员). The open-source aliyundrive-webdav is free and works without any subscription.

## Pitfalls

- **Background process**: Start with `nohup` or terminal(background=true) to keep running
- **Port conflict**: Use a different port if 18080 is in use
- **Token expiry**: The server checks token on startup only — if token expires while running, reconnect
- **npm not pip**: The package was removed from npmjs.org. Only pip3 install works
