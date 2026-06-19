# Feishu Wiki (飞书文档) Content Extraction

## Background

Feishu (飞书/Lark) is ByteDance's enterprise collaboration platform (analogous to Notion/Confluence). Wiki documents are hosted at `my.feishu.cn/wiki/<TOKEN>`. These are SPAs that require authentication to view full content.

## Access Behavior

| State | What's visible |
|-------|---------------|
| **Not logged in** | Page title, TOC/section outline, author name, "Log In or Sign Up" button |
| **Logged in** | Full document content, images, code blocks |
| **Public share link** (`.../wiki/<TOKEN>?from=from_copylink`) | Sometimes full content, sometimes login wall — depends on share settings |

## Detection: Anonymous vs Authenticated

```javascript
document.querySelector('.suite-docx.anonymous')  // null if logged in
```

The `anonymous` class on `#mainContainer` is definitive — when present, content is blocked regardless of TOC visibility.

## Extraction Strategies

### Strategy 1: Via browser with active session (if logged in)

If the user has a Feishu session in their browser (Brave/Chrome), navigate with CDP:

```python
browser_navigate(url="https://my.feishu.cn/wiki/<TOKEN>")
browser_snapshot()
browser_console(expression="document.body.innerText")
```

**When it fails:**
- `browser_snapshot` shows only TOC + "Log In" — session is expired or not present
- Browser console returns empty — content loaded in iframe or Shadow DOM

### Strategy 2: Public share link

Some Feishu docs have a public share toggle. Try the `?from=from_copylink` parameter or check if the doc uses `xxx.feishu.cn/wiki/...` (tenant domain) rather than `my.feishu.cn` (personal).

### Strategy 3: Open API (requires tenant token)

Feishu Open API requires an authenticated access token. Returns `403` / `99991661` without auth.

### Strategy 4: Playwright CLI Headless Browser (when CDP unavailable)

When CDP port 9222 is unreachable (Brave not running, remote Mac, or connection issue), use `npx playwright` as a standalone headless browser:

```bash
# Install (one-time)
npm install playwright
npx playwright install chromium

# Run extraction script
node /tmp/feishu-extract.js
```

**Script template (`/tmp/feishu-extract.js`):**

```javascript
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });

  await page.goto('https://my.feishu.cn/wiki/<TOKEN>', {
    waitUntil: 'domcontentloaded', timeout: 30000
  });
  await page.waitForTimeout(3000);

  // Scroll to trigger Svelte virtual scroller
  for (let i = 0; i < 30; i++) {
    await page.evaluate(() => window.scrollBy(0, 400));
    await page.waitForTimeout(200);
  }

  const text = await page.evaluate(() => {
    const main = document.querySelector('.page-main');
    return main ? main.innerText : document.body.innerText;
  });

  console.log(text);
  await browser.close();
})().catch(err => { console.error(err); process.exit(1); });
```

**Pitfalls:**
- Svelte virtual scrolling means only blocks near viewport are rendered — use the scroll loop to trigger rendering of ALL blocks
- `waitUntil: 'load'` may timeout — use `'domcontentloaded'`
- `document.querySelector('.page-main').innerText` returns only currently-rendered blocks — multiple scroll passes may be needed
- The `suite-docx.anonymous` CSS class definitively indicates login wall (content not rendered even after scrolling)

**When this fails:** Feishu returns `200` with no content body for anonymous users on `my.feishu.cn` (personal workspace). Try the tenant domain (`xxx.feishu.cn/wiki/...` instead of `my.`).

#### Svelte Virtual Scroller Unmounting (Critical)

Feishu's Svelte virtual scroller does NOT accumulate rendered blocks. Blocks that are scrolled **past** are **unmounted** (removed from DOM). This means:

- Scrolling to bottom then back up → only top blocks are rendered, middle content is lost
- Multiple scroll passes (3 rounds of scroll-down-then-back-up) still miss content
- Only content in/near the current viewport at extraction time is in the DOM
- `document.querySelector('.page-main').innerText` returns only the currently-rendered window

**Detection of incomplete extraction:**
```javascript
document.body.innerText.includes('Comments (0)');  // present = bottom reached
document.querySelector('.page-main').innerText.length;  // ~400 chars = barely any content
```

**Workarounds when scroll fails:**
- Try the **Redux store** (see Strategy 7 below) — may have full data even when DOM doesn't
- Try **TOC hash navigation** — clicking sidebar links (e.g. `#Q15`) loads that section into the DOM
- Collect text section-by-section via hash clicks rather than scrolling

### Critical Limitation: Svelte Virtual Scroller with Variable-Height Blocks

Feishu's Svelte virtual scroller has a **fixed render budget** — only blocks within ~2-3 viewport heights of the current scroll position are rendered into the DOM. This means:

- **Aggressive scrolling alone is NOT sufficient** for image-heavy, file-heavy, or mixed-content documents
- Each scroll pass triggers rendering of new blocks, but previously scrolled-past blocks may be removed from the DOM (unmounted)
- Scroll height changes dynamically as new blocks render
- Observed result: only ~413 chars rendered (title + first sentence) out of a multi-page document

**Why this happens:**
1. Svelte keeps a sliding window of rendered blocks (viewport + buffer)
2. Blocks outside this window are unmounted (removed from DOM)
3. Scrolling to bottom triggers bottom blocks, but middle content is skipped
4. Variable-height blocks (images, file attachments) make scroll position unreliable

**Detection of fully-loaded content:**
```javascript
document.body.innerText.includes('Comments (0)');
```

### Strategy 5: Redux store inspection (when logged in)

Feishu uses Redux:

```javascript
const state = window.store.getState();
// slices: appState, indexes, docx, docxState, wiki_base, wikiV2, workspace_next
```

The `docx` slice has metadata (editable, permissions, cover) but NOT document blocks for anonymous users.

### Strategy 7: Redux Store Inspection (when page is partially loaded)

Feishu uses Redux under the hood. Even when the DOM has sparse content, the Redux store may contain document data:

```javascript
const state = window.store.getState();
// Available slices (anonymous users):
//   docx       — metadata (editable, permissions, cover, subscription)
//   docxState  — {jira, agenda} (usually empty for anonymous)
//   entities   — users, permissions, folders, but NOT docx blocks
//   wiki_base  — space info
//   wikiV2     — page tree
```

**For anonymous users:** The `docx` slice has metadata but NO blocks — blocks are loaded via API only after authentication.

**For authenticated users:** Block data may be in `entities.docx` or a Svelte component store.

**Detection approach:**
```javascript
const state = window.store.getState();
if (state.docx && state.docx.root) {
  // Root page ID present — potentially loadable
}
if (state.entities && state.entities.docx) {
  // Block data may be here
}
```

**Alternative: React component inspection**
The page content is managed via `window.PageMain` (a React component):

```javascript
// PageMain.keys → [props, context, refs, updater, offlineSub, ...]
const editor = window.PageMain.editor;
// editor has rootElement, containerRef, preContainerWidth, etc.
// editor.state exists but does NOT contain document blocks
```

**Pitfall:** The Redux store for anonymous users only has metadata (docx, permissions, subscription), not the actual document blocks. Block data is loaded server-side after auth, not stored in Redux for unauthenticated sessions.

### Strategy 6: User-provided content

When all automated approaches fail, ask the user:
1. Are you logged into Feishu in this browser?
2. Is there a public share link (tenant domain, not `my.`)?
3. Can you paste the text content here?

## Svelte Virtual Scrolling (Lazy Block Rendering)

Feishu wiki uses Svelte with **virtual scrolling** — only blocks visible in/near the viewport are rendered into the DOM. This means:

- `document.body.innerText` only returns ~1700 chars (TOC + file attachments + bottom FAQ)
- The main tutorial content (Step 1, Step 2 with images) is NOT in the DOM

**Techniques to force block rendering:**

1. **Full page scroll** — scroll all the way down and back up in 400px steps with 200ms delays
2. **Multiple scroll passes** — Svelte renders blocks incrementally; one pass may not catch everything
3. **Playwright scroll loop** — the script above uses 30 steps × 400px = 12000px of scrolling

## Pitfalls

- **SPA rendering delay**: Feishu is Svelte-based. Wait 3-5s after navigation.
- **Cross-origin iframe**: Document content may load in an iframe. Check `browser_snapshot.frame_tree`.
- **Session cookie**: Feishu uses `ssid` + `session` cookies under `.feishu.cn`. CDP from the same profile picks them up.
- **CORS from curl**: Direct HTTP requests return login page. No server-side content embedding.
- **Playwright launch latency**: First run downloads browser (~150MB Chromium). Subsequent runs are fast.
- **Headless detection**: Feishu may show different content to headless browsers vs headed browsers. Try `headless: false` if content is still blocked.
