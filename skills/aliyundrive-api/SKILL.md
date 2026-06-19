---
name: aliyundrive-api
description: "Work with AliyunDrive (阿里云盘) — get API tokens, WebDAV setup, file operations, and Finder integration"
tags: ["devops"]
---

# AliyunDrive (阿里云盘) API & WebDAV

## Overview
AliyunDrive (aliyundrive.com) is a Chinese cloud storage service by Alibaba Group. The paid plan offers 8 TB for 198元/year (超级会员). It has both a REST API and a built-in WebDAV feature.

## Plans (as of May 2026)
| Plan | Price | Storage | Features |
|------|-------|---------|----------|
| Free | 0元 | 105 GB | Basic |
| 超级会员 (monthly) | 30元/mo | 8 TB | Full |
| 超级会员 (annual) | 198元/yr | 8 TB | Full |
| 超级会员 (new user, annual) | 148元/yr | 8 TB | First year discount |

## REST API

### Getting tokens from browser
Tokens are stored in `localStorage.getItem('token')` on the Alipan web app (https://www.alipan.com/drive/home).

```javascript
var t = JSON.parse(localStorage.getItem('token'));
t.access_token;   // JWT token, expires ~20 min
t.refresh_token;  // long-lived (~30 days)
t.default_sbox_drive_id;  // your drive ID
```

### Refreshing access token
```bash
curl -s -X POST 'https://api.aliyundrive.com/v2/account/token' \
  -H 'Content-Type: application/json' \
  -d '{"refresh_token":"<refresh_token>","grant_type":"refresh_token"}'
```

### Check user info
```bash
curl -s -X POST 'https://api.aliyundrive.com/v2/user/get' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <access_token>' \
  -d '{}'
```

### Check drive/quota
```bash
curl -s -X POST 'https://api.aliyundrive.com/v2/drive/get' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <access_token>' \
  -d '{"drive_id":"<drive_id>"}'
```
Response includes `used_size` and `total_size` (in bytes).

### List files
```bash
curl -s -X POST 'https://api.aliyundrive.com/v2/file/list' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <access_token>' \
  -d '{"drive_id":"<drive_id>","parent_file_id":"root"}'
```

## WebDAV

### Official WebDAV (requires 三方权益包 subscription)
- In Alipan web: navigate to `/drive/application/webdav`
- Click "创建 WebDav 账号"
- Requires paid 三方权益包 (~30元/mo or 198元/yr)
- Limited to 10 GB traffic/mo without extra purchase

### Open-source WebDAV (aliyundrive-webdav, free)
**Install:**
```bash
pip3 install aliyundrive-webdav
```

**Run:**
```bash
aliyundrive-webdav --refresh-token <refresh_token> --port 18080 --root /
```

**Connect in Finder:**
1. Press `Cmd+K`
2. Enter `http://127.0.0.1:18080`
3. Click Connect

**Note:** The `refresh_token` from browser localStorage works directly. If it fails, get a fresh one via the API refresh endpoint above.

### Verify WebDAV is running
```bash
curl -s http://localhost:18080/
```

## Pitfalls
- `access_token` expires every ~20 min — always use `refresh_token` for long-lived access
- `refresh_token` changes after each refresh — save the new one returned by the refresh API
- The open-source WebDAV project was removed from npm, only pip version (aliyundrive-webdav) is available
- The official Alipan Open API (open.aliyundrive.com) no longer accepts new app registrations — use the browser tokens directly
- cua-driver needs Screen Recording permission in System Settings → Privacy & Security → Screen Recording to capture screenshots
