# Alipan (阿里云盘) API Usage

## Overview
阿里云盘 provides a REST API for file operations (upload, download, list, manage). 
Access requires OAuth 2.0 token authentication.

## Token Lifecycle

| Token Type | Lifetime | Where to Get |
|-----------|----------|-------------|
| access_token | ~20 minutes | Login session, or refresh_token exchange |
| refresh_token | ~30 days | Login session (localStorage in browser) |

## Getting refresh_token from Browser

After logging in at `https://www.alipan.com/`:
```javascript
// In browser console (F12) on alipan.com:
var t = JSON.parse(localStorage.getItem('token'));
console.log('refresh_token:', t.refresh_token);
console.log('access_token:', t.access_token);
```

## Refreshing access_token

POST `https://api.aliyundrive.com/v2/account/token`
```json
{"refresh_token": "YOUR_REFRESH_TOKEN", "grant_type": "refresh_token"}
```

Returns new access_token + same refresh_token.

## API Endpoints

### User Info
```
POST https://api.aliyundrive.com/v2/user/get
Authorization: Bearer <access_token>
Body: {}
```

### Drive Info (check quota)
```
POST https://api.aliyundrive.com/v2/drive/get
Authorization: Bearer <access_token>
Body: {"drive_id": "<drive_id>"}
```

### List Files
```
POST https://api.aliyundrive.com/v2/file/list
Authorization: Bearer <access_token>
Body: {
  "drive_id": "<drive_id>",
  "parent_file_id": "root",
  "limit": 50
}
```

### Create File (upload)
```
POST https://api.aliyundrive.com/v2/file/create
Authorization: Bearer <access_token>
```

## Pricing (as of May 2026)

| Plan | Price | Storage |
|------|-------|---------|
| Free | 0 | 105 GB |
| 超级会员 (monthly) | 30元 | 8 TB |
| 超级会员 (yearly) | 198元 | 8 TB |
| 超级会员 (first year promo) | 148元 | 8 TB |

## Checking Active Subscription

Look for `会员生效中` on the home page (alipan.com/drive/home).
Or check via API: `total_size` field in drive info (9440338116608 = 8.59 TB).

## Limitations

- No official Open API portal for creating new apps (open.aliyundrive.com is down)
- Must use tokens from existing login session
- API has rate limits (not documented, but ~100 req/min)
- Download/upload speed may be throttled for free tier
