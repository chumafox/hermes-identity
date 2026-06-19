# MDM/DEP Enrollment Bypass (macOS)

## Problem

A Mac has a persistent DEP enrollment record pointing to an MDM server (e.g. Walmart/Jamf Cloud). On boot, macOS launches Setup Assistant with `-ForceMDMEnroll` and shows an enrollment window with only an "Enroll" button — no skip/decline option.

## Why DNS blocking alone isn't enough

Even with all Apple and Jamf servers blocked in `/etc/hosts`, the enrollment **still triggers locally**:

```
/var/db/ConfigurationProfiles/Settings/
├── .cloudConfigHasActivationRecord    ← SIP-protected flag
├── .cloudConfigRecordFound            ← DEP enrollment data
├── .cloudConfigTimerCheck             ← retry timer
└── .profilesDEPTimerCheck             ← DEP check timer
```

These files are **SIP-protected** (cannot be removed even as root). macOS reads them and says: "This Mac has DEP, proceed with enrollment." The enrollment attempt will fail (DNS blocked), but macOS keeps retrying forever.

The enrollment process runs through a separate mechanism from `launchctl`:
```
mbsystemadministration (root)
mbuseragent (admin)
mbusertrampoline (root)
Setup Assistant -MiniBuddyYes -ForceMDMEnroll (admin)
```

## Mitigation (no physical access)

### 1. DNS block (in /etc/hosts)
Block ALL known Apple DEP/MDM + the specific MDM server:
```
0.0.0.0 deviceenrollment.apple.com
0.0.0.0 gdmf.apple.com
0.0.0.0 mdmenrollment.apple.com
0.0.0.0 iprofiles.apple.com
0.0.0.0 iprofiles.mac.com
0.0.0.0 walmart.jamfcloud.com
0.0.0.0 jamfcloud.com
0.0.0.0 deviceservices.apple.com
```

### 2. .AppleSetupDone (prevents Setup Assistant on next boot)
```bash
sudo touch /var/db/.AppleSetupDone
```

### 3. Disable mdmclient launchd daemon
```bash
sudo launchctl disable system/com.apple.mdmclient.daemon
sudo launchctl disable system/com.apple.mdmclient.daemon.runatboot
```

### 4. Kill active processes
```bash
sudo pkill -9 -f "mdmclient"
sudo pkill -9 -f "Setup Assistant"
```

### 5. Watchdog launchd agent (kills enrollment every 30 seconds)
Create `~/Library/LaunchAgents/com.user.kill-mdm.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.kill-mdm</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>pkill -9 -f "mdmclient"; pkill -9 -f "Setup Assistant"</string>
    </array>
    <key>StartInterval</key>
    <integer>30</integer>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/dev/null</string>
    <key>StandardErrorPath</key>
    <string>/dev/null</string>
</dict>
</plist>
```

Load it:
```bash
launchctl load ~/Library/LaunchAgents/com.user.kill-mdm.plist
```

**Resource impact of watchdog:** Negligible — `pkill` is a few ms of CPU per run. Filesystem/disk: zero. Even at 5-second intervals the load is invisible.

## Permanent fix (requires physical access)

The cloud config files are SIP-protected. To remove them:

### Step 1: Boot into Recovery and disable SIP (filesystem only)
1. Shut down Mac
2. Press and hold **power button** (Apple Silicon) until "Loading startup options..."
3. Click Options → Continue → admin user → password
4. Utilities → Terminal → `csrutil enable --without fs` (disable only filesystem protection)
5. Restart

### Step 2: Remove cloud config files
```bash
sudo rm /var/db/ConfigurationProfiles/Settings/.cloudConfig*
sudo rm /var/db/ConfigurationProfiles/Settings/.profiles*
```

Verify: `ls -la /var/db/ConfigurationProfiles/Settings/ | grep .cloud` — should be empty.

### Step 3: Re-enable SIP
1. Reboot into Recovery again (same method)
2. Terminal → `csrutil enable`
3. Restart

### Step 4: Verify
```bash
profiles status -type enrollment
# → Enrolled via DEP: No, MDM enrollment: No

sudo profiles show -type enrollment
# → No DEP configuration (or empty)
```

## Cleanup after fix

After successful bypass, remove the watchdog:
```bash
launchctl unload ~/Library/LaunchAgents/com.user.kill-mdm.plist
rm ~/Library/LaunchAgents/com.user.kill-mdm.plist
```

The DNS blocks in /etc/hosts are harmless to keep.
