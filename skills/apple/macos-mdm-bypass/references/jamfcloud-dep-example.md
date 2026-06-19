# Real-world Jamf Cloud DEP Configuration

Found on a second-hand Mac (Walmart/Jamf Cloud). The Mac had no prior enrollment and no configuration profiles installed, but the DEP enrollment trigger lived in firmware/NVRAM.

## Detection via SSH

```bash
sudo profiles show -type enrollment
```

## Raw DEP Configuration

```
Device Enrollment configuration:
{
    AllowPairing = 0;
    AnchorCertificates =     (
    );
    AutoAdvanceSetup = 1;
    AwaitDeviceConfigured = 1;
    ConfigurationURL = "https://walmart.jamfcloud.com/cloudenroll";
    IsMDMUnremovable = 0;
    IsMandatory = 1;
    IsMultiUser = 0;
    IsSupervised = 1;
    Language = en;
    MDMProtocolVersion = 1;
    OrganizationAddress = "850 Cherry Ave, n/a, , San Bruno, CA 94066";
    OrganizationAddressLine1 = "850 Cherry Ave";
    OrganizationAddressLine2 = "n/a";
    OrganizationCity = "San Bruno";
    OrganizationCountry = USA;
    OrganizationDepartment = Walmart;
    OrganizationEmail = "chamnith.nou@walmartlabs.com";
    OrganizationMagic = 42C5AA5F036841C1BEB919B074B2FB9E;
    OrganizationName = "Wal-mart.com Usa, Llc";
    OrganizationPhone = "1-844-309-3088";
    OrganizationRegion = US;
    OrganizationSupportPhone = "1-844-309-3088";
    OrganizationZipCode = 94066;
    Region = US;
    SkipSetup =     (
        TOS,
        Diagnostics,
        AppleID,
        FileVault,
        Restore,
        Payment,
        Registration,
        ScreenTime,
        Intelligence,
        Welcome,
        Siri,
        DisplayTone,
        iCloudDiagnostics,
        Privacy,
        iCloudStorage,
        AdditionalPrivacySettings,
        EnableLockdownMode,
        TermsOfAddress,
        Wallpaper
    );
}
```

## Key Observations

- **IsMandatory = 1** — No "skip" or "set up later" option in UI. Only an "Enroll" button.
- **IsSupervised = 1** — The Mac is flagged for supervision (deeper management capabilities).
- **AutoAdvanceSetup = 1** — Setup Assistant auto-advances through skipped setup panes.
- **AwaitDeviceConfigured = 1** — Setup Assistant waits for MDM configuration before proceeding.
- **SkipSetup** has almost everything skipped (19 items) — the only purpose of Setup Assistant on this Mac is to force MDM enrollment.
- **OrganizationMagic** — Unique DEP identifier (per-device or per-org).

## Running Processes (before bypass)

After boot, before any interaction:

```
/usr/libexec/mdmclient daemon              # launchd-managed system daemon
/usr/libexec/mdmclient agent               # per-user agent
/System/Library/CoreServices/Setup Assistant.app/Contents/MacOS/Setup Assistant -MiniBuddyYes -ForceMDMEnroll
/System/Library/CoreServices/Setup Assistant.app/Contents/Resources/mbuseragent
/System/Library/CoreServices/Setup Assistant.app/Contents/Resources/mbusertrampoline
/System/Library/CoreServices/Setup Assistant.app/Contents/Resources/mbsystemadministration
```

## DNS Block Recipe

For a Jamf Cloud DEP lock:

```
0.0.0.0 walmart.jamfcloud.com     # Specific MDM server
0.0.0.0 jamfcloud.com              # Jamf Cloud root domain
0.0.0.0 deviceenrollment.apple.com # Apple DEP check-in server
0.0.0.0 gdmf.apple.com             # Apple MDM push gateway
0.0.0.0 deviceservices.apple.com   # Apple device services
```
