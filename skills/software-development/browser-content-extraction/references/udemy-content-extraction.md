# Udemy Course Content Extraction

## Page Types

Udemy has two main page layouts with different content:

### 1. Course Landing Page (`/course/XXX/`)
Contains: full description, requirements, what-you-learn, instructor bio, course structure with lecture names, durations, preview buttons and "Show lecture description" buttons.

**Preferred for text extraction** — more metadata per page.

### 2. Lecture Player Page (`/course/XXX/learn/lecture/XXXXX`)
Contains: video player, sidebar with course structure, tabs (Overview, Q&A, Notes, Announcements, Reviews).

**Use for:** getting per-lecture text, downloading resources, accessing API data.

---

## API-Based Extraction (Most Reliable)

The lecture player page makes authenticated API calls that return structured JSON. Use the browser's fetch with `credentials:'include'` to reuse the auth session.

### Step 1: Discover Course ID

**Option A — from network requests (on lecture player page):**

```javascript
performance.getEntriesByType('resource')
  .filter(r => r.name.includes('api-2.0'))
  .map(r => ({name: r.name.slice(0, 150), type: r.initiatorType}))
```

Look for URLs matching: `/api-2.0/courses/{COURSE_ID}/...`

**Option B — from public course API (no auth needed):**

```javascript
fetch('/api-2.0/courses/{SLUG}/', {headers:{'Accept':'application/json'}})
  .then(r=>r.json()).then(d=>console.log('Course ID:', d.id))
```
Where `{SLUG}` is the course URL slug (e.g. `romikwvf`).

### Step 1b: Get ALL Lecture IDs at Once

The most efficient way — batch-fetch the full curriculum in a single API call:

```javascript
fetch('/api-2.0/courses/{COURSE_ID}/subscriber-curriculum-items/' +
  '?curriculum_types=lecture&page_size=200&fields[lecture]=id,title,object_index,asset,description',
  {credentials:'include', headers:{'Accept':'application/json'}})
.then(r=>r.json())
.then(d => {
  const lectures = d.results.map(r => ({
    id: r.id,
    title: r.title,
    index: r.object_index,
    desc: (r.description || '').replace(/<[^>]+>/g, '').trim()
  }));
  console.log(JSON.stringify(lectures, null, 2));
})
```

This returns ALL lecture IDs, titles, and descriptions in one response. The `object_index` field maps to lecture number.

### Step 1c: Batch-Fetch Lecture Descriptions

If descriptions need individual API calls (e.g. they were empty in the curriculum response):

```javascript
const ids = [LECTURE_ID_1, LECTURE_ID_2, LECTURE_ID_3];
Promise.all(ids.map(id =>
  fetch('/api-2.0/users/me/subscribed-courses/{COURSE_ID}/lectures/' + id +
    '/?fields[lecture]=id,title,description,asset',
    {credentials:'include', headers:{'Accept':'application/json'}})
  .then(r=>r.json())
)).then(results => results.map(r => ({
  id: r.id, title: r.title,
  desc: (r.description || '').replace(/<[^>]+>/g, '').trim(),
  duration: 0  // duration comes from asset endpoint, not here
})))
```

⚠️ **Pitfall:** `Promise.all` with 5+ simultaneous fetches may time out. Batch in groups of 2-3 for reliability. Use sequential fetching if you encounter `CancelledError`.

### Step 2: Get Lecture Metadata

```javascript
fetch('/api-2.0/users/me/subscribed-courses/{COURSE_ID}/lectures/{LECTURE_ID}/' +
  '?fields[lecture]=asset,description,download_url,is_free,last_watch_time,supplementary_assets',
  {credentials:'include', headers:{'Accept':'application/json'}})
.then(r=>r.json())
.then(d => console.log(JSON.stringify(d, null, 2)))
```

**Response shape:**
- `description` — HTML string with lecture description
- `asset` — `{_class, id, asset_type, title, created}` (asset_id for further queries)
- `download_url` — empty string for DRM-protected content
- `is_free` — boolean
- `supplementary_assets` — PDF/download list (often empty)

### Step 3: Get Asset Details (for Duration & Metadata)

The lecture API response may NOT include `asset.length` (duration). You need a separate call to the asset endpoint:

```javascript
fetch('/api-2.0/assets/{ASSET_ID}/',
  {credentials:'include', headers:{'Accept':'application/json'}})
.then(r=>r.json())
.then(d => console.log(JSON.stringify(d, null, 2)))
```

**Response shape:** `{_class, id, asset_type, title, created, title_cleaned, description, length (seconds), status}`

The `length` field is the video duration in seconds (e.g. 727 = 12:07). The `status` field indicates processing state (1 = ready).

### Available API Endpoints (from observed network traffic)

| Endpoint | Purpose |
|----------|---------|
| `/api-2.0/users/me/subscribed-courses/{CID}/lectures/{LID}/?fields[...]` | Lecture details + asset |
| `/api-2.0/assets/{AID}/` | Asset metadata |
| `/api-2.0/courses/{CID}/subscriber-curriculum-items/?curriculum_types=lecture&page_size=200&fields[lecture]=id,title,object_index,asset,description` | Full curriculum list (IDs + titles + descriptions in one call) |
| `/api-2.0/assets/{AID}/` | Asset metadata including `length` (duration in seconds) |
| `/api-2.0/users/me/subscribed-courses/{CID}/lectures/{LID}/view-logs/` | View tracking (POST) |
| `/api-2.0/users/me/subscribed-courses/{CID}/notes/` | Student notes |
| `/api-2.0/users/me/enrollments/{CID}/` | Enrollment status |

---

## Video URL Extraction via Performance API

**This works despite Widevine DRM.**  
When the video player loads, the browser fetches the MP4 directly (as `initiatorType: "video"`), and the URL persists in resource timing entries.

### Method

```javascript
// On the lecture player page, wait ~8s for player to load
performance.getEntriesByType('resource')
  .filter(r => r.name.includes('mp4-cdn') && r.name.includes('WebHD'))
  .map(r => r.name)
```

**URL format:**
```
https://mp4-cdnXX.udemycdn.com/{DATE}-{HASH}/2/WebHD_720p.mp4?secure={TOKEN}%2C{TIMESTAMP}
```

### Download

```bash
curl -L -C - -o lecture.mp4 \
  -H "Referer: https://www.udemy.com/" \
  -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
  --cookie "__udmy_2_v57r=xxx; csrftoken=xxx; ud_cache_logged_in=1; ud_cache_user=USERID" \
  "https://mp4-cdnXX.udemycdn.com/.../WebHD_720p.mp4?secure=..."
```

`-C -` resumes interrupted downloads. URL token lives ~1 hour after load.

## DRM Protection

Udemy uses **Widevine DRM** — the video element gets a `blob:` URL via MSE, and direct `video.src` returns nothing useful.

### What Does NOT Work

| Method | Failure mode |
|--------|-------------|
| `yt-dlp` | HTTP 403 — Udemy blocks automated tools |
| Browser MediaRecorder `captureStream()` | Cross-origin error — video served from CDN |
| Cookie export → yt-dlp | Brave encrypts cookies with macOS Keychain (AES-256-GCM). Newer Brave versions store encrypted cookies in `encrypted_value` column; `value` column is empty. |
| Direct `video.src` | Returns `blob:` URL, not downloadable |
| CDP-created new tabs | New tabs via `PUT /json/new` have NO auth session — the logged-in cookies don't carry over |

## Automation via CDP WebSocket

For bulk downloading, automate lecture navigation + URL extraction through Brave's CDP WebSocket.

### Prerequisites

```bash
pip install websocket-client

# Brave must start with these flags:
"/Applications/Brave Browser.app/Contents/MacOS/Brave Browser" \
  --remote-debugging-port=9222 \
  --remote-allow-origins=*
```

The `--remote-allow-origins=*` flag is required for Python WebSocket connections (otherwise Brave rejects with 403). Without it, Python's `websocket` library can't authenticate.

### WebSocket CDP Implementation

```python
import json, websocket, time, http.client

# 1. Get a tab that's already logged into Udemy (find by URL)
conn = http.client.HTTPConnection("127.0.0.1", 9222, timeout=5)
conn.request("GET", "/json")
tabs = json.loads(conn.getresponse().read())
conn.close()

# Find a tab with Udemy logged in, or use the first available
target = next((t for t in tabs if "udemy" in t.get("url", "")), tabs[0])
ws_url = target["webSocketDebuggerUrl"]

ws = websocket.create_connection(ws_url, timeout=10)

# Helper to evaluate JS and get result by ID
def js(expr, timeout=5):
    ws.send(json.dumps({"id": 99, "method": "Runtime.evaluate", 
                        "params": {"expression": expr}}))
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            ws.settimeout(deadline - time.time())
            msg = json.loads(ws.recv())
            if msg.get("id") == 99:
                return msg.get("result", {}).get("result", {}).get("value", "")
        except:
            break
    return ""

# 2. Navigate to lecture
ws.send(json.dumps({
    "id": 1, "method": "Page.navigate",
    "params": {"url": "https://www.udemy.com/course/SLUG/learn/lecture/LECTURE_ID"}
}))

# 3. Wait for page load
deadline = time.time() + 20
while time.time() < deadline:
    try:
        ws.settimeout(3)
        msg = json.loads(ws.recv())
        if msg.get("method") == "Page.frameStoppedLoading":
            break
    except:
        break

# 4. Poll for video URL in Performance API
time.sleep(8)
deadline = time.time() + 30
while time.time() < deadline:
    raw = js("JSON.stringify(performance.getEntriesByType('resource')" +
             ".filter(r => r.name.includes('mp4-cdn') && r.name.includes('WebHD'))" +
             ".map(r => r.name))")
    if raw and raw != "[]":
        urls = json.loads(raw)
        if urls:
            video_url = urls[0]
            break
    time.sleep(3)

ws.close()
```

### Critical: Double-Nested CDP Response

The response from `Runtime.evaluate` has a double-nested structure:

```json
{
  "id": 99,
  "result": {
    "result": {
      "type": "string",
      "value": "[\"https://...\"]"
    }
  }
}
```

Access it as: `msg["result"]["result"]["value"]` — NOT `msg["result"]["value"]`. A common bug is reading one level too shallow, which returns `None` and makes every expression look like it failed.

The `js()` helper above handles this correctly with `msg.get("result", {}).get("result", {}).get("value", "")`.

### Pitfalls

- **Udemy anti-bot detection**: When the page is loaded via CDP, Udemy may refuse to render the video player (shows "Loading" forever). The Performance API still captures the video URL if the video pre-fetch succeeds, but this isn't guaranteed.
- **Session lost on Brave restart**: If Brave is killed and restarted with `--remote-allow-origins=*`, the new instance may not have the user's Udemy login. The user must log in again or restore their session.
- **No video URL**: If the lecture hasn't been previously visited in the same Brave window, the Performance API may be empty. Try visiting the lecture manually first, then running the script.
- **Performance buffer cleared**: Navigating between lectures may clear the resource timing buffer. Only URLs loaded after the navigation will appear. Keep checks frequent.
- **WebSocket 403**: If Brave is started without `--remote-allow-origins=*`, all WebSocket connections are rejected. Check `ps aux | grep Brave` for running flags.

### CDP Page.navigate Triggers Anti-Bot

**CDP `Page.navigate` is detected by Udemy.** The video player renders but never loads media (readyState stays 0). Use AppleScript instead to navigate the existing tab — it looks like a real user:

```python
# Navigate via AppleScript (bypasses CDP detection):
script = f'''
tell application "Brave Browser"
    activate
    tell window 1
        set URL of active tab to "{url}"
    end tell
end tell
'''
subprocess.run(["osascript", "-e", script], capture_output=True, timeout=10)

# Then ~20s later, extract URL via CDP WebSocket (read-only, no navigation)
```

**Key difference:** `set URL of active tab` reuses the existing tab (keeps session). `open location` opens a NEW tab (loses session context). Always use `set URL of active tab` when the user already has a logged-in tab.

### Multi-Tab Scanning

The active tab (navigated by AppleScript) may not be the first tab in the CDP listing. Scan ALL tabs:

```python
for tab in tabs:
    if "udemy.com/course" not in tab.get("url", ""):
        continue
    # Check this tab's Performance API for mp4-cdn URL
```

Filter by `"udemy.com/course"` (not just `"udemy"`) to skip marketing/service-worker tabs.

### Cookie Encryption on Modern Chrome/Brave

Brave stores cookies in a SQLite DB at:
```
~/Library/Application Support/BraveSoftware/Brave-Browser/Default/Cookies
```

The `value` column is **empty** — real values are in `encrypted_value` (AES-256-GCM with macOS Keychain). Direct SQLite queries return only encrypted blobs. **Always use `document.cookie` from the browser** to get readable cookies.

### Full Automation Script

See `~/udemy-aging-course/udemy-dl.py` for a complete implementation that:
- Loops over 43 lectures with names + IDs embedded as data
- Connects to existing Brave tab (picks the one with Udemy open)
- Navigates to each lecture, polls for video URL
- Downloads with curl with resume support (`-C -`)
- Skips already-downloaded files (>10 MB)
- Reports success/failure per-lecture
- Supports `--audio-only`, `--resume`, `--dry-run`, `--lectures 1,5,10` flags

### Script Structure

```python
LECTURES = [
    (1, 31793264, "01-pochemu-my-stareem"),
    (2, 31805430, "02-analizy-dlya-otsenki-zdorovya"),
    # ... all 43
]

for num, lid, name in LECTURES:
    url = get_video_url_cdp(lid)
    if url:
        curl_cmd = ["curl", "-L", "-C", "-", "-o", f"{name}.mp4",
                    "-H", "Referer: https://www.udemy.com/",
                    "--cookie", "ud_cache_logged_in=1;...",
                    url]
        subprocess.run(curl_cmd)
```

## What DOES Work

1. **Performance API** (preferred) — extract MP4 URL from `performance.getEntriesByType('resource')` as described above. This is a direct CDN URL with auth token. Works for downloading the full file.

2. **BlackHole audio loopback** (fallback for when URL expires) — capture system audio output:

```bash
brew install blackhole-2ch
# Configure: Audio MIDI Setup → Multi-Output Device (BlackHole + speakers)
ffmpeg -f avfoundation -i ":<BlackHole_index>" -ac 1 -codec:a libmp3lame output.mp3
```

## Automation Script

For bulk download of all lectures, use `~/udemy-aging-course/udemy-dl.py`:
- Navigates each lecture in CDP browser
- Extracts URL from Performance API
- Downloads via curl with resume
- Skips already-completed files (>10MB)
- Named output: `01-lecture-name.mp4`
- Audio-only mode (`-a`), dry-run (`-d`)

## Known Lecture IDs (romikwvf, Course 4637836)

| # | ID | Name |
|---|-----|------|
| 1  | 31793264 | Почему мы стареем |
| 2  | 31805430 | Анализы для оценки здоровья |
| 3  | 31805598 | УЗИ, допплер, ЭКГ |
| 4  | 31805616 | Онкомаркеры |
| 5  | 31805760 | Максимальное потребление кислорода |
| 6  | 31805814 | Идеальная диета |
| 7  | 31805824 | Интервальное голодание |
| 8  | 31805920 | Алкоголь |
| 9  | 31805964 | Кофе |
| 10 | 31806102 | Физнагрузки для долголетия |
| 11 | 31806368 | Суставы |
| 12 | 31806454 | Сауна и баня |
| 13 | 31807316 | Теломеры |
| 14 | 31807324 | NMN |
| 15 | 31807378 | Ресвератрол |
| 16 | 31807384 | Кверцетин |
| 17 | 31807460 | Фисетин |
| 18 | 31807480 | Метформин |
| 19 | 31807496 | Куркумин |
| 20 | 31807634 | Глутатион |
| 21 | 31807668 | Альфа липоевая кислота |
| 22 | 31807680 | Совмещение средств |
| 23 | 31807702 | Гормональная терапия |
| 24 | 31807704 | Ашваганда и сон |
| 25 | 31807710 | Биологический возраст |
| 26 | 39347530 | N-ацетилцистеин + глицин |
| 27 | 40817042 | Крем от старения кожи |
| 28 | 41797154 | Диета имитирующая голодание |
| 29 | 43738734 | Липидограмма |
| 30 | 43739072 | Нормы липидограммы |
| 31 | 43742974 | Аполипопротеин В |
| 32 | 43751938 | Бляшки в сосудах |
| 33 | 43849692 | Уменьшение бляшек |
| 34 | 43850198 | Нагрузки для липопротеинов |
| 35 | 43850626 | Клетчатка |
| 36 | 43851272 | Диета для LDL |
| 37 | 43851584 | Бета ситостерол |
| 38 | 43851848 | Экстракт бергамота |
| 39 | 43857644 | Берберин |
| 40 | 43857964 | Омега-3 |
| 41 | 43859454 | Факторы риска |
| 42 | 43862790 | Оценка результатов |
| 43 | 31807716 | Заключение |

---

## Expanding All Sections

On the landing page, click "Expand all sections" first:

```python
browser_click(ref=eXX)  # Where eXX is the "Expand all sections" button ref
```

Then expand individual sections if needed:

```python
browser_console(expression="Array.from(document.querySelectorAll('button')).slice(1,6).forEach(b => { if(b.getAttribute('aria-expanded')==='false') b.click(); }); 'done'")
```

---

## Known Limitations

- **"Show lecture description" buttons**: These load content via API call. The browser's accessibility tree shows them but JS can't always select them (possibly Shadow DOM). Use the API method above instead.
- **Lecture durations on landing page**: Section 1 shows durations. Section 2+ may not show per-lecture durations until expanded on the lecture player page.
- **Downloadable resources**: Must be accessed from within each lecture's page (click "Resources" button in sidebar). The `supplementary_assets` endpoint may be empty — try the sidebar button.

---

## Example URL Patterns

```
Course landing:    https://www.udemy.com/course/{SLUG}/
Lecture player:    https://www.udemy.com/course/{SLUG}/learn/lecture/{LECTURE_ID}#overview
```
