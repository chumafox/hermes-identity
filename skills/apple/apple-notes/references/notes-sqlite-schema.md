# Apple Notes SQLite Schema Reference

Database: `~/Library/Group Containers/group.com.apple.notes/NoteStore.sqlite`

## Key Tables

### ZICCLOUDSYNCINGOBJECT — notes metadata

| Column | Type | Description |
|--------|------|-------------|
| Z_PK | INTEGER | Primary key |
| ZTITLE | VARCHAR | Note title |
| ZSNIPPET | VARCHAR | Preview snippet |
| ZSTANDARDIZEDCONTENT | VARCHAR | Indexed text content |
| ZADDITIONALINDEXABLETEXT | VARCHAR | Additional searchable text |
| ZFOLDER | INTEGER | FK to folder |
| ZNOTEDATA | INTEGER | FK to ZICNOTEDATA |
| ZMODIFICATIONDATE1 | TIMESTAMP | Last modified |
| ZCREATIONDATE3 | TIMESTAMP | Created |

### ZICNOTEDATA — compressed note body

| Column | Type | Description |
|--------|------|-------------|
| Z_PK | INTEGER | Primary key |
| ZNOTE | INTEGER | FK to ZICCLOUDSYNCINGOBJECT |
| ZDATA | BLOB | zlib-compressed UTF-8 HTML |

### ZICCLOUDSYNCINGOBJECT (folders)

Same table — folders have ZFOLDERTYPE set and ZNOTE is NULL.

## Useful Queries

### Find a note by title
```sql
SELECT ZTITLE, Z_PK, ZSNIPPET 
FROM ZICCLOUDSYNCINGOBJECT 
WHERE ZTITLE LIKE '%keyword%';
```

### Find a note by content (snippet/index)
```sql
SELECT ZTITLE, Z_PK 
FROM ZICCLOUDSYNCINGOBJECT 
WHERE ZSNIPPET LIKE '%keyword%' 
   OR ZSTANDARDIZEDCONTENT LIKE '%keyword%';
```

### Find a note by full body text (zlib decompressed)
```python
import sqlite3, zlib, re
conn = sqlite3.connect('NoteStore.sqlite')
cur = conn.cursor()
cur.execute('''
  SELECT c.ZTITLE, n.ZDATA 
  FROM ZICCLOUDSYNCINGOBJECT c
  JOIN ZICNOTEDATA n ON c.ZNOTEDATA = n.Z_PK
  WHERE n.ZDATA IS NOT NULL AND length(n.ZDATA) > 0
''')
for row in cur.fetchall():
    try:
        text = zlib.decompress(row[1]).decode('utf-8', errors='replace')
        if re.search(r'keyword', text, re.IGNORECASE):
            print(f'Found in: {row[0]}')
    except: pass
```

### Count notes per folder
```sql
SELECT f.ZTITLE AS folder, COUNT(n.Z_PK) AS note_count
FROM ZICCLOUDSYNCINGOBJECT f
LEFT JOIN ZICCLOUDSYNCINGOBJECT n ON n.ZFOLDER = f.Z_PK
WHERE f.ZFOLDERTYPE IS NOT NULL
GROUP BY f.Z_PK
ORDER BY note_count DESC;
```
