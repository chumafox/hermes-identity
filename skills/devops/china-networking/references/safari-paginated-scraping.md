# Paginated Web Scraping via Safari + AppleScript

For scraping sites behind Cloudflare that require a real browser session. The user opens the first page in Safari, then AppleScript-driven bash scripts automate pagination and data extraction.

## Workflow Overview

1. Collect all page URLs via pagination (page/1, page/2, ..., page/N)
2. Scrape each URL individually: navigate → wait → extract → save → checkpoint
3. Supports resume if interrupted midway

## Prerequisites

- User has Safari open on the target page (Cloudflare challenge already passed)
- For JavaScript extraction: Developer → Allow JavaScript from Apple Events
- Write scripts as `.sh` files + separate `.applescript` files (avoids quoting hell)

## Phase 1: Collect All Page URLs

### Step 1.1 — Detect pagination

Read the page text to find "1 2 3 ... 29" pattern:

```bash
osascript -e 'tell application "Safari" to return text of current tab of window 1' | tail -10
```

Common URL patterns: `/programs/page/N/`, `/page/N/`, `?page=N`.

### Step 1.2 — Write a bash script for pagination

Script structure (run in background):

```bash
#!/bin/bash
OUTPUT_FILE="/tmp/scraped_urls.txt"
> "$OUTPUT_FILE"

for page in $(seq 1 29); do
    # Navigate
    osascript -e "tell application \"Safari\" to set URL of current tab of window 1 to \"https://site.com/page/$page/\""
    sleep 4  # wait for Cloudflare to clear

    # Extract all links matching the program pattern
    osascript -e "
        tell application \"Safari\"
            do JavaScript \"
                var links = document.querySelectorAll('a');
                var unique = {};
                for(var i=0; i<links.length; i++) {
                    var h = links[i].href;
                    if(h && h.match(/site\\\\\\.com\\\\\\\\/\\\\\\\\d+[a-z-]*\\\\\\.html/)) {
                        unique[h] = 1;
                    }
                }
                var result = '';
                for(var url in unique) { result += url + '\\\\\\\\n'; }
                result;
            \" in current tab of window 1
        end tell
    " >> "$OUTPUT_FILE"

    sort -u "$OUTPUT_FILE" -o "$OUTPUT_FILE"
    echo "Page $page: $(wc -l < "$OUTPUT_FILE") unique URLs"

    # Random humane pause 3-7 seconds
    sleep $(( RANDOM % 5 + 3 ))
done
```

**Key pitfalls:**
- `mapfile` is NOT available on macOS bash (version 3). Use `while IFS= read -r` loop instead.
- `grep -P` is not available on macOS grep. Use `grep -E` or sed.
- Script hangs if Safari is not open or user closes the tab. Add `set -o pipefail` and timeout guards.
- First line in output file is often empty (starting `>` before any `>>` writes). Use `tail -n +2` to clean.
- `return text` does NOT contain URLs — use JS to read href attributes (see Phase 2 note)

### Step 1.3 — Clean the URL list

```bash
tail -n +2 /tmp/scraped_urls.txt > /tmp/urls_clean.txt
sort -u /tmp/urls_clean.txt -o /tmp/urls_clean.txt
```

## Phase 2: Scrape Descriptions

### THE BEST PATTERN: Separate AppleScript + Python

**ALWAYS use this pattern, never inline bash + osascript + JS.** The three-layer quoting (bash → AppleScript → JavaScript) is error-prone.

1. Create a standalone AppleScript file:

```applescript
tell application "Safari"
    do JavaScript "
        var links = document.querySelectorAll('a');
        var unique = {};
        for(var i=0; i<links.length; i++) {
            var h = links[i].href;
            if(h && h.match(/site\\.ru\\/\\d+[a-z\\-]*\\.html/)) {
                unique[h] = 1;
            }
        }
        var result = '';
        for(var url in unique) result += url + '\\n';
        result;
    " in current tab of window 1
end tell
```

2. Call it from Python:

```python
def get_links():
    r = subprocess.run(["osascript", "/tmp/get_links.applescript"],
                       capture_output=True, text=True, timeout=20)
    raw = r.stdout.strip()
    if raw and raw != "missing value":
        return [line.strip() for line in raw.split("\n") if line.strip().startswith("http")]
    return []
```

### Script with checkpointing

Use Python (not bash) for the full scraper. See `references/python-safari-scraper.md` for a complete template.

## CRITICAL DO NOT: Parallel Safari scraping

**NEVER run two scraping scripts that control the same Safari window simultaneously.**

Each script calls `tell application "Safari" to set URL of current tab of window 1 to "..."` — they will fight over the browser, causing both to fail with corrupted output ("missing value", empty responses, half-loaded pages).

If the user has multiple pages to scrape from different sources:
1. Complete one source fully (URL collection + description parsing) before starting the next
2. Or use separate scripts that target different windows — but `window 2` only exists if the user manually opens a second Safari window (Cmd+N creates a new WINDOW, not a tab)
3. **Do NOT use `&` in a single terminal command** — start one scraper, verify it works, let it finish, then start the next
4. If you accidentally start two, kill both immediately (background sessions can be killed via `process(action="kill")`)

Signs of parallel-Safari conflict:
- Script returns "missing value" for all JS operations
- `return text` shows a different page than expected
- URLs alternate between two different sets
- Checkpoint saves data from mixed sources

## URL Extraction: Why `return text` doesn't work

`osascript -e 'tell application "Safari" to return text of current tab of window 1'` returns **only visible rendered text** — all HTML structure, including `href` attributes, are STRIPPED.

```python
# WRONG: zero results
text = get_text()
urls = re.findall(r'https://site\.ru/\d+', text)  # never matches

# RIGHT: use JS href access via applefile
links = get_links()  # calls /tmp/get_links.applescript
```

## Time Estimates

| Scale | Pages | Programs | Time | Notes |
|-------|-------|----------|------|-------|
| Small | 10 pages | ~470 | ~3 min | Quick test |
| Medium | 30 pages | ~1400 | ~10 min | One site |
| Full scrape + desc | 30 pages | 1285 programs | ~3-4 hours | With humane pauses |

## Pitfalls

- **Safari crashes/freezes** — if Safari beachballs, the script hangs indefinitely. Set a `(timeout N && kill $$) &` watchdog or use `gtimeout` (brew install coreutils).
- **User interacts with Safari** — if user clicks a link during scraping, the wrong page loads. Ask user to not touch Safari while scraping.
- **First URL is often empty** — the `>` redirection in Phase 1 creates an empty first line. Always `tail -n +2` the URL list.
- **`mapfile` is macOS bash 3 poison** — only available in bash 4+. Always use the `while IFS= read -r` pattern.
- **Cloudflare re-checks** — after many requests (~50-100), Cloudflare may re-challenge. If scraping stops returning data, user needs to refresh Safari and re-pass the challenge.
- **No Xcode CLT on target** — `python3 -c "..."` pipes fail silently if CLT missing. Use `| /path/to/portable/python3 -c "..."` instead, or write Python to a `.py` file and run it.
- **Window numbering** — `window 1` always works; `window 2` only if user actually opened a second window (Cmd+N). Tabs created via AppleScript `make new document` are still `window 1`.
