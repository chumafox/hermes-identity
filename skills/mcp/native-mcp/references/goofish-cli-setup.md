# goofish-cli (闲鱼 CLI) — MCP Setup

**Installed:** 2026-06-02 via `uv tool install goofish-cli`
**Version:** 0.2.4
**GitHub:** https://github.com/fancyboi999/goofish-cli

## Installation

```bash
uv tool install goofish-cli
```

Installs 3 executables: `goofish`, `goofish-cli`, `goofish-mcp`.

## Authorization

```bash
# Auto-detect from browser cookies
goofish auth login --browser brave

# Check auth status
goofish auth status
```

`goofish auth login` uses `browser-cookie3` to extract cookies from Chrome/Edge/Brave/Safari. The user must be logged into https://www.goofish.com in the target browser first.

Required cookies: `unb` and `_m_h5_tk`.

## MCP Integration

```bash
# Run as MCP server (stdio)
goofish-mcp
```

Or add to `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  goofish:
    command: "goofish-mcp"
```

## Commands

| Category | Commands |
|----------|----------|
| `auth` | `login`, `reset-guard`, `status` |
| `item` | CRUD operations |
| `search` | Search listings |
| `message` | Messaging |
| `category` | Categories |
| `location` | Location |
| `media` | Media upload |

## Known Issues

- China internet: GitHub raw content may be blocked; use proxy for first install
- Auth requires browser session; headless auth via QR code (`--qr`) not tested yet
