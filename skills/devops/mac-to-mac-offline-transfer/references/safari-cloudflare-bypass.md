# Bypassing Cloudflare via User's Safari (AppleScript Bridge)

## Problem
Sites protected by Cloudflare challenge (like appstorrent.ru) block headless browsers, curl, and Playwright. The only reliable way to access them is through the user's real browser (Safari) where Cloudflare has already issued a session cookie.

## Pattern
Use AppleScript (`osascript`) to control Safari, then execute JavaScript in the browser's context to extract data. The user must:
1. Open the target URL in Safari (or let the agent navigate via AppleScript)
2. Complete any Cloudflare/security challenge manually (if needed)
3. Enable "Allow JavaScript from Apple Events" in Safari → Settings → Advanced → Show Develop menu → Allow JavaScript from Apple Events

Once enabled, the agent can read any page through Safari.

## Commands

### Read page text
```bash
osascript -e 'tell application "Safari" to return text of current tab of window 1'
```

### Navigate to URL
```bash
osascript -e 'tell application "Safari" to set URL of current tab of window 1 to "https://example.com"'
```

### Execute JavaScript and return result
```bash
osascript -e '
tell application "Safari"
    do JavaScript "
        document.querySelectorAll(\"a\").length;
    " in current tab of window 1
end tell
'
```

### Get all unique program URLs from scraped page
```javascript
var links = document.querySelectorAll('a');
var unique = {};
for(var i=0; i<links.length; i++) {
    var h = links[i].href;
    if(h && h.match(/domain\\.com\\/\\d+[a-z-]*\\.html/)) {
        unique[h] = 1;
    }
}
var result = '';
for(var url in unique) {
    result += url + '\\n';
}
result;
```

### Extract title + description from current page
```javascript
(function() {
    var title = '';
    var desc = '';
    var h1 = document.querySelector('h1');
    if(h1) title = h1.innerText.trim();
    if(!title) {
        var h2 = document.querySelector('h2');
        if(h2) title = h2.innerText.trim();
    }
    var ps = document.querySelectorAll('p, .description, [class*=desc], [class*=about]');
    for(var i=0; i<ps.length; i++) {
        var t = ps[i].innerText.trim();
        if(t.length > 50 && !t.match(/cloudflare|javascript|cookie/i)) {
            desc = t.substring(0, 2000).replace(/[\\n\\r]+/g, ' ').trim();
            break;
        }
    }
    return JSON.stringify({title: title, description: desc});
})();
```

## Pagination
Sites with paginated listings (e.g. `/programs/page/1/` through `/programs/page/29/`):
```bash
# Read text to find page numbers
osascript -e 'tell application "Safari" to return text of current tab of window 1' | grep -o '[0-9]*' | tail -5
```

Batch process all pages:
```bash
for page in $(seq 1 29); do
    osascript -e "tell application \"Safari\" to set URL of current tab of window 1 to \"https://site.com/page/$page/\""
    sleep 3
    osascript -e "..." >> /tmp/results.txt
    sleep $(( RANDOM % 5 + 3 ))  # human pause
done
```

## Long-Running Scrape Script
For batch scraping (hundreds of pages), write a Python script that:
1. Reads URLs from a file
2. For each URL: navigate Safari via osascript → wait 3-6s → extract via JavaScript → save to JSON
3. Saves checkpoint after each page (resume on interrupt)
4. Uses random delays

Key components:
- `subprocess.run(["osascript", "-e", script])` to call Safari
- JSON dump after each URL for crash safety
- Checkpoint file to resume from last completed page

See `/tmp/scrape_appstorrent.py` for a reference implementation.

## Pitfalls
- **Safari JavaScript fails silently** — if JS has errors, osascript returns empty string. Test each JS snippet standalone.
- **Quoting hell** — JavaScript strings with quotes need careful escaping inside AppleScript string literals. Write JS to a file and use `osascript /tmp/script.applescript` instead of inline.
- **User must keep Safari focused** — if Safari is closed/minimized, navigation still works but JS execution may be delayed.
- **Rate limiting** — sites may block rapid requests. Use 3-7 second random delays between navigations.
- **Session expiry** — Cloudflare cookies expire. If you get "Just a moment..." page again, user must re-challenge in Safari.
