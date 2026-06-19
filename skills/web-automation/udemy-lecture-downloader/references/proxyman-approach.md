# Proxyman Approach for Udemy Video URL Extraction

Proxyman is a macOS HTTP/HTTPS proxy that can intercept traffic from any app, including Brave.

## When Proxyman Makes Sense

- You already have it installed and configured
- You prefer GUI inspection over JS console extraction
- You want to see ALL network requests (not just video)
- Debugging: understanding Udemy's API calls, CDN redirects, token refresh flow

## Setup

1. Install Proxyman CA certificate:
   - Proxyman → Certificate → Install Certificate on this Mac
   - Add to Keychain, set Trust to "Always"

2. Configure Brave to trust Proxyman CA:
   - Brave uses its own certificate store (not macOS Keychain)
   - Go to `brave://settings/privacy` → Security → Manage certificates
   - Import Proxyman CA certificate
   - OR: use Safari instead (uses system Keychain automatically)

3. Set Proxyman to intercept Brave:
   - Proxyman → Tools → SSL Proxying List → Add `*.udemy.com` and `*.cloudfront.net`

## Intercepting Video URLs

1. Open Udemy course in Brave/Safari (logged in)
2. Start playing any lecture
3. In Proxyman, filter by `mp4` or `cloudfront`
4. Look for requests like:
   ```
   https://mp4-cdn.udemy.com/.../video/WebHD_1080p.mp4?secure=...
   ```
5. Right-click → Copy URL

## Using Intercepted URL with curl

```bash
curl -L -o "lecture.mp4" \
  -H "Referer: https://www.udemy.com/" \
  -H "User-Agent: Mozilla/5.0" \
  --cookie "your_cookies_here" \
  'https://mp4-cdn.udemy.com/.../WebHD_1080p.mp4?secure=...'
```

## Limitations

- Token `?secure=...` expires in ~30-60 minutes — copy and use quickly
- Brave's separate cert store makes setup harder than Safari
- Does NOT bypass Udemy anti-bot — still need valid login session
- CDP detection is separate issue; Proxyman doesn't help with that

## Verdict

Proxyman works but adds setup complexity. The `browser_console` + `performance.getEntriesByType('resource')` method is faster and doesn't require cert configuration. Use Proxyman for debugging, not for routine batch downloads.
