---
name: apple-notes
description: "Manage Apple Notes via memo CLI: create, search, edit."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [Notes, Apple, macOS, note-taking]
    related_skills: [obsidian]
prerequisites:
  commands: [memo]
fallback:
  - osascript (built-in, slow on 1000+ notes)
  - sqlite3 (fast, direct DB access)
---

# Apple Notes

Use `memo` CLI, AppleScript (osascript), or direct SQLite to manage Apple Notes. Notes sync across all Apple devices via iCloud.

## Prerequisites

- **macOS** with Notes.app
- **Preferred:** `brew tap antoniorodr/memo && brew install antoniorodr/memo/memo`
- Grant Automation access to Notes.app when prompted (System Settings → Privacy → Automation)

## Fallback Methods (when memo not installed)

### ⚠️ Performance Warning

AppleScript iterating ALL notes via `every note` **times out** on 1000+ notes (30s+). Two workarounds:
- **Folder-by-folder AppleScript** — iterate notes per folder (fast, works). First list folders + counts to understand dataset size, then target specific folders.
- **SQLite** — direct DB access (fastest). Use for title search before any AppleScript iteration.

**Known dataset:** user has ~1800 notes across 22 folders. Largest: Notes (1490), Lyrics (116), lyric (90). When searching for a specific note title, use SQLite first — it returns instantly. Only fall back to folder-by-folder AppleScript when SQLite doesn't find it (e.g. note body content search).

### Method 1: AppleScript (osascript) — folder-by-folder (preferred)

**List folders + note counts:**
```applescript
tell application "Notes"
	set folderList to every folder
	set output to ""
	repeat with aFolder in folderList
		set folderName to name of aFolder
		set noteCount to count of notes of aFolder
		set output to output & folderName & " (" & noteCount & " notes)" & return
	end repeat
	return output
end tell
```

**Search notes in a specific folder:**
```applescript
tell application "Notes"
	set theFolder to folder "FolderName"
	set noteList to notes of theFolder
	set output to ""
	repeat with aNote in noteList
		set noteName to name of aNote
		set output to output & noteName & return
	end repeat
	return output
end tell
```

**Looking up notes from a list:** when you already have folder note names, compare directly with `if name of aNote is "ExactName"`. Folder names with Cyrillic/latin work identically.

**Note body format:** AppleScript `body` property returns HTML with `<div>` wrappers (not plain text).

### Method 2: SQLite (fast, direct DB access)

```bash
# Database location
DB="$HOME/Library/Group Containers/group.com.apple.notes/NoteStore.sqlite"

# List all note titles (fast)
sqlite3 "$DB" "SELECT ZTITLE, Z_PK FROM ZICCLOUDSYNCINGOBJECT WHERE ZTITLE IS NOT NULL AND ZTITLE != '' ORDER BY ZTITLE;"

# Search titles
sqlite3 "$DB" "SELECT ZTITLE, Z_PK FROM ZICCLOUDSYNCINGOBJECT WHERE ZTITLE LIKE '%query%';"

# Search in snippet, standardized content, additional indexable text
sqlite3 "$DB" "SELECT ZTITLE, Z_PK FROM ZICCLOUDSYNCINGOBJECT WHERE ZSNIPPET LIKE '%query%' OR ZSTANDARDIZEDCONTENT LIKE '%query%' OR ZADDITIONALINDEXABLETEXT LIKE '%query%';"

# Search in compressed note data (full text content via zlib decompression)
python3 -c "
import sqlite3, zlib, re
conn = sqlite3.connect('$DB')
cur = conn.cursor()
cur.execute('''
  SELECT c.ZTITLE, n.ZDATA FROM ZICCLOUDSYNCINGOBJECT c
  JOIN ZICNOTEDATA n ON c.ZNOTEDATA = n.Z_PK
  WHERE n.ZDATA IS NOT NULL AND length(n.ZDATA) > 0
''')
for row in cur.fetchall():
    try:
        text = zlib.decompress(row[1]).decode('utf-8', errors='replace')
        if re.search(r'query', text, re.IGNORECASE):
            print(f'Found in: {row[0]}')
    except: pass
conn.close()
"
```

**Key tables:**
- `ZICCLOUDSYNCINGOBJECT` — notes metadata (ZTITLE, ZSNIPPET, ZSTANDARDIZEDCONTENT, ZFOLDER)
- `ZICNOTEDATA` — compressed note body (ZDATA blob, zlib-compressed UTF-8)

## When to Use

- User asks to create, view, or search Apple Notes
- Saving information to Notes.app for cross-device access
- Organizing notes into folders
- Exporting notes to Markdown/HTML

## When NOT to Use

- Obsidian vault management → use the `obsidian` skill
- Bear Notes → separate app (not supported here)
- Quick agent-only notes → use the `memory` tool instead

## Quick Reference

### View Notes

```bash
memo notes                        # List all notes
memo notes -f "Folder Name"       # Filter by folder
memo notes -s "query"             # Search notes (fuzzy)
```

### Create Notes

```bash
memo notes -a                     # Interactive editor
memo notes -a "Note Title"        # Quick add with title
```

### Edit Notes

```bash
memo notes -e                     # Interactive selection to edit
```

### Delete Notes

```bash
memo notes -d                     # Interactive selection to delete
```

### Move Notes

```bash
memo notes -m                     # Move note to folder (interactive)
```

### Export Notes

```bash
memo notes -ex                    # Export to HTML/Markdown
```

## Limitations

- Cannot edit notes containing images or attachments
- Interactive prompts require terminal access (use pty=true if needed)
- macOS only — requires Apple Notes.app

## Fallback: osascript (when memo is not installed)

If `memo` is not installed, use AppleScript directly via `osascript`:

```bash
# List folders with note counts
osascript -e 'tell application "Notes"
  set folderList to every folder
  set output to ""
  repeat with aFolder in folderList
    set output to output & name of aFolder & " (" & (count of notes of aFolder) & " notes)" & return
  end repeat
  return output
end tell'

# List notes in a specific folder
osascript -e 'tell application "Notes"
  set theFolder to folder "FolderName"
  set noteList to notes of theFolder
  set output to ""
  repeat with aNote in noteList
    set output to output & name of aNote & return
  end repeat
  return output
end tell'

# Read note body by title in a folder
osascript -e 'tell application "Notes"
  set theFolder to folder "FolderName"
  set noteList to notes of theFolder
  repeat with aNote in noteList
    if name of aNote is "NoteTitle" then
      return body of aNote
    end if
  end repeat
  return "Not found"
end tell'
```

**Performance note:** iterating all notes (~1800+) can time out (30s+). Always filter by folder first. The Apple Notes SQLite DB is at `~/Library/Group Containers/group.com.apple.notes/NoteStore.sqlite` — direct SQLite queries are faster for large note counts but require understanding the CoreData schema (ZICCLOUDSYNCINGOBJECT, ZICNOTEDATA tables).
- **Performance:** AppleScript iterating 1000+ notes may time out. For large vaults, use direct SQLite access — see `references/sqlite-direct-access.md`

## Rules

1. Prefer Apple Notes when user wants cross-device sync (iPhone/iPad/Mac)
2. Use the `memory` tool for agent-internal notes that don't need to sync
3. Use the `obsidian` skill for Markdown-native knowledge management
4. **Search ALL folders** when looking for a note — don't guess which folder it's in. Start with SQLite title search (fast), then folder-by-folder AppleScript if needed.
5. **List folders + counts first** to understand the dataset size before iterating.
