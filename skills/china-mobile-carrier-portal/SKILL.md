---
name: china-mobile-carrier-portal
description: "Automate Chinese mobile carrier web portals (10086.cn, 联通, 电信) — login, account info, tariff plans, customer support chat"
tags: ["web-automation"]
---

# China Mobile Carrier Portal Automation

Automate interactions with Chinese mobile carrier websites: 中国移动 (10086.cn), 中国联通, 中国电信. Covers login, tariff plan lookup, billing info, and online customer service chat.

## Supported Sites

- **10086.cn** — China Mobile. Main site (10086.cn) and shop (shop.10086.cn). Two separate auth domains.
- **联通 / 电信** — follow same patterns; adapt selectors.

## Key Architecture

### Two Domains for 10086
- `www.10086.cn` — main portal, login via SMS/QR/email
- `shop.10086.cn` — personal cabinet, SPA (Vue/Vant UI)
- Login on one does NOT carry to the other. Always check for "登录" vs "134****7315" in the header.

### SPA Behavior (shop.10086.cn)
- URL query params are IGNORED. Navigation is JS-driven.
- Menu items (`#my-account`, `#service-query`) don't change URL.
- CDP `Runtime.evaluate` + `click()` on menu links works, but only if you wait and check the right target.
- Links with `href=""` or `javascript:void(0)` are JS-triggered. Click then wait 3-5s for DOM update.

## Workflow Steps

### 1. Launch CDP Browser
```bash
/Applications/Brave\ Browser.app/Contents/MacOS/Brave\ Browser --remote-debugging-port=9222 --new-window --user-data-dir=~/.config/brave-cdp
```
Use `terminal(background=true)` for the process, then verify with `curl http://127.0.0.1:9222/json/version`.

### 2. Navigate and Login
```python
browser_navigate(url)  # main 10086.cn page
browser_snapshot()      # check for login status
```
Login options: SMS code, QR scan (mobile app), email/password (互联网用户).

### 3. Access Personal Cabinet
After login, navigate to shop.10086.cn. Click links via CDP Runtime.evaluate + click():
```javascript
var el = [...document.querySelectorAll('a')].find(a => a.textContent.includes('需要点击的文字'));
if(el) { el.click(); 'clicked'; }
```

### 4. Read Account Data
After clicking a menu item, wait 3-5s, then read content via CDP:
```javascript
document.body.innerText.substring(0,5000)
```
Always specify the target tab ID in `target_id` parameter.

### 5. Find Tariff Changes
Navigate to "业务查询退订" → "我的套餐" section. Shows active plans, pending changes, effective dates.

The page shows a table with columns: 业务名称, 资费标准, 订购时间, 生效时间, 失效时间, 退订时间.
- Current plan has a 失效时间 (expiry date)
- New plan has a 生效时间 (start date) matching the current plan's 失效时间
- Use this to confirm upcoming tariff switches

Example data (from session):
```
全球通5GA尊享套餐199档    199.00    2026-05-15    2026-06-01   生效--    - -
新智享套餐129（2024版）  129.00    2026-01-09    2026-01-09    2026-06-01  - -
```

### 6. Tariff Detail Pages (SPA Issues)

The 全球通5GA尊享套餐 detail page at `https://wap.hb.10086.cn/wapres/wap-h5/dobusiness/QQT5GA.html` is a mobile SPA with lazy-loaded content.

**To see all tariff tiers**, click the "更多档次" element (class `.select-more-toggle`), which reveals hidden plan options:
```javascript
document.querySelector('.select-more-toggle').click()
```

**Complete tariff table for 全球通5GA尊享套餐** (中国移动, verified from official page):
| Price | Status | Traffic | Minutes |
|-------|--------|---------|---------|
| 199元 | 全球通金卡 | 100 GB | 600 min |
| 299元 | 全球通白金卡 | 150 GB | 1050 min |
| 399元 | 全球通钻卡 | 200 GB | 2100 min |
| 599元 | 全球通钻卡 | 400 GB | 3150 min |
| 799元 | 全球通钻卡 | 500 GB | 4200 min |
| 999元 | 全球通钻卡 | 600 GB | 5300 min |

Tariff data is often more complete on Baidu search results than on the official site. Use queries like:
```
https://www.baidu.com/s?wd=全球通5GA尊享套餐199档+流量+分钟
```

### 7. Online Customer Service Chat
- Opens in a new tab (popup). Find it via `Target.getTargets()`.
- URL pattern: `wx.10086.cn/website/zxkf/h5new/`
- Built with Vant UI (Vue component library).
- Real-time chat messages pop up as new DOM elements — poll `.innerText` after 5-6s.

#### Chat Input Pitfalls
The Vant textarea does NOT react to simple `element.value = '...'` and Event dispatch. Use:
```javascript
var nativeInputValueSetter = Object.getOwnPropertyDescriptor(
  window.HTMLTextAreaElement.prototype, 'value'
).set;
nativeInputValueSetter.call(textarea, 'your message');
textarea.dispatchEvent(new Event('input', {bubbles: true}));
```

#### Send Button Discovery
The `.send-btn` element starts with `display: none`. Vant shows it when the field has content AND the React state updates. After setting value, query:
```javascript
var btn = document.querySelector('.send-btn');
```
If found, click it. If still hidden, the Vant state didn't update — retry with Input.dispatchKeyEvent for one char first.

**If chat send keeps failing**, fall back to Baidu search for tariff details — it's often more reliable for finding tariff specs than struggling with the chat bot.

#### Complete Chat Send Recipe (Debugged May 2026)

```javascript
// 1. Focus and type one character via Input.dispatchKeyEvent to trigger Vant state
document.querySelector('textarea.van-field__control').focus();
// (send one real char via Input.dispatchKeyEvent in CDP)

// 2. Then set the full value
var nativeInputValueSetter = Object.getOwnPropertyDescriptor(
  window.HTMLTextAreaElement.prototype, 'value'
).set;
nativeInputValueSetter.call(textarea, 'your message');
textarea.dispatchEvent(new Event('input', {bubbles: true}));

// 3. Send button may still be hidden. Make it visible:
var btn = document.querySelector('.send-btn');
btn.style.display = '';
btn.click();

// 4. Wait 5-6s, poll .innerText for response
```

**If chat sends still fail after all attempts**, fall back to Baidu search — it's faster and more reliable for tariff discovery.

### 8. Chongqing-Specific Promo Tariffs (Promo/线上专享)

Chongqing (重庆) has special online-exclusive high-traffic plans NOT available in the standard "办套餐" listing. These are typically marketed on third-party sites (搜狐, 多鲲通信, 阿里云优惠网) and activated through delivery-activation flows.

#### How to Find Them
Search Baidu with queries targeting Chongqing:
```
https://www.baidu.com/s?wd=重庆移动+大流量+促销+套餐+线上+专享+100G+200G+300G
https://www.baidu.com/s?wd=移动大流量卡+29元+全国通用+2025+2026
```

#### Known Chongqing Promo Plans (as of May 2026)

| Plan Name | Price | Total Traffic | National Traffic | Local Traffic | Notes |
|-----------|-------|--------------|-----------------|---------------|-------|
| 星语卡 | 29→39元/月 | 135G | 105G通用 + 30G定向 | — | 2yr contract, best value |
| 明辉卡 | 29→39元/月 | ~220G | 20G | ~200G | Local-only bulk |
| 雾都卡 | varies | ~190G | 20G | 170G | Local-only bulk |

**Key insight:** Standard national plans (全球通5GA) are expensive per-GB. Promo plans like 星语卡 offer 105G national traffic for 29元 — ~7x cheaper per GB than 全球通5GA at 199元/100GB. However, promo plans often require a new SIM and are for new subscribers only.

#### Pitfalls with Promo Plans
- **"200G" claims often include mostly local-only traffic.** Local traffic is unusable outside the home province.
- **定向流量 (directed traffic)** only works on specific apps (抖音, 爱奇艺, etc.) — not a substitute for general-purpose 通用流量.
- **Activation**: usually delivered by courier who helps activate on the spot, or self-activation via the China Mobile app.
- **Contract length**: typically 12-24 months; early termination may incur fees.
- **Not available for existing users changing plans** — usually requires a new phone number (新入网).

### 7. Searching Tariff Details
Tariff "全球通5GA尊享套餐199档" may NOT appear in the "办套餐" listing (only shows standard plans). Search Baidu instead:
```
https://www.baidu.com/s?wd=全球通5GA尊享套餐199档+流量+分钟
```
Then click results from: 多鲲通信, 百度百家号, 什么值得买.

## Aliyun Drive (阿里云盘) — Quick API Reference

Aliyun Drive (alipan.com) has refresh_token-based auth and a REST API useful for programmatic file access.

### Getting Fresh Access Token

The access token lives in `localStorage['token']` after login on the web app. Extract via CDP:

```javascript
var t = JSON.parse(localStorage.getItem('token'));
t.access_token  // Bearer token (expires ~20 min)
t.refresh_token // Long-lived token (~30 days)
```

### Token Refresh (Public Endpoint — No App Registration Needed)

```bash
curl -s -X POST 'https://api.aliyundrive.com/v2/account/token' \
  -H 'Content-Type: application/json' \
  -d '{"refresh_token":"REFRESH_TOKEN_HERE","grant_type":"refresh_token"}'
```

Returns fresh `access_token` + new `refresh_token`. The public endpoint works without registering a custom OAuth app.

### Key API Endpoints

| Endpoint | Method | Body | Description |
|----------|--------|------|-------------|
| `/v2/user/get` | POST | `{}` | User profile |
| `/v2/drive/get` | POST | `{"drive_id":"..."}` | Drive info (size, used) |
| `/v2/account/token` | POST | `{"refresh_token":"...","grant_type":"refresh_token"}` | Refresh token |

### Drive Info Response Example

```json
{"total_size": 9440338116608, "used_size": 0, "drive_type": "normal", "status": "enabled"}
```

Note: `drive_id` comes from the user info response or can be hardcoded from localStorage.

### WebDAV (Official vs Third-Party)

- **Official WebDAV**: Alipan app has a WebDAV setting tab, but it requires 三方权益包 subscription (~30元/月)
- **aliyundrive-webdav (OSS)**: Install via pip:
  ```bash
  pip3 install aliyundrive-webdav
  aliyundrive-webdav --refresh-token TOKEN --port 18080 --root /
  ```
  Runs a local WebDAV server on port 18080. Connect in Finder via `Cmd+K` → `http://127.0.0.1:18080`
- The pip version `aliyundrive-webdav-2.3.3` works on macOS ARM. npm package is deprecated/removed.

### Pricing Tiers (Confirmed May 2026)

| Plan | Price | Storage | Notes |
|------|-------|---------|-------|
| Free | 0元 | 105 GB | — |
| 超级会员 (1 month) | 30元 | 8 TB | — |
| 超级会员 (1 year) | 198元 | 8 TB | Standard annual |
| 超级会员 (1st year promo) | 148元 | 8 TB | Only for new subs |

Payment via Alipay. After purchase, the dashboard changes from "会员中心" button to "会员生效中" status with updated capacity.

### Refresh Token Lifespan

The same `refresh_token` string persisted across multiple 20-min cycles during the session. It may eventually expire after ~30 days of inactivity.

### Gotchas
- The npm package `aliyundrive-webdav` is no longer in the registry. Use the pip version instead.
- The pip version rejects tokens from expired sessions. Refresh via `/v2/account/token` first.
- cua-driver screenshot for WebDAV verification is blocked without Screen Recording permission.
- Official Alipan Open API portal (open.aliyundrive.com) returns 500 errors. The public token endpoint works without it.

See `references/aliyundrive-api.md` for a condensed reference with no session-specific details.

## Promo Tariffs (线上专享/大流量卡)

China Mobile offers special online-only promo plans ("流量卡") through third-party distributors. These are typically MUCH cheaper per-GB than standard postpaid plans, but require a NEW phone number (新入网).

### Where to Find Them

1. **Baidu search** with queries like:
   ```
   https://www.baidu.com/s?wd=重庆移动+大流量+促销+套餐+线上+专享+100G+200G+300G
   https://www.baidu.com/s?wd=移动大流量卡+29元+全国通用+2025+2026
   ```

2. **Third-party aggregator sites** (curated lists with links to order forms):
   - `simkazhijia.com` — SIM卡之家, well-organized catalog of 移动/联通/电信 promos
   - `duokun.com` — 多鲲通信
   - `sohu.com` — 搜狐 articles (often with affiliate links)

3. **Search strategy** for finding the right plan:
   - Always filter for "通用流量" (unrestricted national traffic) vs "定向流量" (app-specific) vs "省内流量" (province-only)
   - Search both: province-specific ("重庆移动 星语卡") and general ("移动沪享卡 全国通用")
   - Promos from other provinces (上海, 北京) often ship nationwide and work everywhere

### Key Traffic Types to Distinguish

| Chinese Term | Meaning | Where It Works |
|-------------|---------|----------------|
| 全国通用流量 | National general traffic | Anywhere in China |
| 省内通用流量 | Province-only traffic | Only in the issuing province |
| 定向流量 | App-directed traffic | Only specific apps (抖音, 爱奇艺) |
| 本地流量 | City-level traffic | Only in the issuing city |

**Critical pitfall:** A plan advertised as "220G大流量" may contain only 20G national + 200G local. Always check the breakdown before ordering — if traveling between provinces (e.g., 重庆→湖北), local/province traffic becomes unusable.

### How to Read Third-Party Listings

From simkazhijia.com, each plan card shows:
- **原套餐资费** — base plan (before promos)
- **优惠后月租** — effective monthly fee after top-up rebate
- **首充要求** — initial top-up required at delivery (usually 50元 or 100元)
- **流量构成** — traffic breakdown (通用 + 定向 + 省内)
- **合约期** — contract length (typically 12-24 months)

### Freshness Problem

simkazhijia.com has TWO tiers of content:
1. **Homepage** (`simkazhijia.com/`) — lists CURRENT promos with dates (e.g., "2026年 5月 19日"). These are fresh and actively orderable.
2. **Archive pages** (`simkazhijia.com/yidongliuliangka/`) — lists ALL historical promos with their original post dates (some as old as July 2024). Many of these are no longer available.

**Always check the homepage first** for the freshest promos. The archive pages are useful for research (what's possible) but order links on old entries may be dead.

### Order Flow

1. Find plan on simkazhijia.com (homepage or archive)
2. Click plan → detail page with link "→→→点此申请办理"
3. Link opens order form on `3.kazhijia.cn` with PID parameter
4. Order form is minimal — search box, some links (一证通查, 订单查询, 分享店铺, 客服帮助)
5. The 客服帮助 button is typically a static link, NOT a live chat

### Order Form Limitations

The 3.kazhijia.cn order platform:
- Requires search to find specific plans (search box at top)
- May not show the plan you clicked from — the PID parameter isn't always passed correctly
- Form fields require Chinese ID number format — foreign passports are likely rejected
- "客服帮助" opens a static page or WeChat QR code, not inline chat

### Verification

These promo plans are REAL China Mobile SIMs — they show up in the official APP and follow official tariffs. The discount comes from the carrier's promotional budget for new user acquisition, not from any shady source. But:
- Confirm the plan still exists (3rd-party listings can be stale by months)
- Read the fine print on 定向 and 省内 limits
- Prefer plans with auto-renewing 通用流量 over fixed-term promos

See `references/chongqing-promo-tariffs.md` for a detailed table of known Chongqing-specific promo plans.
See `references/national-promo-cards.md` for national (跨省-ready) high-traffic promo cards from various provinces.

## Ordering from Third-Party Aggregators (simkazhijia.com)

### Workflow

1. **Find plan** on simkazhijia.com (catalog page → click plan name → detail page)
2. **Get order link**: on the detail page, find the "→→→点此申请办理" link
   ```javascript
   // Extract the order URL
   var link = document.querySelector('a'); // find the one with text '点此申请'
   link.href  // something like https://3.kazhijia.cn/order/index?uid=...&pid=...
   ```
3. **Navigate to order page** — this opens a form with fields: name, ID, address, phone
4. **Fill form** using CDP Runtime.evaluate with value setters
5. **Submit** order

### Order Form Pitfalls

- The order form is on a **separate domain** (kazhijia.cn) — navigation changes CDP target
- Form fields may use Vant UI or similar — test with native value setter pattern
- After submission, the site shows a confirmation message and the SIM ships by courier

### Foreign Passport (外国护照)

**Critical blocker:** Most promo SIMs from aggregators require 身份证 (Chinese ID). Foreign passport holders should:
1. Click "客服帮助" on the order page to open WeChat/online chat and ask "外国人护照可以办理吗?"
2. Alternatively, use the official China Mobile APP directly — some apps have a passport-friendly signup flow
3. Visit a physical营业厅 in the target province — this is the most reliable option for foreigners

**Common China Mobile answer for foreigners:** Physical stores CAN process passport activation for standard plans. The ultra-cheap promo plans (19-29元 for 185G+) are online-channel only and typically require 身份证. Show the operator the official listing URL and ask if they can match it.

### Known Working Alternatives for Foreigners

- **China Mobile official APP** → some online-only promos accept passport (test each one)
- **Physical 10086 store** → bring passport, ask about 大流量套餐
- **第三平台** (e.g., 京东, 淘宝) → some 3rd-party stores on JD/Taobao accept passport

See `references/ironclad-links-and-procedure.md` for the procedure to obtain "ironclad" evidence links.
See `references/taobao-login-procedure.md` for logging into Taobao/Tmall to access China Mobile官方旗舰店.

## Ordering from Taobao/Tmall (if Direct CDP Fails)

Both Tmall and Taobao reject CDP-driven automation (programmatic clicks, value setting, navigation). Symptom: page stays on homepage, search doesn't submit, login redirect loops.

**Solution:** Give the user a direct URL and let them navigate manually:
```text
https://zhongguoyidong.tmall.com/search.htm?search=y&category=50025119
```
OR search on JD:
```text
https://search.jd.com/Search?keyword=中国移动流量卡29元185G&enc=utf-8
```

### QR Login on Taobao May Produce Garbled Screenshots
Page `https://login.taobao.com/qrcodeLogin.htm` renders an SVG canvas QR code.
- CDP screenshot (4800x3000 Retina) can render as garbled lines — file is valid PNG but visually unreadable
- **Fix:** Fall back to SMS login immediately if QR screenshot looks wrong
- SMS login: enter phone → click "获取短信校验码" → enter code → click "确定/登录"

### Taobao/Tmall account security
- When logging in by SMS on Taobao, after entering the code the site may ask a verification question like "注册时间" (registration year). Pick from options (2021-2026). If wrong, try another.
- After login, Tmall may ask to bind a JD account if you used WeChat OAuth.
- Some accounts are restricted to APP-only for security reasons — you'll see "账号存在安全风险，暂无法在京东网页端使用" on JD.

## Pitfalls

1. **Target switching**: `browser_navigate()` may switch CDP context to `chrome://welcome/`. Always verify with `Target.getTargets()`.
2. **Stale snapshots**: `browser_snapshot()` on SPA pages often returns "(empty page)". Use CDP `Runtime.evaluate` with explicit target_id.
3. **Vant send button**: The `.send-btn` is `display:none` until Vant JS processes the input. Using native value setter + Input.dispatchKeyEvent works more reliably than simple value assignment.
4. **New tab links**: Many links on 10086.cn open in new tabs (popups). Check `Target.getTargets()` after clicking.
5. **browser_console stale data**: The console tool may return content from a different target after navigation. Always re-check target IDs.
6. **Dual auth**: shop.10086.cn and www.10086.cn are separate auth domains. Being logged in on one doesn't mean logged in on the other.

## Finding Promo Tariffs with National Traffic

Standard plans (全球通5GA, 新智享) are expensive per-GB. Promo plans (流量卡) from other provinces offer 185-275G national traffic for 19-39元/月.

### Search Strategy

Search Baidu with keywords targeting high-traffic national plans:

```bash
# General search
移动+大流量卡+29元+全国通用+2025+2026

# Province-targeted (to find plans that ship to Chongqing)
重庆移动+全国通用流量+大流量+线上套餐

# By plan name (once you know what to look for)
移动沪享卡+29元+275G+办理+线上
移动沪花卡+29元+203G+50分钟+办理
移动星沪卡+19元+188G+50分钟+办理
```

### Key Traffic Terms

| Term | Meaning | Cross-Province? |
|------|---------|-----------------|
| 全国通用流量 | National general traffic | ✅ Yes |
| 通用流量 | General traffic (usually national) | ✅ Usually yes |
| 定向流量 | App-directed only (抖音, 爱奇艺) | ❌ App-restricted |
| 省内通用流量 | Province-only traffic | ❌ No |
| 本地流量 | City-level traffic | ❌ No |

**Critical:** A plan advertised as "220G大流量" may be 20G national + 200G local. Always check the breakdown before suggesting to the user, especially if they travel between provinces.

### Sources for Promo Plans

Ranked by reliability:
1. **天猫 China Mobile官方旗舰店** — most authoritative, customer service available
2. **京东 China Mobile旗舰店** — same as above
3. **simkazhijia.com** — well-organized catalog, but may have stale listings
4. **搜狐 articles** — often contain working affiliate links
5. **什么值得买 (smzdm.com)** — user reviews + links

See `references/national-promo-cards.md` for the full table of known plans.
See `references/aliyundrive-api.md` for Aliyun Drive free API reference.

## Taobao/Tmall Login for China Mobile旗舰店

Tmall is the best authoritative source for ironclad proof of promo tariff existence.

### QR Login Procedure

1. Navigate: `https://login.taobao.com/qrcodeLogin.htm`
2. Take screenshot via `browser_vision()` or `Page.captureScreenshot`
3. Copy to Downloads: `cp <screenshot_path> ~/Downloads/taobao_login_qr.png`
4. User scans with Taobao or Alipay app (扫一扫 → 登录电脑版)
5. After scan, page auto-redirects. Check with `Target.getTargets()` after 5-10s

**Pitfall:** After login redirect, CDP context may switch to `chrome://welcome/` or other tabs. Always verify targets.

### QR Screenshot Quality Issue

The `qrcodeLogin.htm` page renders an SVG canvas QR code. The CDP screenshot (4800x3000 Retina) can come out as garbled lines instead of a readable QR. The file IS a valid PNG but the rendering artifact makes it unreadable.

**Fix:** Open `qrcodeLogin.htm` in the browser directly — it has the cleanest QR rendering of all Taobao login pages. If still garbled, fall back to SMS login immediately.

### SMS Login (Primary — More Reliable Than QR)

See `references/taobao-login-procedure.md` for the complete step-by-step SMS login procedure.

### After Login

1. Navigate: `https://www.tmall.com/`
2. Search: "中国移动官方旗舰店" or the specific plan name
3. Within the store, search for the tariff plan
4. Screenshot the listing WITH the store badge (官方旗舰店) visible
5. Use the chat (阿里旺旺) to ask about foreign passport acceptance

## Useful CDP Commands for This Skill

When CDP session loses context (common after page navigations that open new tabs), use:

```bash
# List all browser targets
curl -s http://127.0.0.1:9222/json/list | python3 -c "import sys,json; data=json.load(sys.stdin); [print(t['id'],t['title'][:60]) for t in data]"
```

Then activate a specific target:
```bash
curl -s -X PUT -d '{"targetId":"TARGET_ID"}' http://127.0.0.1:9222/json/activate/{targetId}
```

## Verification

- Check header for "欢迎来到中国移动网站" + masked phone number ("134****7315")
- Check "业务查询退订" page for two important dates: plan start date (订购时间) and plan end date (失效时间)
- For tariff change: look for two entries — current plan's 失效时间 and new plan's 生效时间 should match
- For promo tariffs: verify the plan listing is from China Mobile官方旗舰店 on Tmall/JD (best evidence) or from a reputable aggregator with working order links
