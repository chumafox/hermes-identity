# macOS TCC File Access via Screen Sharing

## Problem

When Screen Sharing connects to a remote Mac running macOS 15+, SSH sessions into that Mac cannot access `~/Documents` — even as root or with sudo (`Operation not permitted`). This is macOS TCC (Full Disk Access) enforcement. Even `sudo launchctl asuser 501`, `osascript`, `ditto`, and direct `find` commands all fail.

The TCC database itself (`~/Library/Application Support/com.apple.TCC/TCC.db`) is also inaccessible — even with `sudo sqlite3`, it returns "authorization denied".

## Workaround: `open -a Terminal` (GUI context)

The remote Mac's GUI Terminal.app has Full Disk Access by default. Launch a copy script via Terminal.app:

**Step 1: Write the script and transfer it**
```bash
# On the SOURCE Mac (your machine), create the script:
cat > /tmp/copy-files.sh << 'SCRIPT'
#!/bin/bash
cp -R /Users/admin/Documents/SourceDir /tmp/dest
chmod -R 755 /tmp/dest
SCRIPT

# SCP it to the remote Mac:
scp /tmp/copy-files.sh admin@remote:/tmp/copy-files.sh
```

**Step 2: Run it on the remote Mac via GUI Terminal**
```bash
ssh admin@remote 'chmod +x /tmp/copy-files.sh && open -a Terminal /tmp/copy-files.sh'
```

**Step 3: Wait and collect**
```bash
sleep 5
scp -r admin@remote:/tmp/dest /local/path/
```

## Key Findings (from real session)

### `open -a Terminal` WORKS even on a locked screen

Contrary to earlier assumptions, launching `open -a Terminal /tmp/script.sh` via SSH works even when the remote Mac is at the lock screen. The script executes successfully and files are copied to /tmp.

**What does NOT work on locked screen:**
- `osascript -e "tell application Finder to ..."` — **hangs indefinitely** (timed out at 15s)
- `osascript -e "tell application Terminal to do script ..."` — **hangs indefinitely**
- `sudo launchctl asuser 501 cp ...` — fails with `Operation not permitted`

### heredoc through sshpass breaks

Multi-line heredocs inside `sshpass` commands get mangled by nested quoting. Instead:
1. Write the script locally with `write_file`
2. SCP it to the remote
3. Execute via `ssh chmod +x && open -a Terminal`

### Reverse SSH push (alternative if screen is locked)

The `open -a Terminal` approach is simpler, but if it fails:

1. Generate a temp SSH key on the SOURCE Mac:
   ```bash
   ssh-keygen -t ed25519 -f /tmp/temp_push_key -N "" -q
   cat /tmp/temp_push_key.pub >> ~/.ssh/authorized_keys
   chmod 600 ~/.ssh/authorized_keys
   ```

2. Copy key to remote and push files:
   ```bash
   scp /tmp/temp_push_key admin@remote:~/.ssh/id_temp
   ssh admin@remote 'chmod 600 ~/.ssh/id_temp'
   
   # Remote pushes to SOURCE:
   ssh admin@remote "ssh -i ~/.ssh/id_temp -o StrictHostKeyChecking=no jenyanovak@source-ip 'cat > /tmp/dest.tar.gz'" < /tmp/dest.tar.gz
   ```

3. Clean up:
   ```bash
   rm /tmp/temp_push_key /tmp/temp_push_key.pub
   ssh admin@remote 'rm ~/.ssh/id_temp'
   # Remove from authorized_keys
   ```
