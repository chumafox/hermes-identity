# Safari osascript Scraping (for Cloudflare-protected or JS-rendered sites)

When sites block curl/Playwright/browser tools (Cloudflare, aggressive JS challenges),
use Safari on the user's Mac via osascript + AppleScript JavaScript bridge.

This is the **only reliable way** to scrape Cloudflare-protected sites, because
Safari is a real user browser that passes the JS challenge.

## Core Pattern

```python
import subprocess, time

def navigate(url):
    subprocess.run(["osascript", "-e",
        f'tell application "Safari" to set URL of current tab of window 1 to "{url}"'],
        capture_output=True, timeout=10)
    time.sleep(4)  # wait for page load

def get_page_text():
    r = subprocess.run(["osascript", "-e",
        'tell application "Safari" to return text of current tab of window 1'],
        capture_output=True, text=True, timeout=20)
    return r.stdout.strip()
```

## Window Management (critical)

- **Always use `current tab of window 1`** — `window 2`, `window -1` do NOT exist
  in most Safari instances. `make new document` creates a TAB, not a WINDOW.
- If the user is working in Safari, create a new window explicitly:
  ```bash
  osascript -e 'tell application "Safari" to make new document with properties {URL:"https://site.com"}'
  ```
  This creates a new TAB in window 1. The script will navigate this tab.
- **Conflict**: If the user manually changes tabs, the script's `set URL` will
  redirect the tab it was using. The user sees windows changing — this is expected.

## Getting Links (JavaScript Required)

Safari `return text` does NOT include URLs (hrefs are not in visible text).
You MUST use JavaScript via `do JavaScript`.

**Write JS to an `.applescript` file** — avoids quoting hell in inline osascript:

```applescript
tell application "Safari"
    do JavaScript "
        var links = document.querySelectorAll('a[href*=\"/1\"], a[href*=\"/2\"]');
        var unique = {};
        for(var i=0; i<links.length; i++) {
            var h = links[i].href;
            if(h && h.match(/appstorrent\\.ru\\/\\d+[a-z\\-]*\\.html/)) {
                unique[h] = 1;
            }
        }
        var result = '';
        for(var url in unique) {
            result += url + '\\n';
        }
        result;
    " in current tab of window 1
end tell
```

Call from Python:
```python
def get_page_urls():
    r = subprocess.run(["osascript", "/path/to/get_links.applescript"],
        capture_output=True, text=True, timeout=15)
    raw = r.stdout.strip()
    if raw and raw != "missing value":
        return [line.strip() for line in raw.split("\n") if "appstorrent" in line]
    return []
```

### Extracting descriptions from visible text

Safari's `return text` returns flattened, whitespace-reduced content.
Filter aggressively — the text includes headers, footers, and navigation:

```python
lines = [l.strip() for l in page_text.split("\n") if l.strip()]
skip = {"DMCA", "Правообладателям", "Программы", "Игры", "Комментарии", "FAQ", "Повреждено", "Telegram"}
title = ""
desc_parts = []
for line in lines:
    if not title and len(line) > 2 and line not in skip and not any(s in line for s in skip):
        title = line.split(" ")[0] if " " in line[:10] else line
    if len(line) > 60 and not any(s in line for s in skip) and not line.startswith("http"):
        desc_parts.append(line)
desc = " ".join(desc_parts)[:2000]
```

## Retry Pattern for Slow/Unstable Internet

```python
MAX_RETRIES = 10

def retry_get_links(url):
    for attempt in range(1, MAX_RETRIES + 1):
        navigate(url)
        links = get_page_urls()
        if links:
            return links
        time.sleep(30)  # wait for internet to come back
    return []

def retry_get_text(url):
    for attempt in range(1, MAX_RETRIES + 1):
        navigate(url)
        text = get_page_text()
        if len(text) > 200:  # meaningful page loaded
            return text
        time.sleep(30)
    return get_page_text()  # last resort
```

## Pagination Navigation

```python
for page in range(1, 22):  # adjust range based on item count
    url = f"https://site.com/category/page/{page}/"
    navigate(url)
    links = get_page_urls()
    # ... process links ...
    time.sleep(random.uniform(2, 5))  # human-like pause
```

## Checkpoint / Resume

```python
CHECKPOINT_FILE = "/tmp/scrape_checkpoint.txt"
OUTPUT_FILE = "/tmp/results.json"

# On each item processed:
with open(CHECKPOINT_FILE, "w") as f:
    f.write(str(current_index))

# On restart:
try:
    with open(CHECKPOINT_FILE) as f:
        start = int(f.read().strip())
except:
    start = 0
```

## Full Python Scraper Template

See the companion file `references/python-safari-scraper-v2.md` for a complete,
runnable script with retry logic, checkpoint resume, and JSON output.

## Limitations

- Need **Allow JavaScript from Apple Events** in Safari → Developer menu
- Blocks user's Safari if running in active tab (window jumps between pages)
- Speed: 3-5 pages/min, 1000 pages ≈ 3-4 hours
- `do JavaScript` may return "missing value" if JS is malformed — always
  validate output before processing
- Run in a **separate background process** via `terminal(background=true)` and
  check progress via log files
