# Memory Backup
Generated: 2026-07-20 (cron identity sync)

## Статус

Memory tool недоступен в этом окружении (вероятно, отключён для cron задач).
Предыдущий бэкап от 2026-07-19 сохранён в git history.

## История предыдущих фактов (из git history)

### Doubao & Voice
- Doubao (CDP 9223): ASR EN+ZH only. Inject: BlackHole+ffmpeg audiotoolbox
- Scripts: ~/bin/{audiodev,doubao-inject}. NO_PROXY="*" при WS
- Bridge: ~/projects/active/doubao-chat-bridge/ (run.sh)
- Doubao bridge chain: RU→EN→TTS(say)→BlackHole→Doubao→CDP→ZH→RU
- Option+T = mute Doubao mic
- Handy dictation (Option+Space, canary-1b-v2)
- TTS: Silero v4 xenia + ffmpeg pitch 0.85

### Browser & Networking
- Brave (CDP 9222) and Doubao (CDP 9223) on macOS
- NO_PROXY="*" при WS/CDP на localhost (websockets ломится через HTTP_PROXY)
- Hostname Mac: dispo (HK), pro (China/utun4)
- Ship WiFi + pro Mac (192.168.103.70)
- Pro (admin): Shadowrocket TUN (utun4, port 1082), SOCKS5 не работает
- git proxy trap: проверять глобальный (~/.gitconfig) И локальный (.git/config)
- en0 BCM4378 — ifconfig down НЕЛЬЗЯ (ломает драйвер, только ребут)
- Timezone: America/Chicago. Прокси US: 169.150.224.227 (Texas, Datacamp)
- Ship: sing-box utun9 + mixed-in 1083 (HTTP+SOCKS5)
- Hysteria2: dispo Shadowrocket → pro UDP 8889
- net-loc {ship|normal} ~/bin/net-loc
- Сеть: dispo (USB en5), pro (192.168.103.70)

### Development
- iOS vibecoding, Xcode 16.2 на безголовом Mac
- CLI: claude, opencode, cursor, agy, antigravity
- ~/cli-common/ единый source (agents+MCP), deploy.sh → symlink
- agy: Anthropic OK, Gemini FAILED_PRECONDITION 400. CLOUD_CODE_URL=cloudcode-pa.googleapis.com
- proxy_on → HTTP 127.0.0.1:1083. Нужен US-аккаунт для авторизации
- Веб-приложения: React+Vite+Tailwind 4, тёмная тема, localStorage, без бэкенда
- Local models: VibeThinker-1.5B-mlx-4bit, Bonsai-8B-mlx-1bit в ~/models/
- oMLX: ~/omlx/, OpenAI API localhost:8000/v1

### System & Tools
- PEP 668: --break-system-packages
- HF: hfd.sh+aria2c
- AliyunDrive: ~/bin/alipan CLI (токен ~/.config/alipan-token.json)
- aliyundrive-webdav 2.3.3 несовместим
- rude (ru-de-translator): CTranslate2 в ~/.config/ru_de_translator/opus-zle-de-ct2/
- Audio tcp/24000 для Doubao. Edge TTS прямой
- Apple Notes (macOS 14+): ZTITLE=empty, ZDATA=gzip protobuf. Читать AppleScript чанками по 300
- Gym diary: ~/Projects/active/gym-diary/, React+Vite+Tailwind4, localhost:5173
- DEEPSEEK_API_KEY=ark (Volc). Aux title_generation: deepseek-fallback или provider:''

### Fitness
- Gym: ~/shelf/gym/. ШРЕДЕР 5 дн
- Вес 85, белок 187г/д (2.2г/кг)
- Псиллиум Now Foods. Овсяная мука в шейк
- 186см/85кг. Цель: сброс 6кг + сила
- Сплит 5дн (ПН грудь/ВТ спина/СР ноги/ЧТ плечи/ПТ руки)
- Приседания Смит 50/8, выпады 17/12, икры 4×10 (60кг)

### Google & Cloudflare
- Google vdubay@gmail.com — регион USA
- Google jenyanovakpro@gmail.com — dev
- Cloudflare: zone jenya.cfd, DNS токен cfut_1nRCS..., acc 9600e1be8c21bb
- Porkbun API есть

### User Profile
- Jenya, Chongqing, Китай
- Russian/brief. Terminal-only
- M1 Air 8GB
- "Стой" = стоп
- Два Mac: dispo (HK) + pro (Китай/utun4)
- Prefers нативные Apple-решения над сторонними
- Prefers shared config across CLI agents — no duplicates
- Python: /opt/homebrew/bin/python3
- Browser: Arc (default). Brave on CDP 9222 for automation only
