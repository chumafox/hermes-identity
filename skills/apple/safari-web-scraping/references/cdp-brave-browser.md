# CDP Brave Browser for Chinese Web Services

Launch Brave Browser with CDP remote debugging for `browser_*` Hermes tools when targeting Chinese online services (e.g. 10086.cn, Taobao, JD, Baidu).

## Why Brave + CDP over Safari/osascript

- Safari/osascript method (the main safari-web-scraping skill) relies on the user having "Allow JavaScript from Apple Events" enabled and Safari open
- Brave with CDP is fully headless, works in background, and the `browser_*` tools (navigate, click, snapshot, console) are more capable than osascript
- Chinese services often use SPAs that work better in Chrome-based browsers
- The user's Brave Browser is already installed on macOS

## Launch Brave with CDP

```bash
/Applications/Brave\ Browser.app/Contents/MacOS/Brave\ Browser \
  --remote-debugging-port=9222 \
  --new-window \
  --user-data-dir=/Users/jenyanovak/.config/brave-cdp \
  2>&1 &
```

Use `terminal(background=true)` for long-lived processes.

## User-Agent Confirmation

After launch, verify via:

```bash
curl -s http://127.0.0.1:9222/json/version | python3 -c "import sys,json; d=json.load(sys.stdin); print('User-Agent:', d.get('User-Agent','?'))"
```

Brave on Mac reports: `Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36`

## Chinese Site Login Flow (10086.cn example)

After navigating to the site, login forms often use tab-switching:

1. Navigate: `browser_navigate(url)`
2. Click login link (e.g. "请登录" ref=e83)
3. Check tabs via `browser_console` JS:

```js
[...document.querySelectorAll('a, button, span, div, li')]
  .filter(el => el.textContent.includes('账号') || el.textContent.includes('密码') || el.textContent.includes('登录'))
  .map(el => ({tag: el.tagName, text: el.textContent.trim().slice(0,60), id: el.id, className: el.className.substring(0,40)}))
```

Common tabs observed on 10086.cn:
- `#sms_login_1` — "短信随机码登录" (SMS code login, phone number)
- `#mail_login_1` — "互联网用户登录" (email/password login, hidden via `hide` class)
- `#qrcode_login_1` — "扫码登录" (QR code scan via mobile app, hidden via `hide` class)

Active tab lacks `hide` class. Click a tab to switch login method:

```js
// Switch to email/password login
document.querySelector('#mail_login_1').click()
```

## Pitfalls

- **Vision API not available:** DeepSeek doesn't support `image_url` in messages. Use `browser_console` JS queries instead of `browser_vision` when the provider is DeepSeek.
- **Screenshot capture works, vision fails:** `browser_snapshot` / `browser_screenshot` work — you just can't `browser_vision` with DeepSeek. Fall back to DOM queries via `browser_console`.
- **CDP already in use:** If Brave is already running, the `--user-data-dir` flag ensures a separate profile to avoid profile locks.
- **Wait for page load:** After navigation, the page may need 2-3 seconds to render fully before DOM elements appear.
- **Chinese IP helps:** Running on a machine inside China avoids Cloudflare/WAF blocks that hit foreign IPs on domestic Chinese sites.
