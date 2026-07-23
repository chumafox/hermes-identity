# Memory Backup
Generated: 2026-07-23 (cron identity sync)

Дамп из `~/.hermes/memories/MEMORY.md` и `USER.md` (memory tool недоступен в cron).

---

## MEMORY.md — заметки агента

- **Doubao (CDP 9223):** ASR EN+ZH only. Инжект: BlackHole+ffmpeg audiotoolbox. Скрипты: ~/bin/{audiodev,doubao-inject}. NO_PROXY="*" при WS. Bridge: ~/projects/active/doubao-chat-bridge/ (run.sh).

- **Brave (CDP 9222) и Doubao (CDP 9223)** на macOS. NO_PROXY="*" при WS/CDP на localhost (websockets ломится через HTTP_PROXY). hostname Mac: dispo.

- **Apple-решения:** prefers нативные (SFSpeechRecognizer, Shortcuts, Automator) над сторонними. Рутины → скрипты. После 5+ вызовов — skill.

- **iOS-разработка** (vibecoding). На безголовом Mac Xcode 16.2.

- **Голосовой ввод:** VoiceNote.app (F5) + Handy (Option+Space, Canary 1B). TTS: Silero v4 xenia + ffmpeg pitch 0.85.

- **PEP 668:** --break-system-packages. HF: hfd.sh+aria2c. AliyunDrive: alipan CLI

- **Gym:** ~/shelf/gym/. ШРЕДЕР 5 дн. Вес 85, белок 187г/д (2.2г/кг). Псиллиум Now Foods. Овсяная мука в шейк.

- **rude (ru-de-translator):** CTranslate2 модель в ~/.config/ru_de_translator/opus-zle-de-ct2/. Audio tcp/24000 для Doubao. Edge TTS прямой.

- **DEEPSEEK_API_KEY=ark (Volc).** Aux title_generation 404: deepseek-fallback или отключить (provider:''). ModelNotOpen → Console activate.

- **M1 Wi-Fi (BCM4378):** sudo ifconfig en0 down ломает драйвер на уровне IOKit, bpfAttach failed (17), только ребут. Никогда не использовать ifconfig en0 down.

- **Apple Notes (macOS 14+):** ZTITLE=empty, ZDATA=gzip protobuf. Читать только AppleScript чанками по 300.

- **Gym diary:** ~/Projects/active/gym-diary/, React+Vite+Tailwind4, localhost:5173. split-default routes utun9 ломают браузеры.

- **Сеть:** dispo (USB en5), pro (192.168.103.70). en0 BCM4378 — ifconfig down НЕЛЬЗЯ. Timezone: America/Chicago. Прокси US: 169.150.224.227 (Texas, Datacamp). Ship: sing-box utun9 + mixed-in 1083 (HTTP+SOCKS5). Hysteria2: dispo Shadowrocket → pro UDP 8889. net-loc {ship|normal} ~/bin/net-loc.

- **CLI:** claude, opencode, cursor, agy, antigravity. ~/cli-common/. agy: Anthropic OK, Gemini FAILED_PRECONDITION 400. CLOUD_CODE_URL=cloudcode-pa.googleapis.com. proxy_on → HTTP 127.0.0.1:1083. Нужен US-аккаунт для авторизации.

- **here.now (skill):** Бесплатный хостинг для статики агентами. Без ключа 24ч, с ключом навсегда. publish.sh + drive.sh.

---

## USER.md — профиль пользователя

- **Doubao bridge (CDP 9223):** RU→EN→TTS(say)→BlackHole→Doubao→CDP→ZH→RU. Option+T=mute. Handy dictation (Option+Space, canary-1b-v2). Web UI: input always active, Enter=form submit. Doubao floating window right → UI max-width 550px left.

- **Doubao voice inject (CDP 9223, BlackHole 2ch, ffmpeg audiotoolbox).** ASR EN+ZH only. Chain: RU→EN→TTS(say)→BlackHole→Doubao→CDP→ZH→RU. Option+T=mute mic.

- **Pro (admin):** Shadowrocket TUN (utun4, port 1082), SOCKS5 не работает — прямой доступ через TUN норм. PEP 668: pip install --break-system-packages. git proxy trap: проверять глобальный (~/.gitconfig) И локальный (.git/config).

- **Gym:** ~/shelf/gym/. ШРЕДЕР 5дн, золотой подход. 186см/85кг, цель сброс 6кг+сила. Белок 187г/д. Псиллиум+овсяная мука. Приседания Смит 50/8, выпады 17/12.

- **Google:** vdubay@gmail.com — регион USA. dev: jenyanovakpro@gmail.com. Cloudflare: zone jenya.cfd, DNS токен cfut_1nRCS..., acc 9600e1be8c21bb. Porkbun API есть.

- **Browser:** Arc (default). Brave on CDP 9222 for automation only.

- **Веб-приложения:** React+Vite+Tailwind 4, тёмная тема, localStorage, без бэкенда. Чисто локальные персональные тулы.
