# Memory Filesystem Layout (for cron/offline access)

The built-in Hermes memory store uses flat markdown files — no SQLite, no API.

## Location

```
~/.hermes/memories/
├── MEMORY.md          # Agent's durable facts (environment, tools, projects)
├── MEMORY.md.lock     # Lock file (always empty, can ignore)
├── USER.md            # User profile (preferences, hardware, location)
└── USER.md.lock       # Lock file (always empty, can ignore)
```

## Reading in cron (when memory() tool is unavailable)

The `memory()` tool and `hermes memory list` do NOT work in cron context.
Workaround: read the flat files directly via read_file or cat.

```bash
cat ~/.hermes/memories/MEMORY.md
cat ~/.hermes/memories/USER.md
```

## Writing in cron

Do NOT write to MEMORY.md or USER.md directly — the memory tool manages
formatting and locking. Cron should only READ these files.

For memory-backup.md generation in cron:
1. Read MEMORY.md + USER.md from filesystem (via read_file or cat)
2. Parse the numbered-line format (lines start with `N|content`)
3. Reformat as a human-readable markdown dump
4. Write to ~/hermes-identity/memory-backup.md

## Format

Both files use a simple numbered-line format:
```
1|Content line one
2|§
3|Content line two
```

The `§` separator on its own line marks a paragraph break between
independent memory entries. Lines with just `§` can be skipped when
reformatting.

## CLI commands that work

```bash
hermes memory              # Shows status (provider, plugins)
hermes memory status       # Same
hermes memory setup        # Configure memory provider
hermes memory off          # Disable memory
hermes memory reset        # Clear all memory
```

There is NO `hermes memory list` or `hermes memory read` subcommand.
