# Safari osascript JS Quoting Pitfalls

## Problem

`osascript -e 'tell application "Safari" to do JavaScript "..." in current tab of window 1'` 
frequently returns `missing value` even when the JavaScript is syntactically correct.

## Root Cause

The shell quoting + AppleScript quoting + JavaScript quoting creates a triple-nesting
that's nearly impossible to get right for complex JS. Specific failures:

1. **Double quotes inside JS strings** — AppleScript uses `"` for string delimiters too
2. **Backslash escaping** — `\\\\n` (JS newline) becomes `\\\\\\\n` in shell, `\\\\n` in AppleScript, `\n` in JS
3. **Regex literals** — `match(/pattern/)` uses `/` which conflicts with both AppleScript and bash
4. **`setTimeout` / callbacks** — osascript returns BEFORE the callback executes

## Solutions

### Option 1: Simple text extraction (most reliable)

Skip JavaScript entirely. Use Safari's `return text` command instead:

```bash
osascript -e 'tell application "Safari" to return text of current tab of window 1'
```

This returns **all visible text** on the page — good enough for scraping titles,
descriptions, and other content. URLs are NOT included (they're in href attributes, not visible text).

### Option 2: External AppleScript file

Write the JS in a `.applescript` file where quoting is simpler:

```applescript
tell application "Safari"
    do JavaScript "
        var links = document.querySelectorAll('a');
        var result = [];
        for(var i=0; i<links.length; i++) {
            var h = links[i].href;
            if(h && h.match(/appstorrent\\.ru\\/\\d+/)) {
                result.push(h);
            }
        }
        result.join('\\n');
    " in current tab of window 1
end tell
```

Execute with: `osascript /path/to/script.applescript`

### Option 3: Python osascript wrapper (`json.dumps`)

In Python, use `json.dumps()` to handle JS string escaping:

```python
import subprocess, json

def safari_js(js_code):
    """Execute JavaScript in Safari and return result."""
    script = f'''
    tell application "Safari"
        do JavaScript {json.dumps(js_code)} in current tab of window 1
    end tell
    '''
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=15)
    return r.stdout.strip()
```

`json.dumps()` correctly escapes all special characters for the AppleScript string.

### Option 4: Get current URL (lightweight check)

```bash
osascript -e 'tell application "Safari" to return URL of current tab of window 1'
```

Useful to verify navigation succeeded before attempting content extraction.

### Debugging checklist

- Is the right window/tab active? Check: `osascript -e 'tell app "Safari" to return URL of current tab of window 1'`
- Did the JS execute at all? Return a literal first: `osascript -e 'tell app "Safari" to do JavaScript "\"hello\"" in current tab of window 1'`
- Is setTimeout involved? osascript won't wait — use synchronous JS or `sleep` in shell
- Regex in JS? Escape ALL backslashes: `\d` → `\\\\d` in shell (one for JS string, one for AppleScript, one for shell)
