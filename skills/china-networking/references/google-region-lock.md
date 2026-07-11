# Google Region Lock & Gemini Blocking

Google services (Gemini, Google Play, etc.) determine availability by **home region** of the Google account, not just IP address.

## How Gemini determines region (in priority order)

1. **Google Account home region** — internal geo profile, set at account creation. NOT the same as Play Store country.
2. **SOCS cookie** — `SOCS=CAES...` stores the geo consent. Cached from previous sessions.
3. **Browser timezone** (`Intl.DateTimeFormat().resolvedOptions().timeZone`) — used as fallback.
4. **navigator.language** / Accept-Language header — browser locale.
5. **IP geolocation** — checked but lowest priority for Gemini web app.

## Symptoms

- Gemini: *"Gemini isn't currently supported in your country. Stay tuned!"*
- Play Store shows **United States**, IP is **US**, but Gemini still blocks
- Google AI Studio (`aistudio.google.com`) works fine (API access)

## Fixes (try in order)

### 1. Clear SOCS cookie for gemini.google.com

```python
# Via CDP - clear all cookies
browser_cdp(method="Network.clearBrowserCookies")

# Or site-specific storage clear
browser_cdp(method="Storage.clearDataForOrigin",
  params={"origin": "https://gemini.google.com", "storageTypes": "all"})
```

Then navigate to `gemini.google.com/app` — it should show Sign In page instead of blocking message.

### 2. Change macOS timezone to US

Gemini uses browser timezone as a geo signal:

```bash
sudo ln -sf /usr/share/zoneinfo/America/Chicago /etc/localtime
# Verify
date  # should show CDT/CST
```

Then restart browser and try Gemini again.

### 3. Use Gemini API (works regardless of region)

Google AI Studio at `aistudio.google.com` works even when the web app is blocked. Create an API key and use it via the Gemini API directly.

### 4. Change Google Play country

- `play.google.com/settings` → Country and profiles
- Requires leaving Family group first
- 90-day cooldown between changes
- Needs a payment method from the new country

## Google Account region vs Play Store country

| Setting | Where to see | Controls |
|---------|-------------|----------|
| Play Store country | `play.google.com/settings` | App store content, subscriptions |
| Google Account home region | Internal, not directly visible | Gemini, Google One, AI services |
| Payment profile | `payments.google.com` | Transactions, billing address |

The Play Store country can differ from the account home region. Gemini uses the **home region**, which often defaults to the country where the account was created (<1 hour after creation, it locks permanently).

## Detection

```javascript
// Browser: check timezone
Intl.DateTimeFormat().resolvedOptions().timeZone
// "America/Chicago" = US, "Asia/Shanghai" = China

// SOCS cookie content
document.cookie.split('; ').find(c => c.startsWith('SOCS='))
```

## Pitfalls

- The `SOCS` cookie is re-set on every visit to Google services. Clearing it is temporary — the geo check fires again on next navigation.
- If the account was created in China, the home region is **permanent** (<1 hour window after creation). No way to change it — must use a different account or API key.
- Changing Play Store country has no effect on Gemini availability.
- Family group membership blocks Play Store country change.
