# Установка .app через SOCKS5 прокси (Китай)

Когда Homebrew и прямые загрузки не работают из-за GFW.

## Шаги

```bash
# 1. Скачать DMG через SOCKS5
curl -L --socks5 127.0.0.1:1080 --max-time 300 \
  -o /tmp/App.dmg \
  "https://github.com/owner/repo/releases/download/v1.0/App_aarch64.dmg"

# 2. Примонтировать
hdiutil attach /tmp/App.dmg -nobrowse

# 3. Установить
cp -R /Volumes/App/App.app /Applications/

# 4. Снять quarantine (если блокирует)
xattr -d com.apple.quarantine /Applications/App.app 2>/dev/null

# 5. Запустить
open /Applications/App.app

# 6. Очистить
hdiutil detach /Volumes/App
rm /tmp/App.dmg
```

## Питфоллы

- **Homebrew не работает:** `brew tap` клонирует через git и виснет. `brew install` без прокси не работает. Всегда качать релиз напрямую через curl + SOCKS5.
- **Homebrew авто-апдейт:** ставить `HOMEBREW_NO_AUTO_UPDATE=1` перед любым brew.
- **Архитектура:** M1 = `aarch64`/`arm64`. Intel = `x64`/`amd64`.
- **Размер:** DMG могут быть 150-300 MB. Ставить `--max-time` с запасом.
- **SOCKS5 порт:** Проверить что inpro включён (порт 1080 слушает) перед curl.
