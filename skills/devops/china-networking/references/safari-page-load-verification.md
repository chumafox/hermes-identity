# Safari Page Load Verification

## Problem

When scraping via Safari + osascript, `sleep 4` is unreliable — slow connections may take 10-20 seconds to load Cloudflare-protected pages. The scraper then reads a partial/empty page (just header/footer HTML) and returns no useful content.

## Solution

Verify the page actually loaded before extracting data:

### Python: check for expected content keywords

```python
def retry_get_text(url, max_retries=5, expected_words=None):
    """Navigate to URL in Safari, retry until page has real content."""
    if expected_words is None:
        expected_words = ["Программы", "Результаты", "Описание", "games", "software"]
    
    for attempt in range(1, max_retries + 1):
        navigate(url)
        time.sleep(4)
        text = get_text()  # osascript return text
        
        # Check if page has real content (not just boilerplate)
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        meaningful = sum(1 for w in expected_words if w in text)
        
        # Check 1: Enough content length
        if len(text) < 200:
            log(f"RETRY {attempt}: too short ({len(text)} chars)")
            time.sleep(30)
            continue
        
        # Check 2: Has at least one expected keyword
        if meaningful == 0 and len(lines) < 10:
            log(f"RETRY {attempt}: boilerplate only ({len(lines)} lines)")
            time.sleep(30)
            continue
        
        return text
    
    log(f"WARN: page never fully loaded after {max_retries} retries")
    return get_text()  # best effort
```

### AppleScript: check page title

```bash
# Quick check that navigation completed
PAGE_TEXT=$(osascript -e 'tell application "Safari" to return text of current tab of window 1')
if echo "$PAGE_TEXT" | grep -qi "cloudflare\|just a moment\|enable javascript"; then
    echo "PAGE BLOCKED OR NOT LOADED"
    sleep 10
    # retry...
fi
```

### JavaScript: wait for body

```applescript
tell application "Safari"
    -- Returns true once body.innerHTML exceeds 500 chars
    do JavaScript "
        (function() {
            var maxWait = 15000;  // 15 seconds max
            var check = function(resolve) {
                var html = document.body ? document.body.innerHTML.length : 0;
                if (html > 500 || Date.now() - start > maxWait) {
                    resolve(html > 500);
                } else {
                    setTimeout(function() { check(resolve); }, 500);
                }
            };
            var start = Date.now();
            return new Promise(function(r) { check(r); });
        })();
    " in current tab of window 1
end tell
```

*Note: This requires `Allow JavaScript from Apple Events` in Safari Developer menu.*

## Common failure modes

| Symptom | Text sample | Root cause |
|---------|------------|------------|
| Only "Программы Игры Расширения" (header) | ~200 chars, nav links only | Page not fully loaded — Cloudflare still processing |
| "Just a moment..." | ~400 chars, Cloudflare JS | Browser hasn't completed challenge |
| "Enable JavaScript and cookies" | ~300 chars | Page requires user interaction (unlikely in osascript) |
| "404 Not Found" | ~100 chars | URL was malformed or page doesn't exist |
