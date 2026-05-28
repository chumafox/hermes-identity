# Safari + osascript Python Scraper (Cloudflare Bypass)

When headless browsers (Playwright, Hermes built-in browser) are blocked by
Cloudflare, use the user's real Safari session on macOS. This approach:

1. Opens URLs in Safari (real browser, passes Cloudflare)
2. Reads page text via AppleScript
3. Executes JavaScript via Safari's JS engine
4. Saves results with JSON checkpoint resume

## Prerequisites

- User enables Safari → Settings → Advanced → "Show Develop menu in menu bar"
- User enables Develop → "Allow JavaScript from Apple Events"
- User stays on the same Mac (script uses local Safari)
- Cannot run headless — Safari window is visible and changes tabs

## Core Pattern (Python)

```python
import subprocess, time, json, re

def navigate(url):
    """Open URL in Safari current tab."""
    subprocess.run(["osascript", "-e",
        f'tell application "Safari" to set URL of current tab of window 1 to "{url}"'],
        capture_output=True, timeout=10)
    time.sleep(4)  # Wait for Cloudflare challenge + page load

def get_text():
    """Get visible text from Safari current tab."""
    r = subprocess.run(["osascript", "-e",
        'tell application "Safari" to return text of current tab of window 1'],
        capture_output=True, text=True, timeout=20)
    return r.stdout.strip()

def get_urls_via_js():
    """Extract links via JavaScript (returns href attributes)."""
    r = subprocess.run(["osascript", "/tmp/get_links.applescript"],
        capture_output=True, text=True, timeout=30)
    raw = r.stdout.strip()
    if raw and raw != "missing value":
        return [line.strip() for line in raw.split("\n") if "appstorrent.ru" in line]
    return []
```

## Extracting URLs from Page Text

**Important:** `osascript -e 'tell application "Safari" to return text...'` returns
ONLY visible text — it does NOT include `<a href="...">` links. URLs that appear
as plain hyperlinked text in the page body are NOT included.

**Workaround 1: JavaScript** requires Safari Developer → Allow JS from Apple Events.
Create a separate `get_links.applescript` file:

```applescript
tell application "Safari"
    do JavaScript "
        var links = document.querySelectorAll('a');
        var unique = {};
        for(var i=0; i<links.length; i++) {
            var h = links[i].href;
            if(h && h.match(/appstorrent\\.ru\\/\\d+/)) {
                unique[h] = 1;
            }
        }
        var result = '';
        for(var url in unique) result += url + '\\n';
        result;
    " in current tab of window 1
end tell
```

**Workaround 2: Regex on visible text** — some sites show full URLs as visible text.
These can be extracted with regex:

```python
for m in re.finditer(r'https://appstorrent\.ru/\d+[a-z0-9\-]*\.html', text):
    all_urls.add(m.group())
```

## Pagination Pattern

For paginated content (e.g. `/programs/page/2/`, `/programs/page/3/`):

```python
all_urls = set()
for page in range(1, 22):  # max pages
    url = f"https://site.com/page/{page}/"
    navigate(url)
    time.sleep(3)
    links = get_urls_via_js()
    for u in links:
        all_urls.add(u)
    time.sleep(2)  # human-like delay between pages
```

## Retry on Connection Loss

Add retry logic for unstable internet (common in China):

```python
def retry_get_text(url, max_retries=10):
    for attempt in range(1, max_retries + 1):
        navigate(url)
        text = get_text()
        if len(text) > 100:  # meaningful content loaded
            return text
        log(f"RETRY {attempt}/{max_retries}: short text ({len(text)} chars), wait 30s")
        time.sleep(30)
    return get_text()  # last attempt whatever we got
```

## JSON Checkpoint Resume

Save progress incrementally and support resume:

```python
OUTPUT = "/tmp/data.json"
CHECKPOINT = "/tmp/checkpoint.txt"

for i, url in enumerate(urls):
    # ... scrape page ...
    
    if (i+1) % 50 == 0:
        with open(OUTPUT, "w") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        log(f"Progress: {i+1}/{len(urls)}")
    
    with open(CHECKPOINT, "w") as f:
        f.write(str(i + 1))

# After resume:
with open(CHECKPOINT) as f:
    start = int(f.read().strip())
# Skip first `start` URLs
```

## Pitfalls

1. **No `do JavaScript` without user opt-in** — JS extraction requires "Allow JavaScript from Apple Events" in Safari Developer menu. If unavailable, rely on text-only regex.

2. **`get_text()` omits URLs** — you'll get page content but not link targets. Use JS or regex on alternative page elements.

3. **Safari window must be visible** — the script changes tabs in the active window. User sees every page load. They may assume browser is "hijacked."

4. **`mapfile` not available on macOS** — bash on macOS is version 3, which lacks `mapfile`. Use `while IFS= read -r line; do ... done < file` instead.

5. **Python over bash** — for complex scrapers, write in Python. Bash osascript quoting is fragile with nested quotes.

6. **No second window** — `window 2` in AppleScript only exists if Safari has multiple open WINDOWS (not tabs). Creating a new document with `make new document` creates a tab, not a window.

7. **Checkpoint file must be reset** — if restarting from scratch, delete old checkpoint file first: `rm -f checkpoint.txt`

## Performance

- 1 page navigation: ~4-7 seconds (Cloudflare + page load)
- 1 page scrape + description parse: ~7-10 seconds
- 1000 programs: ~2-3 hours with human delays
- File grows linearly: ~2-4 KB per entry with description
