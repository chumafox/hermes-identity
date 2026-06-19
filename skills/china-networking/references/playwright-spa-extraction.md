# Playwright SPA Content Extraction

When a page requires JavaScript rendering (Svelte, React, Vue SPA) and CDP is unavailable, use Playwright CLI to extract content.

## One-time setup

```bash
cd /tmp && npm init -y --silent && npm install playwright
npx playwright install chromium
```

## Extraction script pattern

```javascript
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  await page.goto('https://example.com/spa-page', {
    waitUntil: 'load',
    timeout: 30000
  });
  await page.waitForTimeout(2000);
  
  // Scroll to trigger lazy rendering (Feishu, Notion, etc.)
  for (let i = 0; i < 30; i++) {
    await page.evaluate(() => window.scrollBy(0, 400));
    await page.waitForTimeout(200);
  }
  
  // Extract text
  const text = await page.evaluate(() => document.body.innerText);
  console.log(text);
  
  await browser.close();
})();
```

## Key points

- `waitUntil: 'load'` (not `'networkidle'`) — Feishu keeps polling, never idle
- Multiple scroll passes with delays — Svelte virtual scroller renders blocks lazily
- `viewport: { width: 1280, height: 900 }` — wider viewport renders more content
- For login-walled content, use `browserContext` with existing cookies or localStorage

## Why not CDP?

- Brave/CDP may not be running
- Page may have anti-automation checks that Playwright's stealth mode handles better
- Playwright runs in a fresh browser context, no cached state issues

## Cleanup

```bash
rm -rf /tmp/node_modules /tmp/package.json /tmp/package-lock.json
```
