# Chinese Web Portal Automation (CDP)

Techniques for navigating Chinese carrier/government web portals that use aggressive anti-bot measures, SPA architecture, and new-window navigation.

## Portal: China Mobile 10086.cn

### URL Structure
- **Main portal:** `https://www.10086.cn/index/bj/index_100_100.html`
- **Personal account (SPA):** `https://shop.10086.cn/i/?welcome={TIMESTAMP}`
- **Plan selection:** `https://shop.10086.cn/list/140_791_798_0_0_0_0.html`
- **Service query (SPA):** `https://shop.10086.cn/i/?act=service_query` (React Router ignores URL params)
- **Online chat (Vant UI):** `https://wx.10086.cn/website/zxkf/h5new/index.html?service_token=...`
- **Plan detail m-site:** `https://wap.hb.10086.cn/wapres/wap-h5/dobusiness/QQT5GA.html`
- **Province service page:** `https://www.10086.cn/support/bj/` (Beijing)
- **Shop search:** `https://shop.10086.cn/list/140_791_798_0_0_0_0.html?keyword=...`

### Login Methods
The login page `https://www.10086.cn/` offers 3 tabs:
1. **短信随机码登录** (SMS code) — phone + SMS code, uses ID `sms_login_1`
2. **互联网用户登录** (email/password) — for internet account users, ID `mail_login_1`
3. **扫码登录** (QR code scan) — scan via China Mobile app, ID `qrcode_login_1`

The QR code login requires the China Mobile app. After scanning on iPhone, the browser page redirects to the personal account.

### CDP Target Management

**Critical:** 10086.cn opens links in NEW CDP targets (tabs). `browser_navigate` may switch our context to a different tab (e.g. `chrome://welcome/`). Always verify via CDP:

```python
# 1. List all targets after a click
targets = await cdp.invoke("Target.getTargets")
for t in targets["result"]["targetInfos"]:
    print(t["title"], t["url"][:60], t["targetId"][:16])

# 2. Evaluate on the correct target by target_id
result = await cdp.invoke("Runtime.evaluate", {
    "expression": "document.body.innerText.substring(0,5000)",
    "returnByValue": True
}, target_id="4E9B9D0D01C0AB37C02E76841C523124")
```

### SPA Content: JS Fallback

The shop.10086.cn site is a React/SPA (Vant UI component library). `browser_snapshot` shows the shell but not dynamic content. Always use **CDP Runtime.evaluate** directly on the correct target to get rendered text:

```python
result = await cdp.invoke("Runtime.evaluate", {
    "expression": "document.body.innerText",  # or innerHTML
    "returnByValue": True
}, target_id=target_id)
```

The site ignores URL params like `?act=service_query` — navigation is internal via React Router. Use JavaScript clicks on menu items instead.

### SPA Chat (在线客服) — Vant UI Pitfalls

The online chat at `wx.10086.cn` uses Vant UI (Vue component library). Known issues with programmatic interaction:

1. **Send button is `display: none` until input activates** — class `send-btn`, initially hidden. Vant only shows it when it detects real user input through its Vue reactivity system.
2. **`Event('input')` dispatch does NOT work** — Vant's v-model binding doesn't react to synthetic events. Setting `ta.value` + dispatching `input` event results in "不能发送空白消息" error.
3. **Native value setter works to set text** — using `Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set.call(ta, text)` followed by `dispatchEvent(new Event('input', {bubbles:true}))` sets the value in the DOM, but Vant may still treat it as empty depending on version.
4. **`Input.dispatchKeyEvent` (CDP) works reliably** — sending real keystrokes via CDP's `Input.dispatchKeyEvent` with `type: 'char'` triggers Vant's reactivity properly. After at least one real keystroke, the send button becomes visible and programmatic clicks work.
5. **Button visibility check** — use `window.getComputedStyle(btn).display` to check if the send button is actually showing. It changes from `none` → `block` only after real Vant-reactive input.

Workaround pattern:
```python
# Step 1: Focus the textarea
ta.focus()

# Step 2: Send one real keystroke via CDP to wake up Vant reactivity
await cdp.invoke("Input.dispatchKeyEvent", {
    "type": "char", "text": "т", "key": "т", "code": "KeyT",
    "unmodifiedText": "т"
}, target_id=chat_target)

# Step 3: Now set full text + send
ta.value = "..."
ta.dispatchEvent(new Event('input', {bubbles: true}))
document.querySelector('.send-btn').click()
```

### Key Account Sections (left menu, SPA)

| Chinese Label | Meaning | Notes |
|---|---|---|
| 交话费 | Top Up | Recharge phone credit |
| 我的账户 | My Account | Check balance, billing info |
| 账单查询 | Bill Query | Current month billing cycle + breakdown |
| 详单查询 | Call/Data Detail | Itemised records |
| 套餐余量查询 | Plan Balance | Remaining minutes, data, SMS |
| **业务查询退订** | **Service Query/Cancel** | **Active services with START/END dates** |
| 交费记录查询 | Payment History | Past payments |
| 呼死你-防护业务设置 | Harassment Call Block | Settings |
| 归属地查询 | Number Location Lookup | |
| 高频电话骚扰防护设置 | Spam Call Protection | Settings |
| 我的信息 | My Info | Personal details |
| 我的订单 | My Orders | Recent purchases (phones, devices — NOT plan changes!) |
| 售后服务 | After-sales | Returns, repairs |
| 我的邮箱 | My Mailbox | Carrier email |

### Finding Future Plan Changes (业务查询退订)

This is the section to verify when a new plan starts next billing period. The page displays a table:

| 业务名称 | 资费标准 | 订购时间 | **生效时间** | **失效时间** | 退订时间 |
|---|---|---|---|---|---|
| 全球通5GA尊享套餐199档 | 199.00 | 2026-05-15 | **2026-06-01** | 生效-- | - - |
| 新智享套餐129（2024版） | 129.00 | 2026-01-09 | 2026-01-09 | **2026-06-01** | - - |

- **生效时间** = when the plan starts being active
- **失效时间** = when the plan expires
- A plan with 生效时间 of 2026-06-01 and 失效时间 "生效--" means it will BEGIN on June 1st
- The old plan's 失效时间 on the same date confirms the swap happens on the billing cycle boundary

### Billing Period Info

From 账单查询 page:
- **计费周期: 05月01日-05月21日** — billing cycle is calendar month (1st to last day)
- Data resets on the 1st of each month
- The current month's running total is shown as "当月消费" under 我的账户
- Bill generation timestamp shown: "账单生成时间: 2026-05-21 08:27:17"

### Available Plans (Jiangxi/Jingdezhen region 江西/景德镇)

Current plans available:
- **新智享套餐159（2024版）** — 159元, upgrade from 129
- **新畅享套餐89（2024版）** — 89元
- **新畅享套餐59（2024版）** — 59元
- **2018自由选套餐** — flexible
- **2023飞享套餐39** — 39元
- **2022飞享套餐29** — 29元
- **新智享套餐129（2024版）** — current plan

Note: 全球通5GA尊享套餐199档 does NOT appear in the public plan list (shop.10086.cn). It was applied in-store as a service modification and only shows in 业务查询退订.

### 全球通5GA尊享套餐199档 Details

Known from Baidu search + official m-site (`wap.hb.10086.cn/wapres/wap-h5/dobusiness/QQT5GA.html`):

| Field | Value |
|---|---|
| Price | 199元/月 |
| Brand tier | 全球通金卡 |
| Network | 5G-A (5G Advanced, enhanced speed) |
| Contract | 3 years, auto-renew |
| Included | Airport lounge access, video streaming VIP, various privileges |
| More expensive tiers | 399元 (200GB+2100min, 钻卡), 599元 (400GB+3150min), 799元 (500GB+4200min), 999元 (600GB+5300min) |

Exact data/voice allocation for 199档 was NOT shown on the official m-site — the page only listed 399+ tiers. The 199 tier may share features with the 金卡 package.

### Plan Change Sequence

To check future-dated plan changes:
1. Login at `https://www.10086.cn/` (QR code via app)
2. Click "网上营业厅" → "我的移动"
3. Click "业务查询退订" in the left sidebar
4. Read the table — it lists ALL services with their 生效时间 (effective date) and 失效时间 (expiry date)

**CRITICAL:** This info is NOT in "我的订单" (My Orders). That section shows purchase orders for devices/accessories only. Future tariff changes appear exclusively in 业务查询退订. In-store applied changes may not appear in any online plan catalog — only in the service modification table.

## General Pattern for Chinese Web Portals

1. **SPA + new-window navigation** — clicks often open new CDP targets. Use `Target.getTargets` + `Runtime.evaluate` with explicit `target_id`.
2. **`browser_navigate` changes CDP context** — after calling it, the active tab may be `chrome://welcome/`. Always check and switch back.
3. **QR code login is standard** — Chinese carrier sites prefer QR scan via mobile app over passwords.
4. **Login session cross-domain** — 10086.cn and shop.10086.cn share session via top-level domain cookies, but the SPA may show "登录" until navigation triggers session retrieval. Opening any logged-in URL from the main portal (e.g. shop.10086.cn/i/...) is enough — the session cookie is already there.
5. **Text extraction via innerText** — `browser_snapshot` is useless for SPAs. Always use `document.body.innerText` via CDP `Runtime.evaluate` with explicit `target_id`.
6. **Plan changes appear in 业务查询退订 not 我的订单** — this is confusing because the change IS an "order" placed in-store, but the carrier tracks it as a service modification, not a purchase order.
7. **Vant UI reactive fields** — don't trust synthetic JS events for input fields. Use CDP `Input.dispatchKeyEvent` for at least one keystroke, then programmatic events for the rest.
8. **SEO/sitemap pages load faster** — if the SPA is slow, try the pure-HTML sitemap at `https://www.10086.cn/sitemap/` for links.
9. **Browser fingerprint** — some Chinese portals check `navigator.webdriver`. CDP-override (`cdp_override` stealth feature) helps but may not be sufficient. Consider Playwright on the headless Mac (China IP) for truly blocked services.
