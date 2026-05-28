# Python-Based Safari Scraper (Avoids Bash Quoting Hell)

The bash + osascript + doJavaScript pipeline has THREE language shells (bash, AppleScript, JavaScript) -- nested quoting almost always breaks. **Write the scraper as a Python script** instead: Python calls `subprocess.run(["osascript", "-e", script])` and handles JSON serialization cleanly.

## Template

```python
#!/path/to/portable/python3
"""Scrape paginated content via Safari + AppleScript -- Python edition."""
import json, subprocess, time, random, os

URLS_FILE = "/tmp/urls_clean.txt"
OUTPUT_FILE = "/tmp/scraped_data.json"
CHECKPOINT_FILE = "/tmp/scraped_checkpoint.txt"
LOG_FILE = "/tmp/scraped_log.txt"

def log(msg):
    with open(LOG_FILE, "a") as f:
        f.write(f"{time.strftime('%c')} {msg}\n")

def safari_js(js_code):
    script = f'''
    tell application "Safari"
        do JavaScript {json.dumps(js_code)} in current tab of window 1
    end tell
    '''
    try:
        r = subprocess.run(["osascript", "-e", script],
                           capture_output=True, text=True, timeout=15)
        return r.stdout.strip()
    except Exception as e:
        log(f"osascript failed: {e}")
        return ""

def get_text():
    """Return visible page text (good for descriptions, BAD for URLs)."""
    s = 'tell application "Safari" to return text of current tab of window 1'
    r = subprocess.run(["osascript", "-e", s], capture_output=True, text=True, timeout=20)
    return r.stdout.strip()

def navigate(url):
    script = f'tell application "Safari" to set URL of current tab of window 1 to {json.dumps(url)}'
    subprocess.run(["osascript", "-e", script], capture_output=True, timeout=10)

with open(URLS_FILE) as f:
    urls = [line.strip() for line in f if line.strip()]

existing = []
if os.path.exists(OUTPUT_FILE):
    with open(OUTPUT_FILE) as f:
        existing = json.load(f)

start = 0
if os.path.exists(CHECKPOINT_FILE):
    with open(CHECKPOINT_FILE) as f:
        start = int(f.read().strip())

for i in range(start, len(urls)):
    url = urls[i]
    log(f"[{i+1}/{len(urls)}] {url}")
    navigate(url)
    time.sleep(random.uniform(3, 6))

    js = """
    (function() {
        var h1 = document.querySelector('h1');
        var title = h1 ? h1.innerText.trim() : '';
        var ps = document.querySelectorAll('p, .description, [class*=desc]');
        var desc = '';
        for(var i=0; i<ps.length; i++) {
            var t = ps[i].innerText.trim();
            if(t.length > 50) {
                desc = t.substring(0, 2000).replace(/[\\n\\r]+/g, ' ').trim();
                break;
            }
        }
        return JSON.stringify({title: title, description: desc, url: '%s'});
    })();
    """.replace("'%s'", json.dumps(url))

    raw = safari_js(js)
    if raw and raw.startswith("{"):
        try:
            entry = json.loads(raw)
            existing.append(entry)
            with open(OUTPUT_FILE, "w") as f:
                json.dump(existing, f, ensure_ascii=False, indent=2)
        except json.JSONDecodeError as e:
            log(f"JSON error: {e}")
    else:
        log(f"Empty response: {raw[:80] if raw else 'NONE'}")

    with open(CHECKPOINT_FILE, "w") as f:
        f.write(str(i + 1))
    time.sleep(random.uniform(2, 5))

log(f"DONE: {len(existing)} items scraped")
```

## Why Python over Bash

| Problem | Bash | Python |
|---------|------|--------|
| `mapfile` unavailable on macOS bash 3 | Workaround with `while IFS=` | Native |
| Quoting hell (3 shell layers) | Complex escaping breaks | `json.dumps()` handles it |
| JSON building mid-pipeline | Fragile writes | Direct json lib |
| Debugging | Hard to trace | Proper tracebacks |
| `grep -P` not available | Use sed/awk (error-prone) | Native regex |
| Portable Python path | Must pass each command | Shebang at top |

## CRITICAL: `return text` does NOT yield URLs

`osascript -e 'tell application "Safari" to return text of current tab of window 1'` returns **only visible rendered text** — it strips all HTML structure, URLs, and attributes. Attempting to extract hyperlinks from this output with regex WILL produce zero matches.

```python
# WRONG -- always yields 0 matches:
text = get_text()
urls = re.findall(r'https?://[^\\s]+', text)  # NO URLs in text output

# RIGHT -- use do JavaScript to read href attributes:
def get_links():
    s = open("/tmp/get_links.applescript").read()
    r = subprocess.run(["osascript", s], capture_output=True, text=True, timeout=20)
    raw = r.stdout.strip()
    if raw and raw != "missing value":
        return [line.strip() for line in raw.split("\n") if "targetsite.ru" in line]
    return []
```

### The `get_links.applescript` pattern (BEST for URL extraction)

Create a standalone AppleScript file with the JavaScript embedded. This avoids ALL shell/AppleScript quoting issues:

```applescript
tell application "Safari"
    do JavaScript "
        var links = document.querySelectorAll('a');
        var unique = {};
        for(var i=0; i<links.length; i++) {
            var h = links[i].href;
            if(h && h.match(/targetsite\\.ru\\/\\d+[a-z\\-]*\\.html/)) {
                unique[h] = 1;
            }
        }
        var result = '';
        for(var url in unique) result += url + '\\n';
        result;
    " in current tab of window 1
end tell
```

Then call it from Python:
```python
def get_links():
    r = subprocess.run(["osascript", "/tmp/get_links.applescript"], 
                       capture_output=True, text=True, timeout=20)
    raw = r.stdout.strip()
    if raw and raw != "missing value":
        return [line.strip() for line in raw.split("\n") if line.strip().startswith("http")]
    return []
```

**Advantages:**
- No shell escaping — the file has `"`, `$`, `\\` literally
- Easy to test: run `osascript get_links.applescript` directly in terminal
- Python calls it via simple subprocess

## Description Extraction from `return text` (for content sites)

For sites like torrent directories where visible text IS the content (titles, descriptions visible on page), `return text` works well:

```python
def extract_description(text):
    """Extract the first meaningful paragraph from page text."""
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    skip_words = {"DMCA", "Правообладателям", "FAQ", "Комментарии", 
                  "Telegram", "Повреждено", "ЭКСКЛЮЗИВ", "Показать ещё",
                  "Программы", "Игры", "Расширения", "Товары", "ИЗБРАННОЕ"}
    
    title = ""
    desc_parts = []
    for line in lines:
        if not title and len(line) > 2 and line not in skip_words:
            title = line.split(" ")[0] if " " in line[:10] else line
        if len(line) > 60 and not any(s in line for s in skip_words) and not line.startswith("http"):
            desc_parts.append(line)
    
    desc = " ".join(desc_parts)[:2000]
    return title, desc
```

**Pitfall:** The first "long paragraph" is often footer text (copyright, DMCA notice). Filter aggressively with skip_words specific to the target site.

## Pitfalls

- **`json.dumps(js_code)`** serializes JS safely -- avoids shell interpolation
- **Safari tab must be ready** -- wait 3-6s after navigate() before extracting
- **User must enable** Safari > Develop > Allow JavaScript from Apple Events
- **Cloudflare re-challenges after ~50-100 reqs** -- user needs to refresh Safari
- **Run with portable Python** -- system python3 needs CLT which may be missing
- **Window isolation FAILS** — ALWAYS use `window 1`, never `window 2` or `window -1`.
  `make new document` creates a TAB, not a new WINDOW. If you try `window 2` you get:
  `Safari got an error: Can't get window 2. Invalid index.`
  
  If you need a dedicated window, ask user to manually open one (File → New Window, Cmd+N).
  Or accept that the scraper uses the user's active window.

## Retry Pattern (Unstable Networks)

When the target connection is unreliable (e.g. China WiFi with packet loss), wrap `return text` and `do JavaScript` calls with retries:

```python
def retry_get_links(url, max_retries=10):
    for attempt in range(1, max_retries + 1):
        navigate(url)
        links = get_links()
        if links:
            return links
        log(f"RETRY {attempt}/{max_retries}: no links, waiting 30s")
        time.sleep(30)
    return []

def retry_get_text(url, max_retries=10):
    for attempt in range(1, max_retries + 1):
        navigate(url)
        text = get_text()
        if len(text) > 200:  # meaningful content loaded
            return text
        log(f"RETRY {attempt}/{max_retries}: short text ({len(text)} chars), waiting 30s")
        time.sleep(30)
    return get_text()
```

**Signs that a retry is needed:**
- `get_text()` returns < 100 chars (likely Cloudflare challenge or blank page)
- `get_links()` returns empty `[]` (page didn't load)
- `do JavaScript` returns `"missing value"` (Safari returned before page loaded)

**Why 30 seconds:** Cloudflare challenges typically resolve within 10-20s. A 30s wait ensures the challenge clears before we retry. On very slow connections (China WiFi ~60 KiB/s), some pages take 15-20s just to load the HTML.

## Alternative: Playwright

If Safari scraping is too slow or disruptive, try Playwright with headless Chromium:
see `references/playwright-setup.md` in this skill.
