---
name: safari-web-scraping
description: "Scrape Cloudflare-protected sites using Safari on macOS via osascript + Python. Bypass bot detection by piggybacking on the user's authenticated Safari session."
tags: [".archive"]
---

# Safari Web Scraping

Scrape websites that block headless browsers (Cloudflare, bot detection, JS challenges) by controlling the user's real Safari session via osascript.

## When to Use

- Site has Cloudflare / anti-bot protection (e.g. Russian torrent sites, CDN-protected pages)
- Playwright/curl headless fails with "Just a moment..." or CAPTCHA
- Site requires an authenticated session (user logs into a service, agent scrapes data)
- Need to bypass aggressive bot detection without proxies

## When NOT to Use

- Simple pages without JS → use `curl` or Python `requests` (faster, less resource intensive)
- Public APIs → use API directly
- Headless browser suffices → use Playwright/browser tool

## Prerequisites

1. **Safari → Settings → Advanced → Show Develop menu**
2. **Develop → Allow JavaScript from Apple Events** (required for `do JavaScript`)
3. User must **keep Safari running** while scraping

## Core Pattern: Navigate + Extract Text

```python
import subprocess, time, re, json
from urllib.parse import urljoin

def navigate(url, wait=4):
    """Open URL in current Safari tab."""
    s = f'tell application "Safari" to set URL of current tab of window 1 to "{url}"'
    subprocess.run(["osascript", "-e", s], capture_output=True, timeout=10)
    time.sleep(wait)

def get_text():
    """Return all visible text from current page."""
    r = subprocess.run(["osascript", "-e",
        'tell application "Safari" to return text of current tab of window 1'],
        capture_output=True, text=True, timeout=20)
    return r.stdout.strip()

def get_links():
    """Get all <a href> from current page via JavaScript."""
    sc = '''tell application "Safari"
    do JavaScript "
        var links=document.querySelectorAll('a');
        var result=[];
        for(var i=0;i<links.length;i++){
            var h=links[i].href;
            if(h && h.match(/example\\\\.com\\\\/\\\\d+/)) result.push(h);
        }
        [...new Set(result)].join('\\\\n');
    " in current tab of window 1
end tell'''
    r = subprocess.run(["osascript", "-e", sc], capture_output=True, text=True, timeout=20)
    raw = r.stdout.strip()
    if raw and raw != "missing value":
        return [l.strip() for l in raw.split("\n") if l.strip() and "http" in l]
    return []
```

## Alternative: Brave Browser + CDP (for Chinese services)

For Chinese online services (10086.cn, Taobao, etc.) the `browser_*` Hermes tools can be used instead of Safari/osascript. See `references/cdp-brave-browser.md` for details on launching Brave with CDP, login flow patterns, and vision API fallback workarounds.

## Pitfalls

### JavaScript in osascript escaping

### Token extraction from localStorage (authenticated sessions)

Можно вытаскивать токены/сессии из веб-приложений, где пользователь уже залогинен:

```bash
osascript -e '
tell application "Safari"
    do JavaScript "
        var t = JSON.parse(localStorage.getItem(\"token\"));
        JSON.stringify({refresh_token: t.refresh_token, nick: t.nick_name});
    " in current tab of window 1
end tell
'
```

**Использование:** AliyunDrive, Alibaba Cloud Console, любые SPA, хранящие токен в localStorage.
**Требование:** Вкладка Safari должна быть на нужном домене (навигировать через `set URL of current tab`).

Requires: Safari → Settings → Advanced → Show Develop menu + "Allow JavaScript from Apple Events".

The `do JavaScript` string inside an `osascript -e` call has **three levels of escaping**: shell → AppleScript → JavaScript. Use these rules:

```python
# Write JS code in a separate .applescript file, run via osascript /path/file
# This avoids shell/AppleScript escaping issues completely.
```

Example `/tmp/get_links.applescript`:
```applescript
tell application "Safari"
    do JavaScript "
        var links = document.querySelectorAll('a');
        var unique = {};
        for(var i=0; i<links.length; i++) {
            var h = links[i].href;
            if(h && h.match(/appstorrent\\\\.ru\\/\\d+/)) {
                unique[h] = 1;
            }
        }
        var result = '';
        for(var url in unique) result += url + '\\n';
        result;
    " in current tab of window 1
end tell
```

### JS returns "missing value"

- The `do JavaScript` callback may return `missing value` for no reason. Workaround: call `get_text()` as fallback, extract URLs with regex from visible text.
- Safari blocks JS unless "Allow JavaScript from Apple Events" is enabled in Develop menu.
- **IMPORTANT**: `window -1` or `window 2` will error if only one window exists. Always use `current tab of window 1`.
- If JS returns `missing value` consistently, the `do JavaScript` string may have broken escaping — use an `.applescript` file instead of inline `-e`.

### URL regex from visible text DOES NOT WORK

**Do NOT try to extract URLs from `get_text()` via regex.** Safari's `return text` returns only visible text content — URLs (`href` attributes) are not included. You MUST use `do JavaScript` with `document.querySelectorAll('a')` to get `href` values.

```python
# WRONG — will return 0 URLs:
import re
text = get_text()
urls = re.findall(r'https://example\.com/\d+', text)  # always empty

# CORRECT — use JavaScript:
links = get_links()  # via .applescript file
```

### Page not fully loaded

Safari's `return text` may return empty/partial content if the page is still loading. Workaround:
```python
def navigate_with_verify(url, retry=3):
    for attempt in range(retry):
        navigate(url, wait=4)
        text = get_text()
        if len(text) > 200:  # meaningful content
            return text
        elif attempt < retry - 1:
            log(f"Page load attempt {attempt+1}: only {len(text)} chars, waiting 30s")
            time.sleep(30)
    return ""
```

### Empty URL list from JS

If `get_links()` returns empty, the regex may need adjustment. Common reasons:
- Different site structure (relative vs absolute URLs)
- Cloudflare challenge not passed yet
- Page uses JS routing (SPA) — try `window.location.href` in JS
- **Pagination URL pattern**: filter pages often use `/page/N/` suffix. Exclude those from your unique set.
- **Duplicate URLs**: `.html` with query params → `url.split("?")[0]` before dedup.

### Description extraction from text

For Russian torrent/macOS sites like appstorrent.ru, the page text contains footer/header noise (DMCA, Правообладателям, Комментарии, FAQ, Telegram). Filter aggressively:

```python
SKIP_WORDS = {"DMCA", "Правообладателям", "Программы", "Игры", "Расширения",
              "Версии", "Товары", "ИЗБРАННОЕ", "Telegram", "Комментарии", "FAQ",
              "Повреждено", "Поможем", "ЭКСКЛЮЗИВ", "Результаты", "Фильтр", "Ответить"}

for line in lines:
    if len(line) > 60 and not any(s in line for s in SKIP_WORDS) and not line.startswith("http"):
        desc_parts.append(line)
```

### Safari window management

- `make new document` creates a **tab**, not a new window. Use `window 1` always.
- If user is actively using Safari, the scraping tab will visibly change URLs — this is expected.
- User can create a separate, empty Safari window for scraping. The script must use `current tab of window 1` — it will work in whichever window has focus.

## Retry Pattern for Unstable Networks

```python
def retry_get(url, max_retries=10):
    for attempt in range(1, max_retries + 1):
        navigate(url)
        links = get_links()
        if links:
            return links
        log(f"RETRY {attempt}/{max_retries}: empty, wait 30s")
        time.sleep(30)
    return []
```

## Checkpoint / Resume Pattern

```python
CHECKPOINT = "/tmp/scrape_checkpoint.txt"
OUTPUT = "/tmp/results.json"

# Resume
start = 0
if os.path.exists(CHECKPOINT):
    with open(CHECKPOINT) as f:
        start = int(f.read().strip())

for i, url in enumerate(urls[start:], start=start):
    # ... scrape ...
    with open(CHECKPOINT, "w") as f:
        f.write(str(i + 1))
    # Save every N items
    if (i+1) % 50 == 0:
        with open(OUTPUT, "w") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
```

## Human-like Delays

```python
import random
time.sleep(random.uniform(2, 5))  # between requests
time.sleep(random.uniform(3, 6))  # between pagination pages
```

## Logging

Write a log file to track progress, errors, and retries for long-running scrapes:
```python
def log(msg):
    with open("/tmp/scrape.log", "a") as f:
        f.write(f"{time.strftime('%c')} {msg}\n")
```
