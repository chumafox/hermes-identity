# Brave CDP WebSocket — Flags & Quirks

When connecting to Brave via the Chrome DevTools Protocol (CDP) over WebSocket
(from Python, Node.js, or any non-browser client), several macOS-specific
gotchas apply.

## Required Brave Flags

Brave must be launched with **both** flags:

```bash
"/Applications/Brave Browser.app/Contents/MacOS/Brave Browser" \
  --remote-debugging-port=9222 \
  --remote-allow-origins=*
```

Without `--remote-allow-origins=*`, WebSocket connections are rejected with
HTTP 403:

```
WebSocketBadStatusException: Handshake status 403 Forbidden
Rejected an incoming WebSocket connection from the http://127.0.0.1:9222 origin.
```

## Restarting Brave via Script (macOS)

Kill and restart with the right flags:

```bash
killall "Brave Browser"
sleep 3
"/Applications/Brave Browser.app/Contents/MacOS/Brave Browser" \
  --remote-debugging-port=9222 --remote-allow-origins=* \
  --no-first-run --no-default-browser-check &
```

⚠️ macOS session restore may re-open the old window without the new flags.
Use `--no-restore-session` to prevent that.

## Navigating to a URL via AppleScript (Fallback)

When CDP `Page.navigate` triggers anti-bot detection (common on sites like
Udemy), use AppleScript instead — it navigates as a real user action:

```python
import subprocess
script = '''
tell application "Brave Browser"
    activate
    open location "https://example.com/page"
end tell
'''
subprocess.run(["osascript", "-e", script], capture_output=True, timeout=10)
```

## CDP WebSocket Response Parsing

`Runtime.evaluate` responses have a **double-nested** result structure:

```json
{
  "id": 99,
  "result": {
    "result": {
      "type": "string",
      "value": "..."
    }
  }
}
```

Access the value as:
```python
msg.get("result", {}).get("result", {}).get("value", "")
```

NOT `msg["result"]["value"]` — that returns `None` silently.

## Finding an Existing Browser Tab

To use the user's existing logged-in session (rather than creating a new tab):

```python
import http.client, json
conn = http.client.HTTPConnection("127.0.0.1", 9222, timeout=5)
conn.request("GET", "/json")
tabs = json.loads(conn.getresponse().read())
conn.close()

# Find a tab on the target domain
target = next((t for t in tabs if "example.com" in t.get("url", "")), tabs[0])

# Connect to its WebSocket
import websocket
ws = websocket.create_connection(target["webSocketDebuggerUrl"], timeout=10)
```

## Matching Responses by ID

Events (like `Page.frameStoppedLoading`) arrive interleaved with command
responses. Always match by `id`:

```python
def js(ws, expr):
    ws.send(json.dumps({"id": 99, "method": "Runtime.evaluate",
                        "params": {"expression": expr}}))
    deadline = time.time() + 5
    while time.time() < deadline:
        try:
            ws.settimeout(deadline - time.time())
            msg = json.loads(ws.recv())
            if msg.get("id") == 99:
                return msg.get("result", {}).get("result", {}).get("value", "")
        except:
            break
    return ""
```

⚠️ Without ID matching, a `Page.frameStoppedLoading` event will be parsed as
the response to your evaluate call, returning an empty result silently.

## Extracting Video URLs from SPAs

For single-page apps that load video via MSE (blob URLs), the actual CDN URL
appears as a resource timing entry. Poll `performance.getEntriesByType`:

```javascript
// In browser console or CDP Runtime.evaluate:
JSON.stringify(
  performance.getEntriesByType('resource')
    .filter(r => r.name.includes('mp4-cdn') && r.name.includes('WebHD'))
    .map(r => r.name)
)
```

The video element's `currentSrc` may also hold the resolved URL (not the blob):

```javascript
document.querySelector('video')?.currentSrc
```

## Requirements

```bash
pip install websocket-client
```
