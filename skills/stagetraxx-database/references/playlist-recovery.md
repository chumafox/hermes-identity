# Playlist Recovery Procedures

## Symptom: Playlist exists in SQLite but invisible in Stage Traxx 3

**Cause:** ZPLAYLIST row has NULL ZIDENTIFIER (and/or ZSYNCID). CoreData uses these 16-byte UUID blobs for object identity across sessions. Without them, the app doesn't "see" the playlist.

**Detection:**
```sql
SELECT Z_PK, ZNAME FROM ZPLAYLIST WHERE ZIDENTIFIER IS NULL;
```

**Fix:**
```sql
UPDATE ZPLAYLIST SET
  ZIDENTIFIER = randomblob(16),
  ZSYNCID = COALESCE(ZSYNCID, randomblob(16)),
  ZCOLOR = COALESCE(ZCOLOR, 0),
  ZCONTINUOUS = COALESCE(ZCONTINUOUS, 0),
  ZHIDDEN = COALESCE(ZHIDDEN, 0),
  ZVOLUME = COALESCE(ZVOLUME, 1.0)
WHERE ZIDENTIFIER IS NULL;
```

Also fix orphaned playlist items:
```sql
UPDATE ZPLAYLISTITEM SET
  ZIDENTIFIER = randomblob(16),
  ZAUTOPLAY = COALESCE(ZAUTOPLAY, 0),
  ZLOOP = COALESCE(ZLOOP, 0)
WHERE ZIDENTIFIER IS NULL;
```

## Symptom: Queue was cleared but playlist never created

**Cause:** Old `get_playlist.py` cleared the remote queue before verifying `create_playlist_in_db()` succeeded.

**Recovery:** The data is lost — playlist must be recreated manually. Prevention is the fix (see pitfall #1 in SKILL.md).

## Verification

After running recovery SQL, restart Stage Traxx 3. Fixed playlists should appear in the app immediately.
