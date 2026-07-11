# Google Gemini Region Block Diagnostics

## Problem

Gemini (`gemini.google.com`) shows: "Gemini isn't currently supported in your country. Stay tuned!" despite:
- IP being US-based (via Datacamp/Houston)
- Play Store showing "United States"
- Browser language set to en-US
- User being logged into Google Account

## Root Cause: Home Region of Google Account

Google determines Gemini availability via **account home region** (set at account creation, tied to payment profile). This is NOT the same as:

| Setting | Where | Can affect Gemini? |
|---------|-------|--------------------|
| IP address (geoIP) | Network level | ❌ (ignored when logged in) |
| Play Store country | play.google.com/settings | ❌ (separate from home region) |
| Browser timezone | `Intl.DateTimeFormat().resolvedOptions().timeZone` | ❌ (informational only) |
| Browser language | `navigator.language` | ❌ |
| SOCS cookie | `.google.com` domain | ❌ (session preference, not determinant) |
| **Account home region** | Google internal profile | ✅ **THIS is the blocker** |

## Diagnostic Steps

### 1. Check IP location
```bash
curl -s https://ipinfo.io/json
```
- Country: US → IP is fine
- Country: CN → IP is Chinese, need proxy/VPN

### 2. Check Play Store country
Open `https://play.google.com/settings` → "Country and profiles" section.
- Shows "United States" → Play Store is fine
- Shows "China" → fix this first (but still may not unblock Gemini)

### 3. Check timezone
```javascript
Intl.DateTimeFormat().resolvedOptions().timeZone
```
- Asia/Shanghai → change to America/Chicago or America/New_York
- This alone won't fix Gemini (it's informational)

```bash
sudo ln -sf /usr/share/zoneinfo/America/Chicago /etc/localtime
```

### 4. Check SOCS cookie
```bash
# Get SOCS value
document.cookie.split('; ').find(c=>c.startsWith('SOCS='))
```
SOCS encodes language + region preferences. Clearing it may force a fresh negotiation on next page load.

### 5. Clear cookies + storage for gemini.google.com
```python
browser_cdp(method='Network.clearBrowserCookies')
browser_cdp(method='Storage.clearDataForOrigin',
  params={'origin': 'https://gemini.google.com', 'storageTypes': 'all'})
```
Then reload — the login page should appear without the "not supported" banner. But after logging in, the block returns if the account home region is China.

### 6. Check Google Terms country version
Open `https://www.google.com/intl/en/policies/terms/` → look for "Country version: United States" in page text.

### 7. Try AI Studio (separate service)
`https://aistudio.google.com/` often works even when Gemini web doesn't. If you can access API keys there, Gemini API itself is available — only the web UI is blocked.

## Fix Options

### If account home region = China (the common case for accounts created in China):

1. **Create a new Google Account** with IP from US/EU (via VPN during creation). Home region is set at account creation time and cannot be changed without:
   - US payment method
   - Waiting 90+ days between changes
   - Leaving any Family group

2. **Use Gemini via API** instead of web UI:
   - `aistudio.google.com` — API key management, playground
   - Gemini API — programmatic access via API keys
   - Works regardless of account home region

3. **Use alternative AI tools** that work in China:
   - DeepSeek
   - Claude (via API)
   - Kimi
   - Doubao (豆包, ByteDance)

## Further Reading

- Google Play country change: https://support.google.com/googleplay/answer/7431675
- Google Account home region: https://support.google.com/accounts/answer/2978957
- Gemini availability by country: https://support.google.com/gemini/answer/13504001
