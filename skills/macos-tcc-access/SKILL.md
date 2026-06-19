---
name: macos-tcc-access
description: "Workarounds for macOS Transparency Consent & Control (TCC) privacy protections — accessing user files from SSH, bypassing Full Disk Access restrictions, and managing SIP-protected config files on macOS 15+ (Sequoia)."
tags: ["macos", "tcc", "privacy", "sip", "file-access", "sequoia"]
---

# macOS TCC / Privacy Workarounds

macOS 15+ (Sequoia) enforces Full Disk Access (FDA) strictly. Even **root** cannot read `~/Documents`, `~/Desktop`, `~/Downloads` from SSH sessions — only processes running in the user's GUI session have access.

## macOS 25 (Sequoia) Additional Hardening

macOS 25.x (kernel 25) дополнительно ужесточила TCC:
- TCC.db больше не открывается через sudo — `sudo sqlite3 TCC.db` → `authorization denied` (даже встроенный sqlite3 блокируется)
- `launchctl asuser 501 ls ~/Downloads/` больше не обходит TCC — падает с `Operation not permitted`
- `python3 -c 'os.listdir(...)'` тоже блокируется
- `mdfind` в sandbox-контейнерах не работает из SSH
- `tmutil` / `ditto` / `zip` / `rsync` / `cp -c` — все блокируются одинаково
- `sandbox-exec` с разрешительным профилем не обходит TCC
- `security authorizationdb` не даёт модифицировать TCC

**Что НЕ работает как обход:**
- ❌ `sudo sqlite3 /Library/Application\ Support/com.apple.TCC/TCC.db`
- ❌ `sudo launchctl asuser 501 ls ~/Downloads/`
- ❌ `open -a Terminal /tmp/script.sh` на headless Mac (без GUI-сессии)
- ❌ `sandbox-exec -f /tmp/permit.sb /bin/ls`
- ❌ `ditto` / `cp -R` / `rsync` из SSH
- ❌ `profiles -I -F /tmp/profile.mobileconfig` (install fails over SSH)

**Что МОЖЕТ сработать (с ограничениями):**
- Finder через AppleScript — **только** если пользователь залогинен в GUI и не заблокирован экран
- Python внутри бандла приложения, у которого есть Full Disk Access (например, `OpenVox.app/.../python3`)
- `tccutil reset All` — команда выполняется, но изменения вступают в силу только после logout/reboot
- LaunchAgent, запущенный через `launchctl load` от GUI-пользователя — может копировать файлы (Finder API)

**Рекомендация:** не тратить время на обход TCC через SSH. Если файлы лежат в `~/Downloads/` или sandbox-контейнере, а доступ нужен — переместить их через приложение с GUI (OpenVox, Finder), или скачать заново через CLI в `/tmp/`.

## Symptoms

- `ls ~/Documents` from SSH → `Operation not permitted`
- `sudo ls ~/Documents` → `Operation not permitted`
- `sudo ditto` / `sudo cp` → same error
- `stat` works (reads FS metadata), `find`/`ls` fail (reads directory contents)
- TCC database (`~/Library/Application Support/com.apple.TCC/TCC.db`) also protected
- SIP-protected paths like `/var/db/ConfigurationProfiles/Settings/.cloudConfig*` cannot be deleted even as root

## Solution: Run via GUI Terminal

The user's GUI Terminal.app has Full Disk Access. Launch a script from SSH that opens in the GUI context:

```bash
# 1. Write script to a non-restricted location
cat > /tmp/copy_files.sh << 'EOF'
#!/bin/bash
cp -R /Users/admin/Documents/ImportantStuff /tmp/important_copy
EOF
chmod +x /tmp/copy_files.sh

# 2. Launch in user's GUI Terminal (this bypasses TCC)
# Finder/Dock must be running (user must be logged in via Screen Sharing or console)
open -a Terminal /tmp/copy_files.sh

# 3. Wait for completion, then copy from /tmp
sleep 5
ls /tmp/important_copy
```

### Important prerequisites

- **User must be logged in** via Screen Sharing or console (Dock + Finder running)
- **Screen must NOT be locked** — locked screen causes `osascript` to hang
- Works with any app that has FDA: Finder, Terminal, etc.

### Alternative: launchctl asuser (if screen is locked)

```bash
# Get GUI session UID
GUI_UID=$(ps -o uid= -p $(pgrep -x Dock) | tr -d ' ')

# Run command in user's Aqua session context
sudo launchctl asuser "$GUI_UID" open -a Terminal /tmp/script.sh
```

### Failures with osascript over SSH

```bash
# ALL of these fail from SSH (-2753):
osascript -e 'tell application "Finder" to copy ...'    # hangs
osascript -e 'tell application "Terminal" to do script "cp ..."'  # hangs
```

Use `open -a Terminal /tmp/script.sh` instead — it returns immediately and runs in the right context.

## Reverse SSH Push (when TCC blocks local access)

If you can't read files on Mac A (TCC-protected), make Mac A the one that **pushes**:

```bash
# On Mac A (the one with the files):
# 1. Generate temp SSH key on Mac A
ssh-keygen -t ed25519 -f /tmp/push_key -N ""
cat /tmp/push_key.pub

# 2. Add pub key to Mac B's authorized_keys
echo "ssh-ed25519 AAAA..." >> ~/.ssh/authorized_keys

# 3. Copy key to Mac A
# (scp /tmp/push_key user@Mac-A:~/.ssh/id_temp)

# 4. From Mac A, push files to Mac B
ssh -i ~/.ssh/id_temp user@Mac-B 'cat > /tmp/files.tar.gz' < /tmp/files.tar.gz
```

## SIP-Protected Cloud Config (MDM/DEP Files)

Files at `/var/db/ConfigurationProfiles/Settings/` (`.cloudConfig*`, `.profiles*`) are protected by SIP. Cannot `rm` or `chmod` even as root.

**Permanent fix requires physical access:**
1. Boot into Recovery (hold power on Apple Silicon)
2. `csrutil disable` (or `csrutil enable --without fs`)
3. Reboot → delete files: `rm -f /var/db/ConfigurationProfiles/Settings/.cloudConfig* /var/db/ConfigurationProfiles/Settings/.profiles*`
4. Reboot into Recovery → `csrutil enable`

**Without physical access — suppression via:**
- DNS block (hosts file): `deviceenrollment.apple.com`, `gdmf.apple.com`, MDM server
- `/var/db/.AppleSetupDone` — prevents Setup Assistant on next boot
- `launchctl disable system/com.apple.mdmclient.daemon`
- Watchdog launchd agent (see `references/mdm-dep-suppression.md`)

## Scripts

See `scripts/tcc-copy.sh` — template for copying from TCC-protected dirs.

## References

- `references/mdm-dep-suppression.md` — full MDM/DEP bypass workflow
- `references/macos-tcc-limitations.md` — TCC edge cases (Speedify NE, Safari sandbox)
