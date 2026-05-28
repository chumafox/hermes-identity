# Session Findings — 2026-05-21

## China Mobile tariff hunting

### Current state
User (Chongqing, 134****7315, China Mobile):
- Current plan: 新智享套餐129（2024版）— 50GB + 1900min, 129元/月
- Auto-upgrading 1 June to: 全球通5GA尊享套餐199档 — 100GB + 600min, 199元/月
- User wants MORE national data for LESS money on a NEW local number

### 全球通5GA尊享套餐 — full tier table (from hb.10086.cn official page)

| Price | Status | Traffic | Minutes | 
|-------|--------|---------|---------|
| 199元 | 金卡 | 100GB | 600min |
| 299元 | 白金卡 | 150GB | 1050min |
| 399元 | 钻卡 | 200GB | 2100min |
| 599元 | 钻卡 | 400GB | 3150min |
| 799元 | 钻卡 | 500GB | 4200min |
| 999元 | 钻卡 | 600GB | 5300min |

Official page: https://wap.hb.10086.cn/wapres/wap-h5/dobusiness/QQT5GA.html

### Promo tariffs found (simkazhijia.com)

Best for national-only use: **移动星沪卡** 19元/月, 185GB national + 30GB定向 + 50min
Runner up: **移动沪享卡** 29元/月, 240GB + 30GB定向 + 100min

### Platform status
- simkazhijia.com: ✅ found tariffs, has order buttons → 3.kazhijia.cn store
- Tmall (zhongguoyidong.tmall.com): ❌ requires login, doesn't work with CDP automation
- JD.com: ❌ blocks web login, requires app
- 10086.cn customer service chat: ❌ Vant UI resists automation, AppleScript can send but not read WeChat

### Foreign passport issue
- Online promo tariffs require 中国身份证
- User needs to ask seller's WeChat support or visit physical office
- WeChat on Mac: AppleScript can SEND but cannot READ chat content (no Accessibility API exposure)
- cua-driver installed but needs Screen Recording permission for screenshots
