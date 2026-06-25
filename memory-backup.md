# Memory Backup
Generated: 2026-06-26 (cron identity sync)

## Durable Facts (from built-in memory store)

### Doubao & Voice
- Doubao (CDP 9223): ASR EN+ZH only. Inject: BlackHole+ffmpeg audiotoolbox
- Scripts: ~/bin/{audiodev,doubao-inject}. NO_PROXY="*" при WS
- Bridge: ~/projects/active/doubao-chat-bridge/ (run.sh)
- Doubao bridge chain: RU→EN→TTS(say)→BlackHole→Doubao→CDP→ZH→RU
- Option+T = mute Doubao mic
- Handy dictation (Option+Space, canary-1b-v2)
- TTS: Silero v4 xenia + ffmpeg pitch 0.85 (robot voice)

### Browser & Networking
- Brave (CDP 9222) and Doubao (CDP 9223) on macOS
- NO_PROXY="*" при WS/CDP на localhost
- Hostname Mac: dispo (HK), pro (China/utun4)
- Ship WiFi + pro Mac (192.168.103.70)
- proxy_toggle: ~/bin/proxy_toggle
- Pro (admin): Shadowrocket TUN (utun4, port 1082), SOCKS5 не работает
- git proxy trap: проверять глобальный (~/.gitconfig) И локальный (.git/config)

### Development
- iOS vibecoding, Xcode 16.2 на безголовом Mac
- CLI: claude, opencode, cursor-agent, agy
- ~/cli-common/ единый source (agents+MCP), deploy.sh → symlink
- MCP: dataforseo, z.ai, tavily, firecrawl, pencil, goofish
- Convert-skills.py: skills/<name>/skill.yaml → agents/*.md + hermes SKILL.md
- Volcengine Coding Plan Lite (до 14.07): custom:volc-coding
- Models: deepseek-v4-flash/pro, doubao-seed-2.0-code/pro/lite, minimax-m3/m2.7, glm-5.1, kimi-k2.6
- oMLX: ~/omlx/, OpenAI API localhost:8000/v1
- Local models: VibeThinker-1.5B-mlx-4bit, Bonsai-8B-mlx-1bit в ~/models/

### Hermes Desktop
- Hermes One.app v0.6.2 (fatrah/hermes-desktop)
- Updater patched — retry 3× на check + перепроверка перед download
- Лаунчер ~/bin/hermes-desktop с ELECTRON_HTTP_PROXY
- App переподписан ad-hoc

### System & Tools
- PEP 668: --break-system-packages
- HF: hfd.sh+aria2c
- AliyunDrive: ~/bin/alipan CLI (токен ~/.config/alipan-token.json)
- aliyundrive-webdav 2.3.3 несовместим
- Mail.app 16.0, iCloud (chumafox@me.com), управление через osascript

### Fitness
- Gym: ~/shelf/gym/. ШРЕДЕР 5 дн
- Вес 85, белок 187г/д (2.2г/кг)
- Псиллиум Now Foods. Овсяная мука в шейк
- 186см/85кг. Цель: сброс 6кг + сила
- Сплит 5дн (ПН грудь/ВТ спина/СР ноги/ЧТ плечи/ПТ руки)
- Приседания Смит 50/8, выпады формат вес/шаги (17/12), икры 4×10 (60кг)

### User Profile
- Jenya, Chongqing, Китай
- Russian/brief. Terminal-only
- M1 Air 8GB
- "Стой" = стоп
- Два Mac: dispo (HK) + pro (Китай/utun4)
- Prefers нативные Apple-решения над сторонними
- Prefers shared config across CLI agents — no duplicates
- Python: /opt/homebrew/bin/python3
