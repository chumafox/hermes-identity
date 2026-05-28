# VPN/Proxy Apps in China — DNS & Connection Troubleshooting

When a VPN/proxy manager app (Happ, ClashX, V2RayU, Shadowrocket, etc.) has subscription configs installed but cannot connect to upstream servers from China.

## Symptom

- App shows "connecting" but never connects
- No errors in GUI, but server stays disconnected
- Other internet works (curl, ping)

## Root Cause

China Mobile (and other carriers) blocks or poisons DNS queries for foreign VPN server domains. The app's Xray/V2Ray/Clash core receives `NXDOMAIN` or a forged IP from the carrier DNS, so it can never reach the real server.

## Diagnostic

### 1. Check app logs

Typically logs are in `~/Library/Group Containers/<group-id>/Library/Application Support/<engine>/logs/`.

**For Happ (Xray-core):**
```bash
cat ~/Library/Group\ Containers/group.su.ffg.happ/Library/Application\ Support/Xray/logs/connectionLogs/*.log | grep "failed to resolve"
```

Expected failure pattern:
```
failed to resolve ip > app/dns: returning nil for domain <server-domain>
lookup <server-domain>: no such host
```

**For Happ — tunnel stopped reason:**
```bash
grep "Tunnel stopped" ~/Library/Group\ Containers/group.su.ffg.happ/Library/Application\ Support/Xray/logs/connectionLogs/*.log
# → "Stop reason: - userInitiated" (manual disconnect)
# → "Stop reason: - connectionFailed" (DNS/resolve failure)
```

### 2. Confirm DNS block from terminal

```bash
nslookup <server-domain> 1.1.1.1
# If 1.1.1.1 resolves correctly but default DNS doesn't → carrier DNS block
```

### 3. Test DoH endpoints directly (diagnose which DNS works in China)

```bash
# Google DoH — TIMES OUT in China (blocked):
curl -s --max-time 10 "https://8.8.8.8/dns-query?name=example.com&type=A" -H "accept: application/dns-json"

# Yandex DoH — WORKS but returns "Not Found" for unknown/private domains:
curl -s --max-time 10 "https://77.88.8.8/dns-query?name=example.com&type=A" -H "accept: application/dns-json"
# → works for public domains, does NOT know private VPN domains

# Cloudflare DoH — usually works from China:
curl -s --max-time 10 "https://1.1.1.1/dns-query?name=example.com&type=A" -H "accept: application/dns-json"
# → most reliable, try this first
```

**Interpretation:**
- **8.8.8.8 DoH → timeout**: Google DoH is blocked in China. Configure the app to use `https://1.1.1.1/dns-query` instead.
- **77.88.8.8 → "Not Found"**: Yandex DNS works but doesn't resolve private proxy domains.
- **1.1.1.1 → resolves**: Cloudflare works — use this for the app's DNS setting.
- **All DNS fail**: even Cloudflare DoH is blocked → need VPN/proxy just to bootstrap DNS.

### 3b. Counterintuitive: `dig @8.8.8.8` (plain DNS/UDP) works when DoH doesn't

Even though `https://8.8.8.8/dns-query` (DoH over TCP) times out in China, the plain DNS-over-UDP protocol often still works:

```bash
# WORKS even in China (plain DNS/UDP port 53 to Google):
dig +short de.gate8.zone @8.8.8.8
# → 176.97.210.106  (resolves!)

# While DoH to same server TIMES OUT:
curl -s --max-time 10 "https://8.8.8.8/dns-query?name=de.gate8.zone&type=A" -H "accept: application/dns-json"
# → empty / timeout
```

**Why this matters:** If all DoH endpoints fail (1.1.1.1, 8.8.8.8 all timeout), still try `dig @8.8.8.8 serverdomain.com` — plain DNS often bypasses the block even on the same server.

If `dig @1.1.1.1` or `@8.8.8.8` succeeds, you can get the server's IP and configure the app to connect by IP instead of domain (if the app supports it).

### 3c. Happ-specific: Native "Server Resolving" feature

Happ has a built-in **Server Resolving** feature (not in routeSettings — accessible via GUI only):

1. Open Happ → Routing → Route Settings (or directly under the server/subscription name)
2. Look for a "Server Resolving" toggle or field section
3. If the domain (e.g. `de.gate8.zone`) fails to resolve, you can manually enter:
   - Server: `de.gate8.zone` (domain)
   - DNS: `8.8.8.8` (DNS to use for resolving this domain — Happ will use plain DNS queried directly, not DoH)
4. Save and reconnect

**Note:** Some Happ versions may show a format hint like `https://...` in the example. The actual correct format for the domain field is just the bare domain name (no protocol prefix).

### 4. Check if app has its own DNS config

Some apps (like Happ) use their own DNS resolver embedded in Xray-core, which piggybacks on the system DNS. If the system DNS is blocked, the app's resolver fails too.

**For Happ:** The DNS config is in routeSettings.json (NOT encrypted — plain JSON):
```bash
cat ~/Library/Group\ Containers/group.su.ffg.happ/Library/Application\ Support/Xray/routingSettings/<UUID>/routeSettings.json
```

Key fields:
- `remoteDnsDomain` — the DoH URL for remote DNS (default: `https://8.8.8.8/dns-query` — BLOCKED in China)
- `remoteDnsType` — `DoH` or `DoT` or `Plain`
- `domesticDnsDomain` — the DoH URL for domestic DNS (default: `https://77.88.8.8/dns-query` — Yandex, works)
- `domesticDnsType` — usually `DoH`
- `fakeDnsEnabled` — if true, app may not use real DNS at all
- `domainStrategy` — `IPIfNonMatch`, `IPOnDemand`, etc.
- `geositeUrl` — URL for geosite.dat download (e.g., Cloud Mail.Ru — may be blocked)
- `geoipUrl` — URL for geoip.dat download (e.g., Cloud Mail.Ru)
- `globalProxy` — if false, routing rules may exclude the server domain

**IMPORTANT:** Happ's subscription config files (`config.json`, `metaParams.json`) are **encrypted/binary** — cannot read or edit them directly. Only the routeSettings.json and preferences plist are readable.

### 4b. Happ-specific connection-level DNS settings (GUI only)

Beyond routeSettings DNS, Happ has additional DNS controls per-connection/subscription:

1. **Use Server DNS** — A toggle in the connection/subscription detail view. When enabled, Happ uses DNS from the VPN server itself (the server resolves domains client-side). This bypasses local DNS blocking entirely. **Enable this first** before changing DoH URLs.

2. **Enable Fake DNS** — Another toggle near the connection settings. When enabled, Happ intercepts ALL DNS queries and returns fake IPs, routing them through the proxy tunnel. The VPN server then resolves the real IP and forwards traffic.
   - **Recommended:** Enable this if "Use Server DNS" alone doesn't work
   - **Tradeoff:** May break local network services (AirDrop, local DNS-SD) — only relevant for the proxy tunnel traffic

3. **Server Resolving** (per-domain override) — A section where you can manually map a domain to a specific DNS resolver:
   - Domain: `de.gate8.zone`
   - DNS: `8.8.8.8` (Happ will query this DNS directly, bypassing its configured DoH)
   - This uses plain DNS/UDP to 8.8.8.8, not DoH — often works when DoH fails (see 3b)
   - **Format note:** Some Happ GUIs show `https://` in the field label/example. The correct input for the domain field is just the bare domain name (no protocol). The DNS field is just an IP (no protocol).

**Order of attempted fixes (try each sequentially):**
1. Enable **Use Server DNS** → test
2. Enable **Enable Fake DNS** → test  
3. Set **Remote DNS** in routeSettings to `https://1.1.1.1/dns-query`
4. Use **Server Resolving** with domain + DNS `8.8.8.8`
5. Manual IP override (if supported)

### 5. Geo files status

Geo files (geoip.dat, geosite.dat) live in:
```bash
~/Library/Group\ Containers/group.su.ffg.happ/Library/Application\ Support/Xray/geofiles/Default/
```

Check their sizes:
```bash
ls -la ~/Library/Group\ Containers/group.su.ffg.happ/Library/Application\ Support/Xray/geofiles/Default/
# geoip.dat ~15.5 MB, geosite.dat ~7 MB — normal
```

If geo files are missing or 0-byte, the app failed to download them (common when the URL points to Cloud Mail.Ru, which is blocked in China).

## Known Errors & Solutions

### "geosite.dat missing section: WHITELIST"

When Happ (Xray-core) shows:
```
XrayCore cannot be started because the included file geosite.dat missing section: WHITELIST
You can run the TUNNEL without a routing profile by clicking the "Run" button.
```

This means:
- The installed `geosite.dat` is **newer** than the routing profile expects — the `WHITELIST` category was renamed/removed in newer releases
- The app's routing profile (created from an older template) references the `WHITELIST` geosite section which no longer exists

**Solutions (in order of preference):**

1. **Click "Run"** — starts the tunnel WITHOUT routing profile. The tunnel itself still works (proxy connection established), but there's no smart routing — ALL traffic goes through the VPN. This is fine for basic use.

2. **Update routing profile** — Inside Happ, navigate to Routing → Route Settings and either:
   - Edit the existing profile to remove the `WHITELIST` rule
   - Create a new routing profile (which will reference only existing geosite sections)

3. **Install matching geosite.dat** — If you have the older `geosite.dat` (with WHITELIST section), overwrite the new one in:
   ```bash
   ~/Library/Group\ Containers/group.su.ffg.happ/Library/Application\ Support/Xray/geofiles/Default/geosite.dat
   ```

**"Run" mode tradeoffs:**
- ✅ Proxy tunnel works — server connection established
- ✅ DNS resolves (if DoH configured or Use Server DNS enabled)
- ❌ No smart routing — all traffic through VPN (no domestic traffic bypass)
- ❌ May interfere with local network traffic (AirDrop, local DNS)

### Cloud Mail.Ru geo file URLs blocked

Happ stores geo download URLs in `routeSettings.json`:
```json
"geositeUrl": "https://cloclo57.cloud.mail.ru/weblink/view/PDQx/z1jngMjpR",
"geoipUrl": "https://cloclo57.cloud.mail.ru/weblink/view/7vQY/4i3t3xkZq"
```

These are **blocked in China** — Cloud Mail.Ru uses Cloudflare CDN which gets reset/blocked by GFW.

**If Happ can't download geo files:** it keeps trying silently. The download attempts appear as 0-byte `.tmp` files in:
```bash
~/Library/Containers/su.ffg.happ/Data/Library/Caches/com.apple.nsurlsessiond/Downloads/su.ffg.happ/
```

**Workaround:** Existing geo files (even from April) work fine. The WHITELIST error is NOT caused by outdated geo files — it's a routing profile template issue.

## Shadowrocket on macOS — Config File Locations & Fake DNS

Shadowrocket for macOS stores its configuration in `~/Library/Group Containers/group.com.liguangming.Shadowrocket/`. Key files:

| File | Purpose | Format |
|------|---------|--------|
| `dns.conf` | DNS server list (plist XML array of strings) | Plain XML |
| `ServerManager` | All subscription/server/group data | Binary/encrypted |
| `default.db.rule` | Default routing rules | Binary/encrypted |
| `rule.db` | SQLite database with rules | SQLite |
| `groups.archive` | Proxy groups configuration | Binary |
| `NetworkUsage` | Per-server traffic statistics | Binary |

**Reading dns.conf:**
```bash
cat ~/Library/Group\ Containers/group.com.liguangming.Shadowrocket/dns.conf
# Example output:
# <?xml version="1.0" encoding="UTF-8"?>
# <plist><array>
#   <string>114.114.114.114</string>
#   <string>8.8.8.8</string>
# </array></plist>
```

### Shadowrocket Fake DNS Breaks brew (and other tools)

When Shadowrocket is active on macOS, it uses **Fake DNS** — it intercepts DNS queries and returns synthetic IPs from the `198.18.0.0/15` range for domains that should go through the proxy tunnel. This is a VPN-standard technique to route traffic for specific domains through the tunnel.

**Problem:** If the VPN tunnel is active but the upstream server is unreachable (DNS block, server down), brewed domains get `198.18.0.x` IPs that don't actually route to any real server. Tools like `brew` (which accesses `formulae.brew.sh`) and `curl` to GitHub fail with:

```bash
curl: (35) LibreSSL SSL_connect: SSL_ERROR_SYSCALL in connection to formulae.brew.sh:443
```

Because DNS returns `198.18.0.21` instead of the real Cloudflare IP.

**Diagnosis:**
```bash
# Check what IP Shadowrocket gives for brew's domain:
dig +short formulae.brew.sh
# → 198.18.0.21  (fake DNS — NOT the real IP)
# → If it resolves to 198.18.x.x, fake DNS is active

# Check Shadowrocket's HTTP proxy (set as system proxy on port 1082):
scutil --proxy | grep HTTPProxy
# → HTTPProxy: 127.0.0.1
# → HTTPPort: 1082

# Test if the proxy actually works:
http_proxy=http://127.0.0.1:1082 curl -s --max-time 10 "https://api.ipify.org"
# → empty / timeout → proxy returns 503 for CONNECT
```

**Solutions (pick one):**

1. **Add brew domains as DIRECT rules in Shadowrocket GUI:**
   - Shadowrocket → Config → Rules (if visible)
   - Add before other rules:
     ```
     DOMAIN-SUFFIX,brew.sh,DIRECT
     DOMAIN-SUFFIX,github.com,DIRECT
     DOMAIN-SUFFIX,formulae.brew.sh,DIRECT
     DOMAIN-SUFFIX,raw.githubusercontent.com,DIRECT
     ```

2. **Disable "Set as System Proxy"** in Shadowrocket menu bar icon → Settings → uncheck. This removes the HTTP proxy on 1082, letting apps connect directly through the VPN tunnel (utun interface) instead of through the proxy.

3. **Use the VPN tunnel directly** — remove SOCKS/HTTP proxy and let apps use the VPN interface (utun) natively:
   ```bash
   # Set brew to bypass proxy entirely:
   unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
   brew install <package>
   ```

**Key insight:** The VPN tunnel (utun7) and the HTTP proxy (1082) are SEPARATE mechanisms. The HTTP proxy forwards requests through the tunnel but adds an extra layer that can fail (503 on CONNECT). Disabling the proxy and using the tunnel directly often fixes brew.

### Shadowrocket HTTP Proxy (Port 1082) Returns 503 for CONNECT

When Shadowrocket is running in VPN mode, it also sets up an HTTP proxy on `127.0.0.1:1082` (visible via `scutil --proxy`). However, this proxy often returns `503 Service Unavailable` for CONNECT requests to HTTPS sites.

**System proxy config shows:**
```bash
scutil --proxy
# HTTPEnable : 1
# HTTPPort   : 1082
# HTTPProxy  : 127.0.0.1
# HTTPSEnable : 1
# HTTPSPort   : 1082
# HTTPSProxy  : 127.0.0.1
```

But `networksetup -getwebproxy "iPhone USB"` shows `Enabled: No` — the proxy is set **globally via SCDynamicStore**, not per-network-service.

**How it affects different traffic:**

| Traffic type | Path | Works? |
|---|---|---|
| curl (direct, no proxy env) | Via utun7 VPN tunnel | ✅ Usually works |
| curl (with `http_proxy=127.0.0.1:1082`) | Via HTTP proxy → utun7 | ❌ 503 on CONNECT |
| brew (uses system proxy by default) | Via HTTP proxy → utun7 | ❌ 503 / SSL errors |
| Python urllib (system stack) | Via VPN tunnel | ✅ Works |
| Safari (system stack) | Via VPN tunnel | ✅ Works (if proxy disabled) |

**Fix:** Unset proxy environment variables for brew:
```bash
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY
brew install <package>
```

### Fix — Use Shadowrocket's Share VPN (LAN Proxy)

Shadowrocket for macOS has a **Share VPN** toggle that exposes an HTTP proxy on the host's LAN IP (not just localhost). This is useful when other Macs on the same link need internet through the VPN:

1. In Shadowrocket menu bar → Settings → enable **Share VPN**
2. Shadowrocket exposes HTTP proxy on `<LAN-IP>:1082` (e.g. `192.168.104.2:1082`)
3. From any machine on the same network (including the headless Mac over Thunderbolt Bridge), use:
   ```bash
   export http_proxy=http://192.168.104.2:1082
   export https_proxy=http://192.168.104.2:1082
   ```

**Find your LAN IP:**
```bash
ifconfig en0 | grep "inet " | awk '{print $2}'
```

**Key advantage over localhost proxy:** The LAN proxy often works when the localhost proxy returns 503, because it uses a different path through MacPacketTunnel.

**Verification:**
```bash
http_proxy=http://192.168.104.2:1082 curl -s --max-time 10 "https://api.ipify.org"
# → Should return a non-China IP (e.g., Hong Kong/VPN IP)
```

**Use case — brew on headless Mac through host's Shadowrocket:**
```bash
export http_proxy=http://192.168.104.2:1082
export https_proxy=http://192.168.104.2:1082
brew install <package>
```

**Pitfall:** The LAN IP (192.168.104.x) changes if the host Mac reconnects to a different WiFi network. Check the IP after network changes.

### Solution A: Configure DNS-over-HTTPS (DoH) in the app (default fix)

For Happ:
1. Open Happ from menu bar → Routing → Route Settings
2. Change **Remote DNS** to: `https://1.1.1.1/dns-query`
3. Change **Domestic DNS** to: `https://77.88.8.8/dns-query` (already default, works)
4. Save and reconnect

For Shadowrocket on Mac:
- Same subscription URL as iPhone → just import and connect
- Shadowrocket on macOS uses its own DNS resolver
- If DNS fails: in app settings, find DNS section and add `1.1.1.1` or `8.8.8.8`

### Solution B: Change system DNS to 1.1.1.1

```bash
sudo networksetup -setdnsservers "iPhone USB" 1.1.1.1 8.8.8.8
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder
```

This only helps if the app uses the system DNS resolver (Xray-core in Happ uses its own DoH — system DNS changes alone won't fix it).

### Solution C: Use a server IP directly (if app supports it)

Private VPN server domains (e.g., `de.gate8.zone`) are often NOT in any public DNS at all — they only exist in the provider's private DNS. Standard DoH servers don't know them.

If the app allows manual config editing, replace the domain with a raw IP:
```bash
# Try to resolve from various DNS servers:
nslookup <server-domain> 1.1.1.1
nslookup <server-domain> 8.8.8.8
nslookup <server-domain> 77.88.8.8
# If ALL fail → domain is truly private/undiscoverable via public DNS
```

Note: Happ encrypts config files — you can't edit them manually.

### Solution D: Switch to a different server in the subscription

Some servers in the same subscription may use IPs or domains that aren't blocked. Try switching servers in the app GUI.

### Solution E: Use Shadowrocket (macOS app) as simpler alternative

If you have Shadowrocket on iPhone/iPad with a working subscription, **Shadowrocket for macOS** exists and can use the SAME subscription:
- Install Shadowrocket on Mac (from the App Store or as a standalone .app)
- Import the same subscription URL
- Shadowrocket handles DNS better than Happ for Chinese networks
- No routing profile issues (no WHITELIST geosite dependency)
- Works as VPN (not just SOCKS5 proxy) — system-wide

**Detection:** Shadowrocket appears in `networksetup -listallnetworkservices` as:
```
Shadowrocket
(Hardware Port: com.liguangming.Shadowrocket, Device: )
```

## Happ-Specific: Preference Inspection

Useful Happ preferences (plist at `~/Library/Group Containers/group.su.ffg.happ/Library/Preferences/group.su.ffg.happ.plist`):

```bash
sudo plutil -p ~/Library/Group\ Containers/group.su.ffg.happ/Library/Preferences/group.su.ffg.happ.plist
```

Key fields:
- `httpProxyPort` — HTTP proxy port (default: `10809`)
- `sockstProxyPort` — SOCKS5 proxy port (default: `10808`)
- `XRAY_CURRENT` — UUID of currently selected server config
- `XRAY_CURRENT_SUBSCRIPTION` — UUID of the subscription
- `XRAY_ROUTE_IS_ENABLED` — `0` = global proxy mode, `1` = routing rules enabled
- `isLibXrayRunXrayJsonRunning` — `0` = Xray not running, `1` = running
- `enableFragment` — TLS fragmentation (for bypassing DPI)
- `appVersionForAppExtension` — installed version

## Snapshot of Happ Filesystem Layout

```
~/Library/Group Containers/group.su.ffg.happ/
  Library/
    Application Support/Xray/
      geofiles/
        Default/
          geoip.dat          ~15.5 MB
          geosite.dat        ~7 MB
        <UUID>/
          geoModel.json      routing profile metadata
      subscriptionConfigs/
        <SubscriptionUUID>/
          config.json        ENCRYPTED — per-server Xray config
          metaParams.json    ENCRYPTED — subscription metadata
          <ServerGUID>/config.json  ENCRYPTED — individual server configs
      routingSettings/
        <RouteProfileUUID>/
          routeSettings.json     PLAIN JSON — routing config (DNS, geo URLs, rules)
          defaultImportedSettings.json
      logs/
        connectionLogs/      *.log files with tunnel activity
        subscriptions.log
        tunnel.log
      assets/
        data.result          downloaded geo data
    Preferences/
      group.su.ffg.happ.plist   PLAIN — app preferences
    Caches/
    tmp/
  tmp/                       temporary download files
```

## Prevention

When setting up a new VPN service in China:
- Prefer subscriptions that deliver server IPs (not domains) in the config
- Configure DoH in the app immediately after subscription import — use `https://1.1.1.1/dns-query`, NOT `https://8.8.8.8/dns-query`
- Add `1.1.1.1` as system DNS on every network interface
- Ensure geo URL uses a China-accessible mirror (not Cloud Mail.Ru, not raw GitHub)
- Prefer Shadowrocket over Happ for simpler setups (fewer routing profile issues)
