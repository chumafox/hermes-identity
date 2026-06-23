# ALL_PROXY SOCKS5 Environment Trap

## Symptom

```
pip install <package>
ERROR: Could not install packages due to an OSError: Missing dependencies for SOCKS support.
```

## Cause

`ALL_PROXY=socks5://127.0.0.1:1080` is set in the environment (common when a SOCKS5 SSH tunnel is active). pip tries to route through SOCKS but PySocks is not installed.

## Fixes (in order of preference)

1. **Explicit `--proxy` flag** (recommended):
   ```bash
   pip install --proxy socks5://127.0.0.1:1080 <package>
   ```

2. **Install pysocks** (one-time fix, then normal pip works through SOCKS):
   ```bash
   env -u ALL_PROXY pip install pysocks
   ```

3. **Unset ALL_PROXY** for the command:
   ```bash
   env -u ALL_PROXY pip install <package>
   ```

## Affected Tools

- **pip** — fails with "Missing dependencies for SOCKS support"
- **yt-dlp** — YouTube connection timeout unless `--proxy` is passed explicitly
- **Any Python tool using `requests`** with SOCKS proxy in env vars

## Prevention

Always use explicit `--proxy socks5://127.0.0.1:1080` for pip/yt-dlp when a SOCKS5 tunnel is active, rather than relying on ALL_PROXY env var.
