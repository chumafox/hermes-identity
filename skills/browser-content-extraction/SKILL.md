---
name: browser-content-extraction
description: "Extract text content from SPA web apps (Udemy, documentation, dashboards) using CDP-connected browser — expand UI sections, extract via JS fallback, organize into structured .md files."
tags: ["software-development"]
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

## Fallback: Static Content Extraction (When CDP Is Unavailable)

CDP-connected browser may not always be available (Brave not launched, port not forwarded, headless Mac without display). For **static sites** (dev.to, blog posts, documentation that renders server-side), use curl + html2text as fallback:

```bash
# 1. Download the HTML
curl -sL "https://example.com/article" -o /tmp/article.html

# 2. Install html2text (one-time)
NO_PROXY="*" pip3 install --break-system-packages html2text

# 3. Convert to Markdown
python3 -c "
import html2text
h = html2text.HTML2Text()
h.body_width = 0
h.ignore_links = False
h.ignore_images = False
h.unicode_snob = True
h.images_to_alt = True

with open('/tmp/article.html') as f:
    md = h.handle(f.read())

with open('/path/to/output.md', 'w') as f:
    f.write(md)
print(f'Saved: {len(md)} chars')
"
```

### Post-processing: Clean up html2text artifacts

html2text captures navigation, comments, footer, and sidebar. Clean the output:

```python
import re

with open('output.md') as f:
    md = f.read()

# Remove anchor links like [ ](<#section-name>)
md = re.sub(r'\[ ?\]\(<#[^>]+>\)', '', md)

# Remove tag links like [#ai](</t/ai>)
md = re.sub(r'\[#[^\]]+\]\(<[^>]+>\)', '', md)

# Remove "Enter fullscreen mode Exit fullscreen mode" lines
md = re.sub(r'^.*Enter fullscreen mode.*$\n', '', md, flags=re.MULTILINE)

# Fix escaped dashes
md = md.replace('\\\\--', '—').replace('\\--', '—')

# Remove footer after known end markers
for marker in ['## Top comments', 'More from [', '💎 DEV Diamond Sponsors']:
    idx = md.find(marker)
    if idx != -1:
        md = md[:idx].rstrip()

# Clean up multiple blank lines
md = re.sub(r'\n{4,}', '\n\n\n', md)
```

### When to use this vs CDP

| Situation | Method |
|-----------|--------|
| CDP available, site is SPA (React/Vue/Angular) | CDP browser tools |
| CDP available, site is static HTML | Either — CDP or curl |
| CDP unavailable, site is static HTML | curl + html2text |
| CDP unavailable, site is SPA | Need CDP (no fallback) |
| Site behind Cloudflare/anti-bot | CDP with real browser (see `safari-web-scraping` skill) |

### Limitations

- html2text does NOT execute JavaScript — SPA content won't render
- Navigation/footer/comments require post-processing cleanup
- Rate limiting: add `sleep(1)` between requests to avoid 429
- Some sites block `curl -sL` — try adding `-H "User-Agent: Mozilla/5.0"`

## Pitfalls

### Browser clicks don't work via accessibility ref
Sometimes clicking a button via `browser_click(ref="eXX")` returns success but the button doesn't expand. This happens with lazy-loaded content. Use JS-based click instead:

```python
browser_console(expression="document.querySelectorAll('button')[INDEX].click()")
```

### Cross-Origin Iframe Content (Cloud Consoles)

Chinese cloud consoles (Alibaba Cloud Bailian, Tencent Cloud) and some enterprise SPAs load content in **cross-origin iframes** — the parent page shows only a sidebar, and the actual content is in an iframe from a different domain. `browser_snapshot` shows only "2 iframes, (empty page)".

**Fix — CDP with frame_id from the frame tree:**

```python
# 1. Navigate to the page
browser_navigate(url="https://bailian.console.aliyun.com/...")

# 2. Find the content iframe's frame_id from frame_tree in browser_snapshot
# Look for: frame_tree.children where url matches the content domain

# 3. Read text from the iframe via CDP Runtime.evaluate
browser_cdp(
  frame_id="FRAME_ID_FROM_TREE",
  method="Runtime.evaluate",
  params={"expression": "document.body.innerText.substring(0, 5000)", "returnByValue": true}
)

# 4. Click elements inside the iframe via JS event dispatch
browser_cdp(
  frame_id="FRAME_ID_FROM_TREE",
  method="Runtime.evaluate",
  params={"expression": "el.dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true}))", "returnByValue": true}
)
```

**When to use this pattern:**
- `browser_snapshot` shows only iframes with (empty page) content
- Page URL doesn't change when clicking sidebar items (SPA handled inside iframe)
- Content is from a different origin than the parent page (e.g. `free.aliyun.com` vs `bailian.console.aliyun.com`)

**Pitfall:** Iframes may have multiple copies with the same URL in the frame tree. Pick any — they point to the same content iframe names. Verify by reading body.innerText — if it shows the expected sidebar + main content, you have the right one.

### Multi-Tab CDP Targeting (Critical for Cloud Consoles)

When `browser_navigate` opens a page with multiple tabs, `browser_snapshot` and `browser_console` may silently target the **wrong tab** (e.g., a blank New Tab page). Symptom: `browser_console` returns empty strings or unrelated content. The browser tools have their own tab tracking that may not match the tab you navigated to.

**Fix — explicit target_id via Target.getTargets:**

```python
# 1. List all open tabs
browser_cdp(method="Target.getTargets", params={})
# Returns targetInfos array — find the tab with the right URL

# 2. Query the correct tab directly
browser_cdp(
  method="Runtime.evaluate",
  params={"expression": "document.body.innerText.substring(0, 3000)", "returnByValue": true},
  target_id="TAB_TARGET_ID"  # from step 1
)

# 3. Batch-read table data from the correct tab
browser_cdp(
  method="Runtime.evaluate",
  params={"expression": "Array.from(document.querySelectorAll('table tr')).slice(0,10).map(r => Array.from(r.querySelectorAll('td,th')).map(c => c.textContent.trim()).join(' | ')).join('\\n')", "returnByValue": true},
  target_id="TAB_TARGET_ID"
)
```

**When to use this pattern:**
- `browser_console` returns unrelated text (e.g., "Top site removedUndo" instead of your page content)
- `browser_snapshot` shows an empty page or a different URL than expected
- Multiple tabs are open in the browser (especially a blank New Tab)
- Reading table data from SPA dashboards where `browser_snapshot` truncates

**Pitfall:** The CDP supervisor routes stateless calls through the most recently attached tab. If a New Tab was opened after your target page, it becomes the default. Always verify the tab with `Target.getTargets` first.

### Chinese Cloud Console Batch Operations

Cloud consoles (Alibaba Bailian, Tencent Cloud) often have "batch operation" dropdowns that appear functional but silently do nothing when no items are selected. Key signals:

- **No checkboxes in the table** → batch operation cannot target models. The dropdown exists in the UI but requires manual per-row interaction.
- **Clicking batch options with nothing selected** → page reloads, no confirmation dialog, no status change, no error message
- **Per-row action links are reliable** — each row has its own clickable action (e.g., "免费额度用完即停")
- **Some items may not support the operation** — check for "不支持开启" (unsupported) status before assuming a row can be acted on

**Before clicking batch operations:** verify that (a) checkboxes exist in the table, (b) items are actually selected, and (c) the operation makes sense for the user's intent. Batch operations on cloud consoles can be destructive and irreversible.

**CRITICAL: Never click batch operation buttons without explicit user permission.** Unlike individual per-row actions, batch operations may apply to ALL visible/filtered models without confirmation. Clicking "批量关闭" to test the UI can silently apply an irreversible change to the user's account.

### SPA Navigation: Hash Routing and Tab Params

SPAs like Alibaba Cloud console use two-layer navigation:
1. **Tab parameter** (`?tab=subscribe`) — changes the top-level section
2. **Hash route** (`#/costing-balance/overview`) — changes the sub-page within the section

If `browser_navigate` with hash doesn't work (page shows "页面不存在" / page not found), try changing the `tab` query parameter first, then adding the hash:

```
# WRONG — page not found:
?tab=model#/subscribe

# RIGHT — change tab first:
?tab=subscribe#/subscribe

# OR navigate to the root hash for that tab:
?tab=subscribe  (no hash)
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

### CDP Stale WebSocket / 404 Connection Error

When `browser_navigate` or `browser_cdp` repeatedly fails with `404 Not Found` or `server rejected WebSocket connection: HTTP 404`, but the browser is running and `curl http://localhost:9222/json/list` returns tabs — Hermes has cached a stale WebSocket URL from a previous browser session.

**Symptom:** `lsof -i :9222` shows the port listening and `curl -s http://localhost:9222/json/version` returns valid data, but all Hermes browser tools fail.

**Root cause:** After Brave/Browser restart, the DevTools WebSocket ID changes. Hermes stores the old WS URL internally without refreshing on `/browser connect`.

**Fix sequence (try in this order):**

#### Fix 1: Full restart (fastest, works 90% of the time)

Kill ALL browser processes and re-launch with CDP flag:

```bash
pkill -9 -f "Brave Browser"
sleep 3
open -a "Brave Browser" --args --remote-debugging-port=9222
sleep 3
curl -s http://localhost:9222/json/version
```

After this, Hermes browser tools work again — the old WS URL is gone with the old process.

**Pitfall:** `pkill -9` kills all renderers and extensions. Use `osascript` for a gentler quit when forms/data matter:
```bash
osascript -e 'tell application "Brave Browser" to quit'
sleep 2
open -a "Brave Browser" --args --remote-debugging-port=9222
```

#### Fix 2: Python websockets fallback (when restart is not an option)

Navigate and interact via the `websockets` library directly, bypassing Hermes' internal CDP client:

```python
import asyncio, json, urllib.request, websockets

async def cdp_interact():
    r = urllib.request.urlopen('http://localhost:9222/json/list')
    tabs = json.loads(r.read())
    
    ws_url = None
    for t in tabs:
        if t['type'] == 'page':
            ws_url = t['webSocketDebuggerUrl']
            break
    
    async with websockets.connect(ws_url, max_size=5*1024*1024) as ws:
        cmd = json.dumps({'id': 1, 'method': 'Page.navigate', 'params': {'url': 'https://example.com'}})
        await ws.send(cmd)
        resp = await asyncio.wait_for(ws.recv(), timeout=10)
        await asyncio.sleep(3)
        
        cmd = json.dumps({'id': 2, 'method': 'Runtime.evaluate', 'params': {'expression': 'document.body.innerText'}})
        await ws.send(cmd)
        resp = await asyncio.wait_for(ws.recv(), timeout=10)
        data = json.loads(resp).get('result', {}).get('result', {}).get('value', '')
        return data

asyncio.run(cdp_interact())
```

**Pitfall:** `websockets` library must be installed (`pip install websockets`). Always verify `window.location.href` after navigate — some sites redirect to login/block pages.

**When to use Fix 2:** Only when Hermes tools are consistently failing AND restart is impractical (mid-download, long session). For most cases, Fix 1 (restart) is simpler.

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
- `references/bailian-free-quota.md` — Alibaba Cloud Bailian console free quota page: table structure, protection toggle, batch operation quirks, CDP extraction patterns
