# Package Managers in China — Mirror Configuration

Standard registries (npm, PyPI, crates.io) are often unreachable or get ETIMEDOUT from China. Always configure mirrors before running install commands.

## npm — postinstall script workarounds

Several npm packages have postinstall scripts that download large binaries from CDNs blocked in China:

| Package | Downloads | Workaround |
|---------|-----------|------------|
| **cypress** | ~100MB binary (also Chromium) | `--ignore-scripts` — not needed for build |
| **onnxruntime-node** | native binary (many MB) | `--ignore-scripts` — not needed for build |
| **esbuild** | native binary (~8MB) | **Required** for vite; run manually after install |

**Safe approach:**

```bash
npm install --ignore-scripts --registry=https://registry.npmmirror.com
# Then run only what's needed
node node_modules/esbuild/install.js
node node_modules/vite/node_modules/esbuild/install.js
```

The esbuild postinstall is essential — without it, vite's `.bin` symlinks won't work and `vite build` fails with "vite: command not found". cypress and onnxruntime-node can be safely ignored if you're only building, not testing or running inference.

After `npm install --ignore-scripts`, the `.bin/` directory will be empty. Running esbuild postinstall regenerates the symlinks.

## npm — basic configuration

Default registry `https://registry.npmjs.org` frequently fails with ETIMEDOUT on all packages in China. Use npmmirror:

```bash
npm config set registry https://registry.npmmirror.com
npm install
```

**Warning:** npmmirror has a different ecosystem of published packages — rare edge-case packages may not exist there. If a package fails to install, try the official registry with retries:

```bash
npm config set registry https://registry.npmjs.org
npm config set fetch-retries 3
npm config set fetch-retry-mintimeout 10000
npm config set fetch-retry-maxtimeout 60000
npm install
```

## pip / uv

Python packages from PyPI are often slow from China. Use Tsinghua TUNA mirror:

```bash
# pip
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple <package>

# uv
uv sync --index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

Or set persistently:
```bash
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
export UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
```

## HuggingFace

```bash
export HF_ENDPOINT=https://hf-mirror.com
```

See main SKILL.md for full HF/ModelScope workflow.

## VPN / Local Proxy Interference

Even with a mirror registry configured, npm may hang with ETIMEDOUT if the Mac has a local VPN/proxy running that only intercepts traffic at the system level.

**Failure signature:** `curl` and Node.js `https.get` both work fine to the registry (HTTP 200, <2s), but `npm install` hangs with `ETIMEDOUT` on every package. The npm debug log (`tail -5 ~/.npm/_logs/$(ls -t ~/.npm/_logs/ | head -1)`) shows `http fetch GET ... attempt N failed with ETIMEDOUT` while direct HTTP tests succeed instantly. `npm install` output is completely empty — not even a progress spinner.

**Root cause:** VPN/proxy apps like Shadowrocket, Clash, Surge, and V2Ray set system-level HTTP proxy (`scutil --proxy` shows `HTTPProxy: 127.0.0.1:1082`). npm does NOT read system proxy settings — it only honors `HTTP_PROXY` / `HTTPS_PROXY` environment variables. Node.js `https.get()` may work because it falls through to system settings or bypasses the proxy for certain IP ranges (e.g., CGNAT `198.18.x.x` ranges used by Shadowrocket for DNS interception).

**Diagnosis:**

```bash
# Check if a system proxy is active
scutil --proxy | grep -E "HTTP(S)?(Proxy|Port)"

# List active network services (look for Shadowrocket, Surge, Clash)
networksetup -listallnetworkservices

# Check npm debug log for ETIMEDOUT pattern
ls -t ~/.npm/_logs/ | head -1 | xargs -I{} tail -20 ~/.npm/_logs/{}
```

**Always clean cache after failed attempts before retrying.** Failed npm installs from different registries (npmjs.org → npmmirror) leave corrupted cache entries. Subsequent retries to npmmirror will ETIMEDOUT because npm tries to reuse stale connections to the old CDN. Always do `npm cache clean --force` + `rm -rf node_modules package-lock.json` before switching registries.

**First, try WITHOUT proxy (npmmirror CDN works better directly):**

```bash
rm -rf node_modules package-lock.json && \
npm cache clean --force && \
npm config set registry https://registry.npmmirror.com && \
npm config set fetch-retries 5 && \
npm config set fetch-retry-mintimeout 20000 && \
npm config set fetch-retry-maxtimeout 120000 && \
npm install
```

Often this is all that's needed — npmmirror's CDN (`cdn.npmmirror.com`) delivers tarballs without proxy.

**CRITICAL: npm config proxy causes EIDLETIMEOUT on CDN tarballs.** Setting proxy in npm config (`npm config set proxy`) will break `cdn.npmmirror.com:443` tarball downloads — they fail with `npm error code EIDLETIMEOUT` after the metadata phase succeeds. The proxy tunnel (HTTP CONNECT) to the CDN introduces delays that npm treats as idle timeout. This is NOT a transient error — it reproduces every time proxy is configured. **DO NOT leave proxy set in npm config for the full install. Use the two-phase approach below if proxy is needed.**

**If direct access still ETIMEDOUT — proxy with metadata+CDN split workaround:**

The proxy that fixes metadata fetches (`registry.npmmirror.com`) may break CDN tarball downloads (`cdn.npmmirror.com:443`) with `EIDLETIMEOUT`. Strategy: use proxy to warm the packument cache, then remove it for tarballs.

```bash
# Phase 1: warm packument cache via proxy
npm config set proxy http://127.0.0.1:1082
npm config set https-proxy http://127.0.0.1:1082
npm config set registry https://registry.npmmirror.com
npm install  # FAILS on CDN tarballs with EIDLETIMEOUT
# ^ ignore the error — packument (metadata) cache is now warmed

# Phase 2: remove proxy, retry (tarballs download directly from CDN)
npm config delete proxy
npm config delete https-proxy
npm install  # SUCCEEDS — cached metadata hits, direct CDN delivers tarballs
```

**This worked in production (May 2026):** After Phase 1 failed with `EIDLETIMEOUT` on `cdn.npmmirror.com:443`, simply deleting the proxy and re-running `npm install` (with registry still set to npmmirror, no other changes) completed with `added 588 packages in 1m`. The packument cache from Phase 1 made metadata instant, and direct CDN access delivered all tarballs without proxy interference. No `npm cache clean --force` or `rm -rf node_modules` was needed between phases.

**Diagnosis of CDN tarball failure through proxy:**

After `npm install` seems to progress normally (many package.json fetches succeed with HTTP 200), if it eventually fails with:

```
npm error code EIDLETIMEOUT
npm error Idle timeout reached for host `cdn.npmmirror.com:443`
```

...the proxy is interfering with CDN tarball downloads. The npm log shows hundreds of successful metadata fetches (`http fetch GET 200 https://registry.npmmirror.com/...` at 85-90ms each) followed by silence on the CDN. Solution: delete proxy and retry.

**If proxy is still needed (metadata also fails direct):**

```bash
# Clean corrupted cache from previous failed attempts first
npm cache clean --force
rm -rf node_modules package-lock.json

# Set registry to Chinese mirror
npm config set registry https://registry.npmmirror.com

# Set proxy via config (most reliable for npm 10.x)
npm config set proxy http://127.0.0.1:1082
npm config set https-proxy http://127.0.0.1:1082

# Also export env vars as belt-and-suspenders
export HTTP_PROXY=http://127.0.0.1:1082
export HTTPS_PROXY=http://127.0.0.1:1082

# Now install
npm install
```

Or in one line:
```bash
rm -rf node_modules package-lock.json && \
npm cache clean --force && \
npm config set registry https://registry.npmmirror.com && \
npm config set proxy http://127.0.0.1:1082 && \
npm config set https-proxy http://127.0.0.1:1082 && \
npm install
```

**Why env vars alone may not work (npm 10.x):** On npm 10.9.2+, the `HTTP_PROXY`/`HTTPS_PROXY` env variables are NOT always picked up by `make-fetch-happen` (npm's HTTP client). The `npm config set proxy` approach forces npm's config layer to pass the proxy to the fetch library directly, bypassing the env var parsing bug. Always use config when env vars fail.

**Common proxy ports:**
| App | Port |
|-----|------|
| Shadowrocket | `1082` |
| Clash | `7890` |
| Surge | `6152` |
| V2Ray | `1081` or `1087` |
| Sing-box | `2080` |

**Note:** If the proxy port differs, substitute accordingly. Check with `scutil --proxy`.

## Error Signatures

- `npm install` → empty progress for >5 min, then all packages show `ETIMEDOUT` in `~/.npm/_logs/`. Try `HTTP_PROXY=http://127.0.0.1:1082 npm install` if a local
VPN is present.
- `pip install` → hangs on "Collecting..." then `ReadTimeoutError`
- `uv sync` → hangs then exits with network error (no timeout flag — use `UV_HTTP_TIMEOUT=180`)
