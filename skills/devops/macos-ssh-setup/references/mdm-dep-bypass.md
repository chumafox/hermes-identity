# MDM/DEP Enrollment Bypass (macOS)

## Background

Some second-hand Macs come with MDM/DEP enrollment pointing to a corporate MDM server (Jamf, etc.). The device checks with Apple's DEP servers on boot, gets the MDM server URL, and forces enrollment.

On macOS 15+, the `.cloudConfig*` files in `/var/db/ConfigurationProfiles/Settings/` are SIP-protected and cannot be removed even as root.

## DNS-Level Blocking

Add these to `/etc/hosts` to prevent the Mac from contacting Apple's DEP servers and the corporate MDM:

```bash
echo "0.0.0.0 deviceenrollment.apple.com" | sudo tee -a /etc/hosts
echo "0.0.0.0 mdmenrollment.apple.com" | sudo tee -a /etc/hosts
echo "0.0.0.0 iprofiles.apple.com" | sudo tee -a /etc/hosts
echo "0.0.0.0 gdmf.apple.com" | sudo tee -a /etc/hosts
echo "0.0.0.0 iprofiles.mac.com" | sudo tee -a /etc/hosts
echo "0.0.0.0 deviceservices.apple.com" | sudo tee -a /etc/hosts
echo "0.0.0.0 walmart.jamfcloud.com" | sudo tee -a /etc/hosts  # replace with your MDM
```

**Note:** DNS blocking prevents enrollment from completing successfully, but macOS still TRIGGERS enrollment locally because the `.cloudConfig*` files exist. The processes (mdmclient, Setup Assistant) will keep respawning.

## Kill Running Processes

```bash
sudo pkill -9 -f "mdmclient"
sudo pkill -9 -f "Setup Assistant"
sudo launchctl disable system/com.apple.mdmclient.daemon
sudo launchctl disable system/com.apple.mdmclient.daemon.runatboot
```

**Both** launchd entries must be disabled — `com.apple.mdmclient.daemon` is the main daemon, `com.apple.mdmclient.daemon.runatboot` runs at early boot. After a reboot, verify both are still disabled:

```bash
sudo launchctl print-disabled system | grep mdm
# Expected: "com.apple.mdmclient.daemon" => disabled
#           "com.apple.mdmclient.daemon.runatboot" => disabled
```

If only `runatboot` stayed disabled after reboot, re-disable the main daemon. Launchctl disable state can be lost across reboots on macOS 15+ in some configurations.

Also kill these support processes that can continue independently of mdmclient daemon:
```bash
sudo pkill -9 -f "mbuseragent"
sudo pkill -9 -f "mbsystemadministration"
sudo pkill -9 -f "mbusertrampoline"
```

The watchdog should include all of them:
```bash
pkill -9 -f "mdmclient"; pkill -9 -f "Setup Assistant"; pkill -9 -f "mbuseragent"
```

## Prevent Setup Assistant on Next Boot

```bash
sudo touch /var/db/.AppleSetupDone
```

## Watchdog Launchd Agent (Immediate Relief)

Create a launchd agent that periodically kills mdmclient/Setup Assistant so the enrollment window never appears:

**~/Library/LaunchAgents/com.user.kill-mdm.plist:**
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
        <string>pkill -9 -f "mdmclient"; pkill -9 -f "Setup Assistant"; pkill -9 -f "mbuseragent"; pkill -9 -f "mbsystemadministration"; pkill -9 -f "mbusertrampoline"</string>
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
# Verify:
launchctl list com.user.kill-mdm
```

To change the interval, unload, edit `StartInterval`, and reload:
```bash
launchctl unload ~/Library/LaunchAgents/com.user.kill-mdm.plist
# Edit the <integer>5</integer> value (5s recommended — fast enough to suppress UI, negligible CPU)
launchctl load ~/Library/LaunchAgents/com.user.kill-mdm.plist
```

## Permanent Fix (Requires Physical Access / Recovery Mode)

Since `.cloudConfig*` files are SIP-protected, the only permanent fix is:

### Apple Silicon (M1/M2/M3/M4)

1. Fully shut down the Mac
2. Press and **hold** the power button until "Loading startup options..." appears
3. Click **Options → Continue**
4. Select admin user → enter password
5. In the menu bar: **Utilities → Terminal**
6. Run: `csrutil disable`
7. Expected output: "Successfully disabled System Integrity Protection"
8. Close Terminal → Apple menu → Restart
9. After reboot (SSH will work again), remove the cloud config files:
   ```bash
   cd /var/db/ConfigurationProfiles/Settings/
   sudo rm -f .cloudConfigHasActivationRecord .cloudConfigRecordFound .cloudConfigTimerCheck .profilesDEPTimerCheck
   ```
10. Shut down again → boot into Recovery (power button → Options) → Terminal
11. Run: `csrutil enable`
12. Restart — enrollment will never trigger again

### For macOS 15 (Sequoia): Disable only fs protection (safer)

Instead of `csrutil disable` (disables ALL SIP), use:
```bash
csrutil enable --without fs
```
This keeps SIP active for everything except filesystem protection — enough to delete the cloud config files. Re-enable with `csrutil enable` in a second Recovery boot.

### Intel Macs

1. Restart and hold **Cmd+R** until Recovery loads
2. Proceed with same steps as above (csrutil commands work identically)

## Detection

Check current enrollment status:
```bash
profiles status -type enrollment
profiles show -type enrollment   # shows DEP config if enrolled
```

Check local cloud config files (protected by SIP):
```bash
ls -la /var/db/ConfigurationProfiles/Settings/.cloudConfig*
# Files: .cloudConfigHasActivationRecord, .cloudConfigRecordFound,
#        .cloudConfigTimerCheck, .profilesDEPTimerCheck
```

Check running MDM processes:
```bash
ps aux | grep -i "mdmclient\|Setup Assistant\|mbuseragent\|mbsystemadministration"
```

## Notes

- The `.AppleSetupDone` file prevents Setup Assistant from showing on next boot but does NOT prevent mdmclient from running independently on macOS 15+.
- The watchdog approach with `launchctl` agent is a practical workaround that consumes negligible resources (<0.1% CPU every 5s).
- After DNS block + watchdog + launchctl disable, reboot is safe — the Mac will boot without MDM enrollment prompt.
