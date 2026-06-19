# Aliyun Drive (阿里云盘) — Free API Reference

## Getting Access Token

The access token is stored in `localStorage['token']` (parsed JSON). Extract via CDP:

```javascript
var t = JSON.parse(localStorage.getItem('token'));
t.access_token  // Bearer token string
t.refresh_token // long-lived token (~30 days)
```

## Token Refresh

The public endpoint works without registering a custom OAuth app:

```bash
curl -s -X POST 'https://api.aliyundrive.com/v2/account/token' \
  -H 'Content-Type: application/json' \
  -d '{"refresh_token":"TOKEN","grant_type":"refresh_token"}'
```

Returns fresh access_token + refresh_token.

## Key API Endpoints

| Endpoint | Method | Body | Description |
|----------|--------|------|-------------|
| /v2/user/get | POST | {} | User profile |
| /v2/drive/get | POST | {"drive_id":"..."} | Drive info (total_size, used_size) |
| /v2/account/token | POST | {"refresh_token":"...","grant_type":"refresh_token"} | Token refresh |

## Drive Info Response

```json
{"total_size": 9440338116608, "used_size": 0, "drive_type": "normal", "status": "enabled"}
```

## WebDAV Setup

Two options:

1. **Official**: Alipan WebDAV tab requires 三方权益包 subscription (~30元/月)
2. **OSS (recommended)**: 
   ```bash
   pip3 install aliyundrive-webdav
   aliyundrive-webdav --refresh-token TOKEN --port 18080 --root /
   ```
   Connect in Finder via Cmd+K -> http://127.0.0.1:18080

Note: npm package aliyundrive-webdav is removed from registry. Use pip version 2.3.3+.

## Pricing

| Plan | Price | Storage |
|------|-------|---------|
| Free | 0元 | 105 GB |
| 超级会员 1mo | 30元 | 8 TB |
| 超级会员 1yr | 198元 | 8 TB |
| 超级会员 1yr promo | 148元 | 8 TB |

After purchase, dashboard shows "会员生效中" instead of "会员中心" button.

## Gotchas

- Refresh token persisted across multiple 20-min cycles (same string `6628b916057046a5a0cebb9af6811e0d`). May expire after ~30 days inactivity.
- Official Open API portal (open.aliyundrive.com) returns 500 errors. Public token endpoint works without it.
- The pip aliyundrive-webdav rejects tokens from expired grant_type sessions. Refresh first.
- cua-driver screenshots for WebDAV verification blocked without Screen Recording permission.
