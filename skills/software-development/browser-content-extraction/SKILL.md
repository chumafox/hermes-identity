---
name: browser-content-extraction
description: Extract text content from SPA web apps (Udemy, documentation, dashboards) using CDP-connected browser — expand UI sections, extract via JS fallback, organize into structured .md files.
version: 1.0.0
author: Hermes Agent
tags: [browser, scraping, content-extraction, udemy, spa, cdp]
---

# Browser Content Extraction

Extract structured text content from Single-Page Applications and web apps using Hermes' browser tools. When the page renders dynamically (React, Vue, Angular), standard HTML fetching won't work — but the CDP-connected browser can click, scroll, expand, and read rendered text.

## When to Use

- Extracting course content from platforms like Udemy, Coursera, Skillshare
- Scraping documentation sites that lazy-load sections
- Capturing text from dashboards that require login
- Any site where content is rendered via JavaScript and not in static HTML
- **Downloading videos from DRM-protected SPA sites** (via Performance API URL extraction)

## Golden Rule

**Never hand-crank repetitive work.** If you'd do the same sequence (navigate → extract → download) more than twice, write a script instead. The script saves tokens for both of you. Key principles:

1. **Embed all IDs/names as data** in the script — don't re-discover them every time
2. **Loop with error handling and resume** — not all items succeed on first pass
3. **Name files predictably** — zero-padded numbers, consistent slug format
4. **Track progress** — skip already-completed items, report per-item status

When the user says "создай автоматизацию" (create automation) or complains about repetitive work — that's the signal. Don't wait to be told twice.

## Prerequisites

**Never hand-crank repetitive work.** If you'd do the same sequence (navigate → extract → download) more than twice, write a script instead. The script:
- Embeds all IDs/names as data
- Loops with error handling and resume
- Saves tokens for both of you
- Gets saved alongside this skill for reuse

Scripts go in the project folder, referenced from the extraction output.

## Prerequisites

- A running browser with CDP (Chrome DevTools Protocol) enabled
- `browser.cdp_url` configured in Hermes config
- For logged-in sites: the browser must have active sessions (cookies/credentials)

## Technique: The 3-Phase Extraction

### Phase 1: Reconnaissance

Navigate to the target page and get the initial snapshot:

```python
browser_navigate(url="https://target-site.com/course/xxx")
browser_snapshot()  # See the structure, find section headers, expand buttons
```

Look for:
- Expand/collapse buttons for sections
- "Show more" / "Read more" buttons
- Tab panels that might contain text
- The URL pattern — is there a landing page vs player page?

For SPA content, the browser_snapshot will be truncated (shows "N more lines truncated"). Switch to JS in Phase 2.

### Phase 2: Expansion & Text Extraction

**When browser_snapshot truncates**, use `browser_console` with JavaScript to get all text:

```python
# Get full page text
browser_console(expression="document.body.innerText.slice(0, 15000)")

# Or for the full text without length limit:
browser_console(expression="document.body.innerText")
```

**To find and click expand buttons**, use JS enumeration:

```python
# List all buttons with their state
browser_console(expression="Array.from(document.querySelectorAll('button')).map(b => ({text: b.textContent.trim().slice(0, 60), expanded: b.getAttribute('aria-expanded')}))")

# Click all collapse/section toggles
browser_console(expression="Array.from(document.querySelectorAll('button')).slice(1,6).forEach(b => { if(b.getAttribute('aria-expanded')==='false') b.click(); }); 'done'")
```

**For "Show more" buttons:**
```python
browser_console(expression="Array.from(document.querySelectorAll('button')).filter(b => b.textContent.includes('Show more')).forEach(b => b.click())")
```

## Output Organization Pattern

After extraction, structure content into a consistent directory layout:

```
project-folder/
├── index.md              # Main table of contents — course metadata, structure table, file index, status checklist
├── video-list.md         # Media items to download (all lectures with durations)
└── sections/
    ├── 00-course-info.md # Comprehensive course metadata: author, rating, description, what-you-learn, requirements, instructor bio
    ├── all-lectures-descriptions.md  # Single file with ALL lecture descriptions (for large courses)
    ├── 01-section-1.md   # Organized by chunks/sections
    ├── lecture-01.md     # Individual lecture file (when detailed per-lecture extraction is needed)
    └── ...
```

Status tracking checklist convention:
```markdown
## Статус
- [x] Названия всех лекций
- [x] Описания всех лекций
- [ ] Аудио/видео
- [ ] Транскрибация
```

Create files using `write_file`. Track progress with `todo` tool.

## Pitfalls

### Browser clicks don't work via accessibility ref
Sometimes clicking a button via `browser_click(ref="eXX")` returns success but the button doesn't expand. This happens with lazy-loaded content. Use JS-based click instead:

```python
browser_console(expression="document.querySelectorAll('button')[INDEX].click()")
```

### snapshot truncation
The accessibility tree snapshot has a line limit (~500-600 lines). When the page is large, content is truncated. Always use `document.body.innerText` in `browser_console` as fallback to get ALL visible text.

### Duplicate lecture titles in course content
Udemy's course structure may return lecture titles 3x per lecture (from different DOM nodes). Deduplicate with `Array.from(new Set(...))` in JS or use unique filenames.

### "Show lecture description" buttons not responding
These buttons on Udemy's course landing page may load content via API/fetch that doesn't appear immediately. Try navigating to the individual lecture page instead, where the description is embedded in the page layout.

### Scroll needed for lazy-loaded content
Some pages lazy-render content below the fold. Use `browser_scroll` to trigger rendering:

```python
browser_scroll(direction="down")
# Then re-snapshot or re-extract
```

### Phase 4: API-Based Extraction (Fallback for Protected Content)

When browser interactions fail (Shadow DOM, lazy-loaded descriptions), try the platform's internal API. Udemy exposes REST endpoints that return structured JSON. This is the **most reliable** method — no DOM parsing, no clicking.

```python
# 1. Find the course numeric ID 
#    Use network requests OR the public API:
browser_console(expression="fetch('/api-2.0/courses/{SLUG}/', {headers:{'Accept':'application/json'}}).then(r=>r.json()).then(d=>d.id)")

# 2. Get ALL lecture IDs + titles in one call (curriculum endpoint):
browser_console(expression="fetch('/api-2.0/courses/{CID}/subscriber-curriculum-items/?curriculum_types=lecture&page_size=200&fields[lecture]=id,title,object_index', {credentials:'include', headers:{'Accept':'application/json'}}).then(r=>r.json())")

# 3. Batch-fetch descriptions (2-3 at a time to avoid timeouts):
ids = [LID_1, LID_2, LID_3]
js = f'''
Promise.all([{','.join(str(i) for i in ids)}].map(id =>
  fetch('/api-2.0/users/me/subscribed-courses/{CID}/lectures/'+id+'/?fields[lecture]=id,title,description,asset',
    {{credentials:'include', headers:{{'Accept':'application/json'}}}})
  .then(r=>r.json())
))
'''
browser_console(expression=js)
```

⚠️ **Fetch batching pitfall:** `Promise.all` with 5+ simultaneous fetches may trigger `CancelledError` (browser timeout). Fetch 2-3 at a time for reliability. For 43 lectures, that's ~15 batches — tedious but reliable.

**Response shape per lecture:**
```json
{"id": 12345, "title": "Lecture name", "description": "<p>HTML description...</p>", "asset": {"id": 67890, "asset_type": "Video", "title": "file.mp4"}}
```

Strip HTML from descriptions: `.replace(/<[^>]+>/g, '').trim()`

**Duration note:** The lecture API does NOT return `asset.length`. To get duration in seconds, make a separate call to `/api-2.0/assets/{ASSET_ID}/`.

### Phase 5: Video URL Extraction via CDP + Performance API

**This is the most reliable approach for DRM-protected video sites.**  
Even when a site uses Widevine/EME for playback, the browser's Resource Timing API often exposes the direct media URL before/during MSE processing.

#### Technique: Extract MP4 URL from Resource Timing

```python
# 1. Navigate to the lecture/video page in the CDP-connected browser
browser_navigate(url="https://site.com/lecture/123")

# 2. Wait for video to start loading (the player pre-fetches metadata)
import time; time.sleep(8)

# 3. Extract the video URL from Performance API
result = browser_console(
  expression="performance.getEntriesByType('resource')" +
    ".filter(r => r.name.includes('mp4') && r.name.includes('720p'))" +
    ".map(r => r.name)[0]"
)
video_url = result.get("result")  # e.g. "https://cdn.example.com/video.mp4?secure=TOKEN"
```

**Key filters for Udemy:**
```javascript
r.name.includes('mp4-cdn') && r.name.includes('WebHD')
```

The URL typically has a `secure=` token with an expiry timestamp. The token survives for the duration of the page session (~1 hour after initial load).

#### Download via curl with auth headers

```bash
curl -L -C - -o lecture.mp4 \
  -H "Referer: https://www.udemy.com/" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
  --cookie "ud_cache_logged_in=1; ud_cache_user=USER_ID; csrftoken=TOKEN" \
  "https://mp4-cdnXX.udemycdn.com/.../WebHD_720p.mp4?secure=TOKEN"
```

**Critical headers:**
- `Referer: https://www.udemy.com/` — required to pass CDN referrer check
- `Cookie` with at least `ud_cache_logged_in`, `ud_cache_user`, `csrftoken` — from browser's `document.cookie`
- `-C -` flag for resume support (if download is interrupted)

#### Cookie retrieval

Get cookies from the browser session:
```javascript
document.cookie  // returns all cookies as string
```

For automated scripts, extract key cookies from the browser:
```python
cookie_str = browser_console(expression="document.cookie")
# Parse and pass to curl --cookie "..."
```

**Pitfall:** Chrome/Brave on macOS encrypts cookies in its SQLite DB (AES-256-GCM with Keychain). 
`document.cookie` from the browser session is the only reliable way to get readable cookies. Direct DB queries return `encrypted_value` blobs that require the OS keychain to decrypt.

#### Anti-bot navigation: AppleScript over CDP Page.navigate

**CDP `Page.navigate` triggers anti-bot detection** on sites like Udemy. The video player renders but never receives media data (readyState stays 0). Use AppleScript to navigate the existing tab instead — it looks like a real user action:

```python
import subprocess
script = f'''
tell application "Brave Browser"
    activate
    if (count of windows) > 0 then
        tell window 1
            set URL of active tab to "{url}"
        end tell
    else
        open location "{url}"
    end if
end tell
'''
subprocess.run(["osascript", "-e", script], capture_output=True, timeout=10)
```

**Key differences:**
- `open location` → opens a NEW tab each time (bad for session continuity)
- `set URL of active tab` → reuses the current tab, keeps login session (good)
- AppleScript triggers real browser navigation without CDP detection signals
- After AppleScript navigation, the tab URL changes in ~1-2s, then video content loads in ~15-25s
- Use CDP WebSocket only for the *read* phase (extracting URL from Performance API), not for navigation

#### CDP WebSocket: proper response parsing

When using `websocket-client` library directly (not Hermes tools), the CDP response format is double-nested:

```python
response = {
  "id": 99,
  "result": {
    "result": {
      "type": "string", 
      "value": "[...]"  # ← actual result here
    }
  }
}
```

**Correct access path:** `response["result"]["result"]["value"]`

Always match responses by `id` field to distinguish evaluate results from Page events:

```python
def cdp_eval(ws, expr):
    ws.send(json.dumps({"id": 99, "method": "Runtime.evaluate", "params": {"expression": expr}}))
    deadline = time.time() + 5
    while time.time() < deadline:
        try:
            ws.settimeout(deadline - time.time())
            msg = json.loads(ws.recv())
            if msg.get("id") == 99:           # ← match by ID
                return msg["result"]["result"]["value"]  # ← double nest
        except:
            break
    return ""
```

**Prerequisites for WebSocket CDP:**
- Brave must be started with: `--remote-debugging-port=9222 --remote-allow-origins=*`
- Without `--remote-allow-origins=*`, WebSocket handshake returns 403

#### Multi-tab scanning

When the active tab might not be the first one in the CDP tab list, scan ALL tabs:

```python
import http.client, json, websocket

conn = http.client.HTTPConnection("127.0.0.1", 9222, timeout=5)
conn.request("GET", "/json")
tabs = json.loads(conn.getresponse().read())
conn.close()

for tab in tabs:
    if "udemy.com/course" not in tab.get("url", ""):
        continue
    ws = websocket.create_connection(tab["webSocketDebuggerUrl"], timeout=5)
    # ... evaluate JS to find video URL ...
    ws.close()
```

Filter by `"udemy.com/course"` (not just `"udemy"`) to avoid matching marketing/service-worker tabs.

#### Video URL expiry

Udemy MP4 URLs have a `secure=` parameter with a Unix timestamp expiry (~1 hour from page load):
```
https://mp4-cdnXX.udemycdn.com/.../WebHD_720p.mp4?secure=BASE64%2C<UNIX_EXPIRY>
```

If download fails mid-way (curl exits with partial file), the URL may have expired. Re-navigate to the lecture page and extract a fresh URL. Resuming a stale URL won't work.

#### Naming & organization

Name files after lecture numbers for easy reference:
```python
filename = f"{lecture_num:02d}-lecture-name-slugified.mp4"
```

#### Resume interrupted downloads

Udemy video URLs have a `secure=` token with expiry (~1 hour from page load). Within that window, resume works:
```bash
curl -L -C - -o lecture.mp4 [url + headers]
```
If the URL expired, re-navigate to the lecture page to get a fresh URL.

### Phase 6: Automation Pattern (Script, Don't Hand-Crank)

When extracting content from multiple pages (e.g. all 43 lectures of a course):

1. **Parse the iteration logic** — the common steps (navigate → extract URL → download → name)
2. **Write a reusable script** — embed all lecture IDs + names, loop over them
3. **Never manually repeat** — if you'd do the same task more than twice, script it

The script should handle:
- Resuming interrupted downloads (`-C -`)
- Skipping already-downloaded files (check file size > 10MB)
- Clean naming (zero-padded numbers, sanitized names)
- Error reporting per item, not aborting on first failure

**Structure from this session (udemy-dl.py):**
```
for each lecture:
  if file exists and >10MB → skip
  navigate to lecture page via CDP
  wait for video URL to appear in Performance API
  download with curl (resume if --resume flag)
  (optional) extract audio with ffmpeg
  report success/failure
```

## Reference Files
- `references/udemy-content-extraction.md` — Udemy-specific page patterns, API endpoints, and DRM tricks
- `references/chinese-web-portals.md` — 10086.cn (China Mobile) account navigation, CDP target management for SPA portals, plan change verification
