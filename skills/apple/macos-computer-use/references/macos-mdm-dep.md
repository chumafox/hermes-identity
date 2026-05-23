# macOS MDM / DEP Enrollment Blocking

When a Mac shows unwanted MDM enrollment popups (e.g., "Enroll in MDM from Walmart/Jamf"), the device is registered in Apple's Device Enrollment Program (DEP) by a previous owner organization.

## Detection

Check enrollment status:

```bash
# Check installed profiles
sudo profiles list -v
sudo profiles list -v -user

# Check DEP enrollment configuration
sudo profiles show -type enrollment

# Key indicators in output:
#   IsMDMUnremovable = 0  → can be removed (good)
#   IsMDMUnremovable = 1  → cannot be removed via software
#   IsSupervised = 1      → device is supervised
#   ConfigurationURL      → enrollment server URL
#   OrganizationName      → who registered it
```

## Blocking

### 1. Block the enrollment server (hosts file)

```bash
# Find the URL from profiles show output (e.g., "https://walmart.jamfcloud.com/cloudenroll")
# Add to /etc/hosts:
echo "0.0.0.0 <mdm-server-domain>" | sudo tee -a /etc/hosts

# Example:
# echo "0.0.0.0 walmart.jamfcloud.com" | sudo tee -a /etc/hosts
```

### 2. Renew / decline enrollment

```bash
sudo profiles renew -type enrollment
```

### 3. Remove any installed profiles (if present)

```bash
# List profiles
sudo profiles list

# Remove a specific profile
sudo profiles remove -identifier <profile-identifier>
```

## SIP Protection (macOS 14+)

On modern macOS (14+), DEP configuration files in `/var/db/ConfigurationProfiles/Settings/` are protected by **System Integrity Protection (SIP)**:

- `sudo rm file` → `Operation not permitted`
- `sudo sh -c 'cat /dev/null > file'` → `Operation not permitted`
- `sudo chmod 000 file` → `Operation not permitted`
- `sudo touch file` → `Operation not permitted`

Key files in this directory:
- `.cloudConfigHasActivationRecord` — flag file (0 bytes, acts as boolean)
- `.cloudConfigRecordFound` — contains the actual DEP configuration JSON
- `.cloudConfigTimerCheck` — DEP enrollment retry timer
- `.profilesDEPTimerCheck` — DEP polling timer
- `com.apple.mdm.depnag.plist` — controls the red badge in System Settings > Profiles
- `com.apple.mdm.prelogin.plist` — pre-login enrollment state
- `.deviceConfigurationBits` — device configuration flags

Only the original organization (Walmart, etc.) or Apple can truly clear these. The hosts block prevents the enrollment server from being reached, but the files remain and the badging may persist.

## Aggressive Removal (SIP disable + Recovery)

If you need the red badge gone entirely:

1. **Reboot into Recovery Mode** — Apple Silicon: hold power button; Intel: Cmd+R at startup
2. **Open Terminal** in Recovery → `csrutil disable`
3. **Reboot normally**, then:
   ```bash
   sudo rm -f /var/db/ConfigurationProfiles/Settings/.cloudConfig*
   sudo rm -f /var/db/ConfigurationProfiles/Settings/com.apple.mdm.*
   ```
4. **Reboot into Recovery again** → `csrutil enable`
5. The red badge should be gone after full restart

**Warning**: Disabling SIP weakens system security. Re-enable it immediately after clearing the DEP files.

## Verification

```bash
# Quick check — if this says "No" for both, the device has no active enrollment:
sudo profiles status -type enrollment
# Output: Enrolled via DEP: No / MDM enrollment: No

# Full DEP config dump:
sudo profiles show -type enrollment
```

Even if `profiles status` says "No", the red badge may persist if the SIP-protected `.cloudConfigRecordFound` file still exists with organization data.

## Limitations

- **IsMDMUnremovable = 1**: The MDM profile is Apple-signed and cannot be removed without Apple's involvement or erasing the device.
- **DEP is tied to serial number**: Even with the enrollment server blocked, the device serial is registered in Apple's DEP. A full reset or disk erase will trigger enrollment again. The hosts block only prevents the live connection.
- **Permanent removal**: Requires the original organization to release the serial from their DEP portal, or Apple to do it with proof of purchase (for second-hand devices).

## Inspection Commands

```bash
# Apple DEP configuration
sudo profiles show -type enrollment

# Configuration profiles (system domain)
sudo profiles list

# All skipped setup screens (DEP config)
# Look for: SkipSetup = (TOS, Diagnostics, AppleID, ...)
```
