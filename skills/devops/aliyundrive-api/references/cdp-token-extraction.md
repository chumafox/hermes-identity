# Получение refresh_token через Brave CDP

Когда пользователь не может залогиниться в китайском UI alipan.com, используем CDP.

## Workflow

### 1. Запуск Brave с CDP
```bash
pkill -9 -f "Brave Browser"
sleep 2
open -a "Brave Browser" --args --remote-debugging-port=9222 \
  --load-extension=/tmp/kimi-webbridge-ext
# Ждать готовности
for i in 1 2 3 4 5 6; do sleep 2; curl -s http://localhost:9222/json/version >/dev/null 2>&1 && break; done
```

### 2. Навигация
`browser_navigate(url="https://www.alipan.com/drive/home")` — редиректит на OAuth.

### 3. Обход iframe
Страница логина — кросс-оригин iframe (auth.alipan.com).
```javascript
// Найти URL iframe
document.querySelector("iframe").src
// Открыть напрямую (обходит cross-origin)
browser_cdp(method="Page.navigate", params={'url': '<iframe_src>'})
```

### 4. Методы входа
- "扫码登录" — QR-код, сканировать приложением
- "账号登录" — телефон + SMS
- "桌面端已登录，点击头像可直接登录" — если сессия есть

### 5. Получение токена
После логина:
```javascript
JSON.parse(localStorage.getItem('token')).refresh_token
```

### 6. Проверка
```bash
curl -s -X POST 'https://api.aliyundrive.com/v2/account/token' \
  -H 'Content-Type: application/json' \
  -d '{"refresh_token":"<token>","grant_type":"refresh_token"}'
```

## Pitfalls
- access_token expires ~20 min — use refresh_token
- refresh_token меняется после каждого refresh — сохранять новый
- Iframe cross-origin — не доступен DOM, нужно навигироваться напрямую
- SPA: body.innerText может быть пустым до JS-рендера
- browser_vision 403 в Китае — использовать CDP evaluate
- Если Brave был без CDP: pkill -9, потом fresh start
