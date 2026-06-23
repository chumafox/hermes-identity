# SQLite Direct Access to Apple Notes

When AppleScript is too slow (e.g. 1800+ notes), access NoteStore.sqlite directly.

## Database Location

```
~/Library/Group Containers/group.com.apple.notes/NoteStore.sqlite
```

## Key Tables

- `ZICCLOUDSYNCINGOBJECT` — notes metadata: `ZTITLE` (title), `ZSNIPPET` (preview), `ZADDITIONALINDEXABLETEXT`, `ZSTANDARDIZEDCONTENT`, `ZFOLDER` (folder FK)
- `ZICNOTEDATA` — note body: `ZDATA` (compressed HTML blob, zlib)
- `ZFOLDER` — folder names (join via `ZICCLOUDSYNCINGOBJECT.ZFOLDER`)

## Useful Queries

### List all note titles
```sql
SELECT ZTITLE, Z_PK FROM ZICCLOUDSYNCINGOBJECT 
WHERE ZTITLE IS NOT NULL AND ZTITLE != ''
ORDER BY ZTITLE;
```

### Search notes by title
```sql
SELECT ZTITLE, Z_PK FROM ZICCLOUDSYNCINGOBJECT 
WHERE ZTITLE LIKE '%keyword%';
```

### Search in note content (decompressed)
```python
import sqlite3, zlib, re

conn = sqlite3.connect('NoteStore.sqlite')
cur = conn.cursor()
cur.execute('''
SELECT c.Z_PK, c.ZTITLE, n.ZDATA 
FROM ZICCLOUDSYNCINGOBJECT c
JOIN ZICNOTEDATA n ON c.ZNOTEDATA = n.Z_PK
WHERE n.ZDATA IS NOT NULL AND length(n.ZDATA) > 0
''')
for pk, title, data in cur.fetchall():
    try:
        text = zlib.decompress(data).decode('utf-8', errors='replace')
        if 'keyword' in text.lower():
            print(f'PK={pk} | {title}')
    except:
        pass
```

### List folders with note counts
```sql
SELECT f.ZNAME AS folder, COUNT(c.Z_PK) AS notes
FROM ZFOLDER f
LEFT JOIN ZICCLOUDSYNCINGOBJECT c ON c.ZFOLDER = f.Z_PK
GROUP BY f.Z_PK
ORDER BY notes DESC;
```

## Notes

- Note body is stored as **zlib-compressed HTML** in `ZICNOTEDATA.ZDATA`
- Titles are in `ZICCLOUDSYNCINGOBJECT.ZTITLE`
- `ZSNIPPET` contains a plain-text preview
- Database is SQLite with standard Core Data schema (Z-prefixed tables)
- **Don't write to this DB** — only read. Apple Notes may corrupt if modified externally.
- Close Notes.app before querying to avoid lock conflicts.
