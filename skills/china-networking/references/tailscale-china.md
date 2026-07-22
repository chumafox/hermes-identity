# Tailscale from Behind the Chinese Firewall

## Problem Overview

Tailscale relies on UDP DERP (Designated Encrypted Relay for Packets) servers hosted
on Google Cloud, AWS, and other non-China infrastructure. From behind the GFW, these
UDP connections to DERP relays are throttled or blocked, making peer-to-peer connectivity
unreliable even when `tailscale status` shows nodes as "active".

## Symptoms

- `tailscale status` shows remote node as `active; relay "lax"` (or similar DERP tag)
- `tailscale ping 100.x.x.x` → `ping timed out` / `no reply`
- `ssh user@100.x.x.x` → `Operation timed out`
- `tailscale netcheck` shows ALL DERP latencies at 3.2s+ (the connection timeout threshold)
- Health warning: `"Tailscale hasn't received a network map from the coordination server"`

## Root Causes

1. **UDP DERP blocked** — Most Tailscale DERP servers use UDP on non-standard ports
   and are behind CDN IPs that China blocks or throttles
2. **CGNAT** — Chinese ISPs commonly use Carrier-Grade NAT, making direct STUN punching
   impossible without a working relay
3. **DNS/connectivity to coordination server** — login.tailscale.com and the coordination
   plane may also be affected, causing stale network maps

## macOS GUI Sandbox Limitation

Tailscale installed via App Store or DMG download is a **sandboxed GUI build**.
`tailscale set --ssh` fails with:

```
The Tailscale SSH server does not run in sandboxed Tailscale GUI builds.
```

**Fix:** Install the CLI variant (non-sandboxed):

```bash
# Option A: Homebrew (installs CLI, not the GUI cask)
brew install tailscale

# Option B: Manual download from pkgs.tailscale.com
curl -fsSL -o /tmp/tailscale.pkg \
  "https://pkgs.tailscale.com/stable/tailscale-latest-arm64.pkg"
sudo installer -pkg /tmp/tailscale.pkg -target /
```

After CLI install, verify SSH works:
```bash
tailscale set --ssh        # enables Tailscale SSH server
sudo systemsetup -setremotelogin on   # macOS Remote Login (also required)
```

## Workarounds

### A. Reverse SSH Tunnel (simplest, requires access)

If you can run a command on the remote machine once (physical access, previous SSH session):

```bash
# On the remote machine — forward its port 22 to the jump host
ssh -N -R 10022:localhost:22 user@jump-host

# From the source machine — connect through the jump host
ssh -J user@jump-host -p 10022 remote-user@localhost
```

The jump host must be on a network the target machine can reach (LAN, or behind the
same NAT). Use `autossh` for persistence across disconnects.

### B. Custom DERP Server (best long-term)

Deploy a Tailscale DERP server on a VPS outside China (Hong Kong, Singapore, or Japan
for lowest latency to China):

```bash
# On the VPS (Ubuntu/Debian):
sudo apt install golang-go
go install tailscale.com/cmd/derper@latest
sudo setcap cap_net_bind_service=+ep ~/go/bin/derper

# Run:
~/go/bin/derper -hostname derp.yourdomain.com -verify-clients

# Tailscale ACL to add the custom DERP:
# In the admin console, add to the `derpMap` section or use
# `tailscale up --accept-routes` with appropriate ACL rules
```

Reference: https://tailscale.com/kb/1118/custom-derp-servers

### C. Sing-Box Direct Route for Tailscale

If the source machine routes through sing-box TUN mode, Tailscale's DERP traffic may be
intercepted and forced through a SOCKS5 TCP proxy (which cannot carry UDP DERP traffic).

Add Tailscale's CGNAT range to the `direct` outbound:

```json
{
  "ip_cidr": [
    "100.64.0.0/10",
    "fd7a:115c:a1e0::/48"
  ],
  "outbound": "direct"
}
```

This lets Tailscale attempt direct DERP connections. May still fail if the ISP blocks
UDP to DERP IPs.

### D. Tailscale Exit Node on VPS

If you have a VPS outside China with Tailscale installed, configure it as an exit node.
Both Chinese machines then route DERP traffic through the VPS:

```bash
# On the VPS:
tailscale up --advertise-exit-node
```

Then on each client:
```bash
tailscale up --exit-node=<vps-tailscale-ip>
```

### E. ZeroTier as Alternative

ZeroTier often works from China because its root servers and relay infrastructure are
different (and less aggressively blocked). Install on both machines:

```bash
curl -s https://install.zerotier.com | sudo bash
sudo zerotier-cli join <network-id>
```

## Detection Commands

```bash
# Netcheck — shows DERP latency from current location
tailscale netcheck 2>&1 | grep -E "DERP latency|Nearest DERP"
# If all >3s → blocked

# Ping peer via Tailscale
tailscale ping --c 3 --timeout 5s 100.x.x.x

# Direct ICMP ping to Tailscale IP (requires DERP or direct conn)
ping -c 2 100.x.x.x

# Check peer route
tailscale status | grep <peer-name>

# Check which relay a peer is using
tailscale status --peers | grep <peer-name>
```

## Sing-Box Context

When using sing-box + SSH tunnel SOCKS5 (port 1080), the chain is:

```
app → sing-box TUN (utun9) → mixed proxy :1083 → SOCKS5 :1080 → SSH tunnel → VPS outside China → internet
```

Tailscale DERP uses UDP and cannot traverse SOCKS5 (which is TCP-only). This creates
a conflict where:
- TCP traffic to Tailscale IPs works (via the SOCKS5 chain if the jump host is on Tailscale)
- UDP DERP traffic fails (no UDP relay in the chain)
