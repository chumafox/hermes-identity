# Playwright Setup for China Networking

## Why Playwright

When the built-in Hermes browser (Browserbase) is blocked by anti-bot measures,
Playwright offers a second headless-Chromium path. It has more human-like
fingerprints and can sometimes bypass lighter Cloudflare challenges.

## Local Installation

Prefer **local** install (cd to a temp dir, npm init, npm install) rather than
global or npx. This avoids:

- npx re-downloading playwright every time
- Permission issues with global npm installs
- Version drift between projects

```bash
cd /tmp
npm init -y 2>/dev/null
npm install playwright
npx playwright install chromium
```

Total download: ~150 MB (npm package + Chromium browser).
On slow Chinese WiFi: 10-30 minutes.  

**Run with `background=true`** — a foreground `npx playwright install chromium` will timeout  
at Hermes' default 120s timeout long before the download finishes:
```bash
# WRONG — Hermes terminal times out
npx playwright install chromium  # → Command timed out after 120s

# RIGHT — run in background
terminal(background=true, command="npx playwright install chromium", timeout=10)
```

If timeouts occur, the Chromium binary may be partially downloaded.  
Delete `~/Library/Caches/ms-playwright/` and retry.  
Chromium ~150 MB; at 60 KiB/s expect ~45 min.

## Verification Script

Write a test script, don't use `node -e` (Hermes security blocks it):

```js
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.goto('https://example.com', { timeout: 10000 });
  console.log('OK:', await page.title());
  await browser.close();
})();
```

Run with:

```bash
cd /tmp && node test_playwright.js
```

## Usage with appstorrent.ru

Cloudflare blocks Playwright on appstorrent.ru despite headless Chromium.
Always fall back to Safari + osascript (see `references/python-safari-scraper.md`)
when Playwright fails.

## Pitfalls

| Pitfall | Fix |
|---------|-----|
| `npx playwright` re-downloads package every time | Install locally with `npm install playwright` first |
| Chromium download times out at 90%+ | Try again — curl/aria2c also time out on CF-protected CDNs |
| `require('playwright')` not found | cd to dir with `node_modules/` or install globally |
| Electron apps need display (headless Mac) | Use CLI binaries (Claude Code, Cursor), not full .app bundles |
| macOS Gatekeeper blocks Chromium | `xattr -cr /path/to/chromium.app` if running headed |
