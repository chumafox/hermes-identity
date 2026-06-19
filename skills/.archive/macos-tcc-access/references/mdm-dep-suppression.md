# MDM/DEP Enrollment Suppression

## Context

Mac was originally owned by **Walmart** (Walmart Jamf Cloud). DEP enrollment is mandatory (`IsMandatory=1`). The Mac has an admin user and SSH access but the enrollment happens at the system level.

## Key Files (SIP-Protected)

```
/var/db/ConfigurationProfiles/Settings/.cloudConfigHasActivationRecord
/var db/ConfigurationProfiles/Settings/.cloudConfigRecordFound
/var/db/ConfigurationProfiles/Settings/.cloudConfigTimerCheck
/var/db/ConfigurationProfiles/Settings/.profilesDEPTimerCheck
```

These trigger Setup Assistant with `-ForceMDMEnroll` even when network blocks are in place.

## Suppression Without Physical Access

### 1. DNS Block (immediate effect)

```bash
sudo tee -a /etc/hosts << 'EOF'
0.0.0.0 deviceenrollment.apple.com
0.0.0.0 gdmf.apple.com
0.0.0.0 mdmenrollment.apple.com
0.0.0 robots.apple.com
0.0.0.0 iprofiles.apple.com
0.0.0.0 iprofiles.mac.com
0.0.0.0 walmart.jamfcloud.com
0.0.0.0 jamfcloud.com
0.0.0.0 deviceservices.apple.com
EOF
dscacheutil -flushcache
sudo killall -HUP mDNSResponder
```

### 2. Block Setup Assistant on Next Boot

```bash
sudo touch /var/db/.AppleSetupDone
```

### 3. Disable mdmclient Daemon

```bash
sudo launchctl disable system/com.apple.mdmclient.daemon
sudo launchctl disable system/com.apple.mdmclient.daemon.runatboot
```

### 4. Watchdog Launchd Agent (kills processes every 5s)

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
    <integer>5</integer>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/dev/null</string>
    <key>StandardErrorPath</key>
    <string>/dev/null</string>
</dict>
</plist>
```

```bash
launchctl load ~/Library/LaunchAgents/com.user.kill-mdm.plist
```

## Permanent Fix (Physical Access Required)

1. Shut down → hold power button → Options → Recovery
2. Terminal → `csrutil disable` → Restart
3. `rm -f /var/db/ConfigurationProfiles/Settings/.cloudConfig*`
4. `rm -f /var/db/ConfigurationProfiles/Settings/.profiles*`
5. Restart → Recovery → `csrutil enable`

## Verification

```bash
profiles status -type enrollment
# Expected: Enrolled via DEP: No, MDM enrollment: No
```
