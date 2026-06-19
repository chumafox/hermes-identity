# macOS TCC Hardening (macOS 15+ and 25+)

macOS 15+ (Sequoia) and 25+ enforce Full Disk Access (FDA) strictly. Even **root** cannot read `~/Documents`, `~/Desktop`, `~/Downloads` from SSH sessions.

## macOS 25 Additional Hardening

macOS 25.x (kernel 25) further tightened TCC:
- TCC.db no longer opens via sudo: `sudo sqlite3 TCC.db` → `authorization denied`
- `launchctl asuser 501 ls ~/Downloads/` no longer bypasses TCC
- `python3 -c 'os.listdir(...)'` blocked
- `sandbox-exec` with permissive profile does not bypass TCC

**What does NOT work as bypass:**
- ❌ `sudo sqlite3 /Library/Application Support/com.apple.TCC/TCC.db`
- ❌ `sudo launchctl asuser 501 ls ~/Downloads/`
- ❌ `open -a Terminal /tmp/script.sh` on headless Mac (no GUI session)
- ❌ `sandbox-exec -f /tmp/permit.sb /bin/ls`
- ❌ `ditto` / `cp -R` / `rsync` from SSH

**What MAY work:**
- ✅ Finder via AppleScript — only if user logged into GUI and screen unlocked
- ✅ LaunchAgent loaded via `launchctl load` from GUI user context
- ✅ Python inside an app bundle with FDA (e.g., OpenVox.app/.../python3)
- ✅ `tccutil reset All` — takes effect after logout/reboot

## Solutions

### Run via GUI Terminal.app

```bash
cat > /tmp/copy_files.sh << 'EOF'
#!/bin/bash
cp -R /Users/admin/Documents/ImportantStuff /tmp/important_copy
EOF
chmod +x /tmp/copy_files.sh

# Launch in user's GUI Terminal (bypasses TCC)
# Prerequisites: user logged in, screen NOT locked
open -a Terminal /tmp/copy_files.sh

# Wait, then copy from /tmp
sleep 5
scp -r user@remote:/tmp/important_copy /local/path/
```

### Reverse SSH Push (when TCC blocks local access)

If you can't read files on Mac A due to TCC, make Mac A **push** to Mac B:

```bash
# On Mac A (has files):
ssh-keygen -t ed25519 -f /tmp/push_key -N ""
cat /tmp/push_key.pub  # → give this to Mac B

# On Mac B:
echo "ssh-ed25519 AAAA..." >> ~/.ssh/authorized_keys

# On Mac A — copy temp key, then push files:
scp /tmp/push_key user@remote:~/.ssh/id_temp
ssh -i ~/.ssh/id_temp user@remote 'cat > /tmp/files.tar.gz' < /tmp/files.tar.gz

# Cleanup
rm /tmp/push_key*
ssh user@remote 'rm ~/.ssh/id_temp'
```

This works because the SSH client running on Mac A's user session inherits TCC grants from the user context, even though the SSH server doesn't.

### Finder via AppleScript

```bash
ssh user@remote 'osascript -e "tell application \"Finder\" to copy folder POSIX file \"/Users/user/Documents/SOURCE\" to folder POSIX file \"/tmp\""'
```

## SIP-Protected Cloud Config (MDM/DEP)

Files at `/var/db/ConfigurationProfiles/Settings/` (`.cloudConfig*`) are SIP-protected. Cannot delete even as root via SSH.

**Permanent fix requires Recovery Mode:**
1. Boot into Recovery (hold power on Apple Silicon)
2. `csrutil disable`
3. Reboot → `rm -f /var/db/ConfigurationProfiles/Settings/.cloudConfig*`
4. Reboot into Recovery → `csrutil enable`

**Without physical access — suppress via:**
- DNS blocks: `deviceenrollment.apple.com`, `gdmf.apple.com` in /etc/hosts
- `touch /var/db/.AppleSetupDone`
- `launchctl disable system/com.apple.mdmclient.daemon`
- Watchdog launchd agent (see macos-mdm-bypass skill)
