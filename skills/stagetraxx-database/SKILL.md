---
name: stagetraxx-database
description: Stage Traxx 3 SQLite database operations — playlist creation, cross-Mac sync (Air ↔ Mac Pro), CoreData schema, and data recovery. Covers get_playlist.py, server.py, ui_server.py, and the mastering project.
---

# Stage Traxx 3 Database Operations

## Schema Overview

Stage Traxx 3 stores everything in a CoreData-backed SQLite database at:
```
~/Library/Containers/de.dikant.stagetraxx3/Data/Library/Application Support/Stage Traxx 3/stagetraxx3.sqlite
```

Audio files live at:
```
~/Library/Containers/de.dikant.stagetraxx3/Data/Documents/
```

### Key Tables

| Table | Z_ENT | Purpose |
|-------|-------|---------|
| ZSONG | — | Tracks (title, artist, file URL) |
| ZSONGDATA | — | Lyrics, metadata |
| ZPLAYLIST | 1 | Playlists |
| ZPLAYLISTITEM | 2 | Playlist → Song join table |
| ZTRACK | — | Additional track metadata |
| Z_PRIMARYKEY | — | CoreData sequence counter |

### ZPLAYLIST Schema

```sql
CREATE TABLE ZPLAYLIST (
  Z_PK INTEGER PRIMARY KEY,
  Z_ENT INTEGER,
  Z_OPT INTEGER,
  ZCOLOR INTEGER,
  ZCONTINUOUS INTEGER,
  ZHIDDEN INTEGER,
  ZCREATED TIMESTAMP,
  ZVOLUME FLOAT,
  ZNAME VARCHAR,
  ZIDENTIFIER BLOB,    -- REQUIRED: 16-byte UUID blob
  ZSYNCID BLOB         -- REQUIRED: 16-byte UUID blob
);
```

### ZPLAYLISTITEM Schema

```sql
CREATE TABLE ZPLAYLISTITEM (
  Z_PK INTEGER PRIMARY KEY,
  Z_ENT INTEGER,
  Z_OPT INTEGER,
  ZAUTOPLAY INTEGER,
  ZLOOP INTEGER,
  ZSORTORDER INTEGER,
  ZPLAYLIST INTEGER,      -- FK → ZPLAYLIST.Z_PK
  ZSONG INTEGER,          -- FK → ZSONG.Z_PK
  ZSOURCEPLAYLIST INTEGER,
  ZADDED TIMESTAMP,
  ZIDENTIFIER BLOB        -- REQUIRED: 16-byte UUID blob
);
```

## CRITICAL: ZIDENTIFIER Blob

**Without ZIDENTIFIER, CoreData objects are invisible to the app.** The playlist exists in SQLite but Stage Traxx 3 won't display it after restart. This is the #1 cause of "playlists disappear."

Always generate and insert:
```python
import uuid
identifier = uuid.uuid4().bytes  # 16-byte binary blob
```

Same for ZSYNCID in ZPLAYLIST.

## CLI Commands (`get_playlist.py`)

The script doubles as a sync tool and a playlist management CLI. Run from the Air side:

```bash
cd ~/Projects/active/audio/stagetraxx-server && uv run python get_playlist.py
```

### `uv run python get_playlist.py` (no args)
Default mode: fetch queued playlists from Mac Pro → create in local SQLite → clear queue → sync songs snapshot up.

### `--list`
List all playlists with track counts:

```bash
uv run python get_playlist.py --list
# Playlists (21):
#   [559] 1Jul (26 tracks)
#   [562] My Playlist (28 tracks)
```

### `--delete NAME_OR_ID`
Delete a playlist by name (partial match) or Z_PK. If multiple match, shows list and asks for exact PK:

```bash
uv run python get_playlist.py --delete "My Playlist"
uv run python get_playlist.py --delete 562
```

Deletes ZPLAYLISTITEM rows first (FK constraint), then ZPLAYLIST row.

### `--clear`
Delete ALL playlists at once. Wipes ZPLAYLISTITEM then ZPLAYLIST.

```bash
uv run python get_playlist.py --clear
```

Also available as a standalone command:
```bash
clear-plst
# → ~/bin/clear-plst: cd ~/Projects/active/audio/stagetraxx-server && uv run python get_playlist.py --clear
```

## Architecture: Two-Mac Sync

```
Air (dispo, local)                    Mac Pro (192.168.103.70)
┌──────────────────┐                  ┌──────────────────────┐
│ get_playlist.py  │  POST /api/sync  │ ui_server.py (port   │
│ (uv run)         │ ◄──────────────► │ 5555)                │
│                  │  GET /api/queue  │                      │
│ create_playlist  │  DELETE /api/queue│ data/queue.json     │
│ → local SQLite   │                  │ data/songs_snapshot  │
└──────────────────┘                  └──────────────────────┘
```

1. `get-playlist` (alias: `uv run get_playlist.py`) syncs songs UP to Mac Pro, then fetches queued playlists DOWN
2. Web UI on Mac Pro creates playlists into `data/queue.json`
3. `get-playlist` reads queue, creates playlists in local SQLite, then clears queue

## Creating a Playlist (SQL)

```python
import time, uuid

coredata_time = time.time() - 978307200  # Mac Absolute Time (seconds since Jan 1 2001)

# Get next PK
cursor.execute("SELECT Z_MAX FROM Z_PRIMARYKEY WHERE Z_ENT=1")
playlist_id = cursor.fetchone()[0] + 1

# Insert playlist
cursor.execute("""
  INSERT INTO ZPLAYLIST (Z_PK, Z_ENT, Z_OPT, ZCOLOR, ZCONTINUOUS, ZHIDDEN,
                         ZNAME, ZCREATED, ZVOLUME, ZIDENTIFIER, ZSYNCID)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (playlist_id, 1, 1, 0, 0, 0, name, coredata_time, 1.0,
      uuid.uuid4().bytes, uuid.uuid4().bytes))

# Update sequence
cursor.execute("UPDATE Z_PRIMARYKEY SET Z_MAX=? WHERE Z_ENT=1", (playlist_id,))
```

## Recovery

See `references/playlist-recovery.md` for step-by-step procedures to fix invisible playlists (missing ZIDENTIFIER) and handle queue-loss scenarios.

## Lyrics: Fetching & Storing

### Script Landscape

There are multiple scripts for lyrics, scattered across two locations:

| Script | Location | Method | Annie filter? | Status |
|--------|----------|--------|---------------|--------|
| `fetch_lyrics.py` | `~/Projects/active/audio/stagetraxx-server/` | DB query → ID3 → lrclib.net → write ZSONGDATA | ✅ Yes | Active/maintained |
| `fix_titles.py` | `~/scripts/` | Cleans ZSONG.ZTITLE in DB (removes minus, instrumental, etc.) | ❌ No | Needs Annie filter |
| `download_lyrics.py` | `~/Originals/` | File-based: scans Documents/ → lrclib.net → saves .txt | ❌ No | Legacy |
| `fetch_remaining_lyrics.py` | `~/Originals/` | File-based: scans Documents/ → DeepSeek API → saves .txt | ❌ No | Legacy |
| `restore_annie.py` | `~/scripts/` | Restores titles from backup + re-cleans via `clean_db_title()` | N/A | Recovery tool |

**Key insight:** Only `fetch_lyrics.py` (in stagetraxx-server) filters Annie from titles. The other scripts (`fix_titles.py`, `download_lyrics.py`) do NOT — if run, they'll search with "Annie" in the query and fail to find matches.

### Annie/SUNO Filtering (REQUIRED for any title-cleanup script)

Stage Traxx tracks often have "Annie" or "SUNO" appended to the title (e.g. "My Heart Will Go On Annie", "Killing Me Softly SUNO"). These must be stripped before searching for lyrics:

```python
# Remove trailing "Annie" or "SUNO" (whole word at end, case-insensitive)
t = re.sub(r'\s+Annie\s*$', '', t, flags=re.IGNORECASE)
t = re.sub(r'\s+SUNO\s*$', '', t, flags=re.IGNORECASE)
# Handle case where title IS just "Annie" or "SUNO"
t = re.sub(r'^Annie\s*$', '', t, flags=re.IGNORECASE)
t = re.sub(r'^SUNO\s*$', '', t, flags=re.IGNORECASE)
```

Also remove other common suffixes: `.mp3`, `.m4a`, parenthesized notes `(minus)`, `(normal)`, `(minus 3)`, bracketed notes `[...]`, leading numbers, `_` → space.

### Primary Pipeline (`fetch_lyrics.py`)

```bash
cd ~/Projects/active/audio/stagetraxx-server && uv run fetch_lyrics.py
```

1. Query `ZSONG` LEFT JOIN `ZSONGDATA` — find tracks where `ZLYRICS IS NULL OR ''`
2. For each track:
   a. **ID3 tags first** — read `USLT` frame from `.mp3` or `©lyr` from `.m4a` via mutagen
   b. **If no ID3** — search via **Volcengine DeepSeek API** (primary, works from China)
   c. **Fallback** — lrclib.net for synced lyrics
   d. Insert/update `ZSONGDATA.ZLYRICS`
3. Strips proxy env vars (`ALL_PROXY`, `HTTP_PROXY`, etc.) before curl calls

### API: Volcengine DeepSeek (primary, works from China)

```
POST https://ark.cn-beijing.volces.com/api/coding/v1/chat/completions
Authorization: Bearer $VOLC_CODING_API_KEY
```

Model: `deepseek-v4-flash`. Prompt: ask for full lyrics, output ONLY lyrics text or `NOT_FOUND`.

**Critical:** Must use `curl` via `subprocess.run()` with stripped proxy env, NOT `urllib.request` — `ALL_PROXY=socks5://127.0.0.1:1080` breaks urllib SSL/DNS from China.

```python
clean_env = {k: v for k, v in os.environ.items()
             if not k.upper().endswith('_PROXY') and not k.lower().endswith('_proxy')}

result = subprocess.run(
    ["curl", "-s", "--max-time", "25", API_URL,
     "-H", "Content-Type: application/json",
     "-H", f"Authorization: Bearer {API_KEY}",
     "-d", payload],
    capture_output=True, text=True, timeout=30, env=clean_env
)
```

DeepSeek finds lyrics for ~60% of popular songs. Instrumentals, rare tracks, and Chinese-only songs are more likely to return NOT_FOUND.

### Fallback: lrclib.net (synced lyrics)

```
GET https://lrclib.net/api/get?artist_name={artist}&track_name={title}
```

Returns JSON with `plainLyrics` field. Used as secondary source when DeepSeek returns nothing.

### ZSONGDATA Schema

```sql
CREATE TABLE ZSONGDATA (
  Z_PK INTEGER PRIMARY KEY,
  Z_ENT INTEGER,      -- 5 for SongData
  Z_OPT INTEGER,
  ZSONG INTEGER,      -- FK → ZSONG.Z_PK
  ZLYRICS VARCHAR,
  ZWAVEFORMDATA BLOB
);
```

Z_PRIMARYKEY for SongData: `Z_ENT = 5`

### Insert/Update Logic

```python
# Check if row exists
existing = cursor.execute("SELECT Z_PK FROM ZSONGDATA WHERE ZSONG = ?", (pk,)).fetchone()

if existing:
    cursor.execute("UPDATE ZSONGDATA SET ZLYRICS = ? WHERE ZSONG = ?", (lyrics, pk))
else:
    cursor.execute("SELECT Z_MAX FROM Z_PRIMARYKEY WHERE Z_ENT = 5")
    new_pk = cursor.fetchone()[0] + 1
    cursor.execute("INSERT INTO ZSONGDATA (Z_PK, Z_ENT, Z_OPT, ZSONG, ZLYRICS) VALUES (?, ?, ?, ?, ?)",
                   (new_pk, 5, 1, pk, lyrics))
    cursor.execute("UPDATE Z_PRIMARYKEY SET Z_MAX = ? WHERE Z_ENT = 5", (new_pk,))
```

### Pitfalls

- **ALL_PROXY env var** breaks `requests` (SOCKS dependency). Script unsets proxy vars at startup.
- **mutagen** is only available inside `uv run` venv, not system python.
- **lrclib.net** may occasionally timeout from China — retry or skip gracefully.
- **ID3 USLT frames** take priority over API — if user already embedded lyrics in file, don't overwrite.
- **Skip tracks that already have ZLYRICS** — check before processing.

### 1. Queue cleared before verification
Old `get_playlist.py` cleared the remote queue even if `create_playlist_in_db()` failed. **Always verify success before clearing queue.** Use a flag:
```python
all_success = True
for req in queue:
    try:
        create_playlist_in_db(name, tracks)
    except Exception as e:
        all_success = False
if all_success:
    requests.delete(f"{MACPRO_URL}/api/queue")
```

### 2. Missing ZIDENTIFIER → invisible playlists
Every ZPLAYLIST and ZPLAYLISTITEM needs a `uuid.uuid4().bytes` in ZIDENTIFIER. ZPLAYLIST also needs ZSYNCID.

### 3. Missing ZAUTOPLAY/ZLOOP on items
ZPLAYLISTITEM needs `ZAUTOPLAY=0, ZLOOP=0` for default behavior.

### 4. Renaming files without updating DB
Never rename audio files without updating `ZSONG.ZFILEURL`. Stage Traxx 3 hardcodes physical paths. A rename without DB update breaks the track (red in UI, unplayable).

### 5. Backup before mass updates
```bash
cp "$DB_PATH" "$DB_PATH.backup.$(date +%Y%m%d)"
```

### 6. CoreData merge conflict after SQLite deletion (`NSMergeConflict`, `newVersion = <deleted>`)

If you delete playlists from SQLite (via `--delete`, `--clear`, or direct SQL) **while Stage Traxx 3 is running**, the app still holds the deleted objects in memory. When a track finishes and CoreData tries to save changes (e.g. `volume`, `continuous`), it detects the object was deleted externally and crashes:

```
Unresolved error Error Domain=NSCocoaErrorDomain Code=133020 "Could not merge changes."
NSMergeConflict for NSManagedObject ... with oldVersion = 1 and newVersion = <deleted>
```

**Fix:** Close Stage Traxx 3 before running `--clear` or `--delete`. Or restart the app after deletion — in-memory cache resets and the error stops.

**Recovery:** If the deleted playlist was important, re-create it via the web UI or SQL. The error itself is harmless — it only means the app couldn't save the in-memory state of a now-deleted object.

## Web UI (index.html)

The web UI at `~/Projects/active/audio/stagetraxx-server/templates/index.html` is served by `ui_server.py` on port 5555.

### Playlist Area Height

The right panel (playlist configuration) uses `flex flex-col h-[80vh]`. To fit 15+ tracks without scrolling, keep elements compact:

- **Right panel padding:** `p-4` (not p-6)
- **Title:** `text-xl font-bold mb-3` (not text-2xl, mb-4)
- **Name input:** `px-3 py-2 text-sm` (not px-4 py-3)
- **Track items (JS):** `p-2 text-xs space-y-1` (not p-3 text-sm space-y-2)
- **Create button:** `py-3 text-base` (not py-4 text-lg)
- **SVG icons in track items:** `w-4 h-4` (not w-5 h-5)

### Pitfall: `print()` in Flask background process → BrokenPipeError

When `ui_server.py` runs in the background (stdout not connected to a terminal), `print()` calls crash with `BrokenPipeError: [Errno 32] Broken pipe`. Flask catches this and returns a 500 HTML page instead of JSON, which causes the frontend `response.json()` to fail with "The string did not match the expected pattern."

**Fix:** always use `file=sys.stderr` for debug prints in Flask background processes:

```python
import sys
print("message", file=sys.stderr)
```

Or use Flask's logger:
```python
app.logger.info("message")
```

### Deployment

After editing `index.html` or `ui_server.py`, restart the server on the Mac Pro:
```bash
ssh jenyanovak@192.168.103.70 "cd ~/Projects/active/audio/stagetraxx-server && uv run ui_server.py"
```

**If SSH is unavailable** (connection closed, auth failure):
- The server process is still running — it won't pick up code changes until restarted
- Alternative delivery methods: copy via shared filesystem, USB drive, or restart the server process through a different mechanism (e.g. if launched via launchd, use `launchctl`)

## Project Files

- `~/Projects/active/audio/stagetraxx-server/get_playlist.py` — sync script (Air side)
- `~/Projects/active/audio/stagetraxx-server/server.py` — direct DB write server (Mac Pro, old)
- `~/Projects/active/audio/stagetraxx-server/ui_server.py` — queue-based server (Mac Pro, current)
- `~/Projects/active/audio/stage-traxx-mastering/master.py` — audio mastering (EQ + loudness)

Alias: `get-playlist` → `uv run ~/Projects/active/audio/stagetraxx-server/get_playlist.py`
