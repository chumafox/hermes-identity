# Cookie Extraction Notes

## Brave Cookie Storage

Brave (Chromium-based) stores cookies in an SQLite database at:
```
~/Library/Application Support/BraveSoftware/Brave-Browser/Default/Cookies
```

## Encryption

Since Brave v115+, cookies are encrypted using AES-256-GCM with a key stored in macOS Keychain.
The `encrypted_value` column contains the ciphertext, while `value` is always empty.

Columns:
- `host_key`, `name`, `value` (empty), `encrypted_value` (BLOB), `path`, `expires_utc`, `is_secure`, `is_httponly`

## Extraction Methods

### Method 1: document.cookie (Hermes browser_console)
Works: ✅
```
browser_console(expression="document.cookie")
```
Returns all cookies as a cookie-string. Use these with curl:
```
curl --cookie "NAME1=VALUE1; NAME2=VALUE2" ...
```
Limitation: `HttpOnly` cookies are not accessible via JS.

### Method 2: Python + SQLite (encrypted)
Works: ❌ (encrypted)
```python
import sqlite3
db = "~/Library/Application Support/BraveSoftware/Brave-Browser/Default/Cookies"
conn = sqlite3.connect(db)
rows = conn.execute("SELECT name, encrypted_value FROM cookies WHERE host_key LIKE '%udemy%'")
# encrypted_value is AES-GCM encrypted — needs macOS Keychain key
```
Requires: `pip install pycryptodome` + macOS Keychain access. Not implemented.

### Method 3: browser_cookie3 library
Works: ❌ (not installed)
```python
import browser_cookie3
cj = browser_cookie3.brave(domain='udemy.com')
```
Not installed. Also may not work with encrypted cookies.

## Current Working Approach

Use `document.cookie` from `browser_console` to get cookies, then pass to curl.
Session cookies expire after ~1 hour of inactivity.
