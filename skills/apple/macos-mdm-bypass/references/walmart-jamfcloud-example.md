# Walmart Jamf Cloud DEP Configuration (Real-World Example)

From a second-hand Mac (M1 Pro, macOS 15 Sequoia) previously owned by Walmart.

## DEP Enrollment Output

```
sudo profiles show -type enrollment

Device Enrollment configuration:
{
    AllowPairing = 0;
    AnchorCertificates = ();
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
    SkipSetup = (
        TOS, Diagnostics, AppleID, FileVault, Restore, Payment,
        Registration, ScreenTime, Intelligence, Welcome, Siri,
        DisplayTone, iCloudDiagnostics, Privacy, iCloudStorage,
        AdditionalPrivacySettings, EnableLockdownMode,
        TermsOfAddress, Wallpaper
    );
}
```

## SIP-Protected Cloud Config Files

Located at `/var/db/ConfigurationProfiles/Settings/`:

```
.cloudConfigHasActivationRecord   (0 bytes, flag file)
.cloudConfigRecordFound           (2.3 KB, DEP record)
.cloudConfigTimerCheck             (260 bytes, retry timer)
.profilesDEPTimerCheck            (603 bytes, DEP check timer)
```

These files cannot be removed even as root. Deletion requires SIP disable via Recovery Mode.

## Bypass Applied

- DNS blocks: deviceenrollment.apple.com, gdmf.apple.com, mdmenrollment.apple.com, iprofiles.apple.com, iprofiles.mac.com, deviceservices.apple.com, walmart.jamfcloud.com, jamfcloud.com
- /var/db/.AppleSetupDone created
- launchctl disable: com.apple.mdmclient.daemon, com.apple.mdmclient.daemon.runatboot
- Watchdog: com.user.kill-mdm (5s interval) in ~/Library/LaunchAgents/
- Result: Enrolled via DEP: No, MDM enrollment: No
