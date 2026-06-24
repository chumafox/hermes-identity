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

## Pitfalls

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

## Project Files

- `~/Projects/active/audio/stagetraxx-server/get_playlist.py` — sync script (Air side)
- `~/Projects/active/audio/stagetraxx-server/server.py` — direct DB write server (Mac Pro, old)
- `~/Projects/active/audio/stagetraxx-server/ui_server.py` — queue-based server (Mac Pro, current)
- `~/Projects/active/audio/stage-traxx-mastering/master.py` — audio mastering (EQ + loudness)

Alias: `get-playlist` → `uv run ~/Projects/active/audio/stagetraxx-server/get_playlist.py`
