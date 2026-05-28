# China Mobile Carrier SPA Sites — Practical Guide

## Overview

Chinese carrier sites (10086.cn, shop.10086.cn) are SPAs that load content dynamically.
Navigating them requires CDP (Chrome DevTools Protocol) with Runtime.evaluate.

## Login Flow (QR Code)

1. Navigate to https://www.10086.cn/index/bj/index_100_100.html
2. Click the '请登录' link (visible in initial snapshot)
3. On login page, select '扫码登录' (QR code tab)
4. User opens China Mobile app on phone -> scans QR code -> logged in
5. After login, masked phone number appears in top bar
6. Click '个人中心' to access dashboard

### Login state propagation

Login on www.10086.cn does NOT propagate to shop.10086.cn.
They use different subdomain cookies.
If not logged in on shop.10086.cn, the page shows a login button.
Navigate to shop.10086.cn separately after login on www.10086.cn.

## SPA Navigation Pitfalls (shop.10086.cn)

- browser_click refs become stale after ANY navigation (DOM re-renders)
- Clicking sidebar links (业务查询退订, 账单查询) triggers XHR - snapshot shows empty
- Solution: use browser_cdp with Runtime.evaluate + target_id
- Links may open in new tabs (target=_blank) - monitor via Target.getTargets
- URL query params have no effect (SPA ignores them)

## Key Pages (after login on shop.10086.cn)

Use CDP Runtime.evaluate to read SPA content via target_id.

### 业务查询退订 (Plan Change Verification)

Shows a table with columns:
- 业务名称 (plan name)
- 资费标准 (price)
- 订购时间 (order date)
- 生效时间 (effective date)
- 失效时间 (expiry date)
- 退订时间 (unsubscribe date)
- 操作 (actions)

This is where you find FUTURE plan changes:
- Current plan: 失效时间 = next billing period start
- New plan: 生效时间 = next billing period start, 失效时间 = 生效--
- A plan with future 生效时间 = will activate on that date

### 账单查询 (Billing)

Shows billing period (e.g. 05月01日-05月21日), current charges itemized:
- 套餐及固定费 (plan & fixed fees)
- 套餐外上网费 (overage data)
- 套餐外短彩信费 (overage SMS)
- Total with discounts

### 套餐余量查询 (Usage Left)

Shows remaining for each plan component:
- Voice minutes (语音), Data (流量), SMS
- Per-component breakdown with percentages

## CDP Tab Management

Use these CDP methods for SPA navigation:

```bash
# List all tabs
browser_cdp method="Target.getTargets"

# Read page content from specific tab
browser_cdp method="Runtime.evaluate" target_id="TAB_ID" \
  params='{"expression":"document.body.innerText.substring(0,5000)","returnByValue":true}'

# Click sidebar link via JS (more reliable than browser_click)
browser_cdp method="Runtime.evaluate" target_id="TAB_ID" \
  params='{"expression":"[...document.querySelectorAll(\"a\")].find(a => a.textContent.includes(\"TEXT\")).click()","returnByValue":true}'
```

## Sample Plan Table

| Plan | Price | Data | Voice | Notes |
|------|-------|------|-------|-------|
| 新智享套餐129（2024版） | 129元/月 | 50GB | 1900 min | 全球通银卡 |
| 全球通5GA尊享套餐199档 | 199元/月 | 5G-A | varies | 全球通金卡 |

Billing cycle: 1st - last day of month (standard for China Mobile).
