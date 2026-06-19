# Orphaned NetworkExtensions: Persist After App Deletion

## Проблема

На macOS NetworkExtension (NE) остаются активными даже после удаления приложения.
`systemextensionsctl list` показывает `[activated enabled]` — расширение перехватывает
трафик на уровне ядра, хотя само приложение удалено.

## Симптомы

- `arp -an` показывает хост (есть MAC), но **все порты таймаутятся** (не refused!)
- `ping`, `ssh`, `nc` — всё timeout
- `systemextensionsctl list` показывает NE с `*` в обеих колонках (enabled + active)
- Приложение не найдено: `ls /Applications/ | grep -i appname` → пусто
- Процесс не запущен: `pgrep -fl name` → пусто

## Как проверить

```bash
# 1. Список всех активных NetworkExtension
systemextensionsctl list

# Ищи строки с [activated enabled] (обе звёздочки):
#   *  *  TEAMID  bundleID (version)  Name  [activated enabled]

# 2. Проверить есть ли приложение
ls /Applications/ | grep -iE "speedify|little.snitch|shadowrocket"

# 3. Проверить процессы
pgrep -fl "speedify|snitch|shadowrocket"
```

## Самые частые виновники

| Расширение | bundleID | Что блокирует |
|------------|----------|---------------|
| Speedify PacketTunnel | com.connectify.Speedify.PacketTunnelSysExt | ВСЁ — перехватывает NSURLSession, Safari, urllib. Даже без запущенного приложения. |
| Little Snitch | at.obdev.littlesnitch.networkextension | Входящие/исходящие по кешированным правилам. |
| Tailscale | io.tailscale.ipn.macsys.network-extension | Не блокирует если не подключён. |

## Почему это происходит

macOS кеширует SystemExtension в `/Library/SystemExtensions/<UUID>/`.
При удалении приложения расширение **не деактивируется автоматически** —
остаётся в памяти до перезагрузки.

Даже после перезагрузки NE может остаться, если приложение было перемещено
в Корзину, а не удалено навсегда.

## Реальный кейс (с этого корабля, июнь 2026)

На display Mac `systemextensionsctl list` показал:
```
*  *  MLZF7K7B5R  at.obdev.littlesnitch.networkextension  Little Snitch     [activated enabled]
*  *  42L9495X72  com.connectify.Speedify.PacketTunnelSysExt  Speedify     [activated enabled]
```

Но пользователь утверждал: **"Little Snitch и Speedify — этого нет, нигде не установлено"**.

Проверка подтвердила:
- `ls /Applications/ | grep -iE "snitch|speedify"` → пусто
- `pgrep -fl "snitch|speedify"` → пусто
- `which speedify` → не найден

Расширения остались от давно удалённых приложений и перехватывали весь входящий трафик
на уровне ядра. Результат: безголовый Mac в той же WiFi подсети пингуется (ARP есть),
но все порты таймаутятся — SSH, VNC, ping.

На headless Mac Speedify NE был в статусе `[terminated waiting to uninstall on reboot]` —
удалён через GUI, но не перезагружен.

Удалять через: **System Settings → General → Login Items & Extensions → Network Extensions** → `-` (минус).
После удаления — **обязательно перезагрузить**.

## Как удалить

### Способ 1: GUI (рекомендуется, работает на M1 с SIP)

**System Settings → General → Login Items & Extensions → Network Extensions**

Там отображаются все установленные NE. Нажать на расширение → `-` (минус) удалить.

### Способ 2: Удалить приложение + перезагрузка

```bash
# 1. Полностью удалить приложение (не просто в корзину)
sudo rm -rf /Applications/Speedify.app 2>/dev/null
sudo rm -rf ~/Applications/Speedify.app 2>/dev/null

# 2. Перезагрузить
sudo shutdown -r now "removing NE"
```

После перезагрузки NE исчезает из `systemextensionsctl list`.

### Способ 3: systemextensionsctl uninstall (НЕ работает на M1 с SIP)

```bash
# НЕ РАБОТАЕТ на M1 с SIP:
# sudo systemextensionsctl uninstall TEAMID bundleID
# → "This tool cannot be used if System Integrity Protection is enabled"
```

## Что делать, если GUI недоступен (headless Mac)

На headless Mac без монитора:
1. Зайти по Screen Sharing или физически
2. Открыть System Settings → General → Login Items & Extensions → Network Extensions
3. Удалить NE через `-` (минус)
4. Перезагрузить

Если Screen Sharing тоже не работает (NE блокирует) — физический доступ.
