# Basic Safari Page Reading via AppleScript

For extracting visible text from pages behind Cloudflare (when curl/Playwright are blocked).

## Quick Reference

```bash
# Get visible text
osascript -e 'tell application "Safari" to return text of current tab of window 1'

# Get page title
osascript -e 'tell application "Safari" to return name of current tab of window 1'

# Get current URL
osascript -e 'tell application "Safari" to return URL of current tab of window 1'

# Navigate to URL
osascript -e 'tell application "Safari" to set URL of current tab of window 1 to "https://example.com"'

# Create new tab (NOT a new window!)
osascript -e 'tell application "Safari" to make new document with properties {URL:"https://example.com"}'

# Open a new WINDOW (user-facing shortcut: Cmd+N)
osascript -e 'tell application "Safari" to make new window with properties {document:(make new document with properties {URL:"https://example.com"})}'
```

## CRITICAL: `return text` does NOT yield URLs

`return text` returns **only visible rendered text** — it strips ALL HTML structure. This means:
- No `href` attribute values
- No `src` attribute values
- No image links
- No CSS class names or IDs

```bash
# WRONG — produces ZERO results even if page has 100+ links:
TEXT=$(osascript -e 'tell application "Safari" to return text of current tab of window 1')
echo "$TEXT" | grep -o 'https://[^ ]*'   # nothing

# RIGHT — use JavaScript to read href attributes:
osascript -e '
tell application "Safari"
    do JavaScript "
        var links = document.querySelectorAll('"'"'a'"'"');
        var result = [];
        for(var i=0; i<links.length; i++) {
            result.push(links[i].href);
        }
        result.join('"'"'\\n'"'"');
    " in current tab of window 1
end tell
'
```

## Extract Description from Visible Text

For content-rich sites (articles, program descriptions), `return text` IS useful for extracting descriptions:

```bash
TEXT=$(osascript -e 'tell application "Safari" to return text of current tab of window 1')
echo "$TEXT" | grep -v "DMCA\|Правообладателям\|FAQ\|Комментарии\|Telegram\|Повреждено" | head -20
```

## Combination: Navigate + Wait + Read

```bash
osascript -e 'tell application "Safari" to set URL of current tab of window 1 to "https://target-site.com"'
sleep 4  # wait for Cloudflare challenge to pass
osascript -e 'tell application "Safari" to return text of current tab of window 1'
```

## Pitfalls

- **`return text` returns empty on error** — if the page doesn't load (no internet, Cloudflare block, DNS failure), `return text` returns an empty string. Always check length before processing.
- **No JavaScript execution** — `return text` does NOT run JavaScript on the page. If the page loads via JS (SPA apps), the text will be empty or minimal.
- **Tab vs Window confusion** — `make new document` creates a TAB, not a WINDOW. `window 2` does NOT exist after this. Always use `current tab of window 1`.
- **Requires Safari open** — if Safari is not running, osascript hangs until timeout.
