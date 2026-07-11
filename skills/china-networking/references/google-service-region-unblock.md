# Unblocking Google Services by Account Region

When a Google service (e.g. Gemini) shows "not supported in your country" despite US IP and US Play Store settings.

## Root Cause

Google determines service availability by the **home region** of the Google Account, not by:
- IP address / geolocation
- Play Store country setting
- Timezone
- Browser language
- SOCS cookies

Home region is set when the account is created. In China, many accounts get associated with Vietnam, Russia, or China itself depending on the creation path.

## Diagnosis

1. **Check IP** — `curl -s https://ipinfo.io/json` shows country/city
2. **Check Play Store country** — `https://play.google.com/settings` → "Country and profiles"
3. **Check Google Terms country** — `https://policies.google.com/terms` shows "Country version: XX"
   - **Logged in**: shows your account's home region
   - **Not logged in**: shows region by IP
4. **Check Gemini directly** — `https://gemini.google.com/app` while logged in

## Fix: Country Association Form

1. Go to `https://policies.google.com/country-association-form`
2. Sign in with the affected account
3. Select the correct country (United States, Japan, Singapore — where the service is available)
4. Select state if applicable
5. Choose reason: **"I live here"** or **"I moved here in the past year"**
6. Submit — you'll get a confirmation email at the account's email address
7. Wait (minutes to hours) for Google to process
8. After confirmation email: log out and back into the service

## Notes

- **Family group** blocks Play Store country changes but does NOT block the country-association form
- Changing home region resets the Google company responsible for the account (e.g. Google Ireland → Google LLC)
- After the change, SOCS cookies and cached session may still show old region — clear cookies or use a fresh browser session
- Safari (without automation) works better for initial login after region change than Brave with CDP, because CDP automation sessions may interfere with Google auth flows

## Test After Change

```bash
# Check Google Terms shows new country
curl -s https://policies.google.com/terms | grep -i "country version"

# Open in browser and check
https://gemini.google.com/app
```
