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
---

# Apple Notes

Use `memo` to manage Apple Notes directly from the terminal. Notes sync across all Apple devices via iCloud.

## Prerequisites

- **macOS** with Notes.app
- Install: `brew tap antoniorodr/memo && brew install antoniorodr/memo/memo`
- Grant Automation access to Notes.app when prompted (System Settings → Privacy → Automation)

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

## Fallback When CLI is Unavailable

### Issue Reference

See `references/memo-cli-unavailable.md` for detailed troubleshooting when CLI is missing.

If `memo` command fails (command not found), use **GUI automation** via the `macos-computer-use` skill:

```
computer_use(action="focus_app", app="com.apple.Notes")  # Focus Notes.app
computer_use(action="click", element=N)                 # Click target button  
computer_use(action="type", text="...")                # Type into active field
```

### Terminal Workarounds (when CLI missing)
```bash
# Launch Notes.app
open -a "Notes"

# Search notes via AppleScript
osascript -e 'tell application "Finder" to GET contents of every note item'

# Or use Notes scriptable app directly
osascript -e 'tell application "Notes" to activate'
```

### GUI Workflow When CLI Missing
1. Launch Notes via Spotlight: `command+space`, type "Notes", enter
2. Use `computer_use` to interact with the window
3. Creating: Click New → type title (key="return") → type content (auto-saves)
4. Searching: Click menu Find, or use keyboard shortcut

## Rules

1. Prefer Apple Notes when user wants cross-device sync (iPhone/iPad/Mac)
2. Use the `memory` tool for agent-internal notes that don't need to sync
3. Use the `obsidian` skill for Markdown-native knowledge management
4. If memo CLI unavailable, fallback to macos-computer-use for GUI automation
5. Install memo CLI if available: `brew tap antoniorodr/memo && brew install memo`
