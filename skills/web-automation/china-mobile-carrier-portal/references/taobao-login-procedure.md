# Taobao SMS Login Procedure (Verified May 2026)

## Quick Steps

1. Navigate: `https://login.taobao.com/`
2. Click "短信登录" (SMS login tab)
3. Check the agreement checkbox
4. Enter phone number (e.g., 13479837315)
5. Click "获取短信校验码" (get SMS code)
6. Enter the 4-digit code
7. Click "确定" (confirm)

## Pitfalls

- **Code expires quickly.** If you get "校验码失效，请重新获取", click "获取短信校验码" again and enter the new code immediately.
- **Getting "验证身份" page after SMS login** — this is normal. It's Taobao's identity verification. Just enter the new code they send via SMS.
- **Register time question** — after login, Taobao may ask "注册时间" (when was this account registered?). Options: 2026, 2025, 2024, 2023, 2022, 2021. If you don't know, try 2024 or 2023 (typical for established accounts).
- **"t************2" masked account name** — this is normal, it just masks the full account name.
- **Tmall/Taobao shared auth** — logging into Taobao also logs you into Tmall (same session).
- **Session doesn't survive browser restart** — the CDP browser instance loses auth after `pkill`. Need to re-login.

## After Login on Tmall

- Tmall shows "tb703386058212" (or similar) in the top-right header
- Access to official stores (like China Mobile官方旗舰店) is available
- Search for "中国移动官方旗舰店" → category "号卡/套餐" (SIM cards & tariffs)
