# Pre-built Binary macOS Version Incompatibility

Many ML/AI tools distribute pre-compiled binaries (Mach-O executables, `.dylib`s) that may be built for a newer macOS version than the user is running.

## Error Signature

```
dyld[PID]: Symbol not found: _OBJC_CLASS_$_<ClassName>
  Referenced from: <UUID> <path/to/binary> (built for macOS X.Y which is newer than running OS)
  Expected in: <UUID> /System/Library/Frameworks/<Framework>.framework/Versions/A/<Framework>
```

### Common variants

| Build target | Running OS | Typical error |
|-------------|-----------|---------------|
| macOS 26.0 (Sequoia+) | macOS 14.x (Sonoma) | `_OBJC_CLASS_$_MTLResidencySetDescriptor` not found in Metal |

## Root Cause

The binary was compiled against a macOS SDK that includes APIs not present in the running OS version. Apple's Metal, CoreGraphics, and other frameworks often add new API symbols in each major release. When a developer builds on the latest Xcode (targeting the latest SDK), the resulting binary may use symbols that don't exist on older systems.

## Diagnosis

```bash
# Check what macOS version the binary was built for:
otool -l <binary> 2>/dev/null | grep -A3 'LC_BUILD_VERSION' | head -6
# Output shows: platform, minos (minimum OS), sdk

# For a quick check:
strings <binary> | grep -i 'built for macOS\|minos'

# Identify the framework version running:
/usr/bin/sw_vers
```

## Solutions

1. **Update macOS** — If the binary requires macOS 26.0+, update the system to match.

2. **Find an older build** — Check the developer's releases page for a build targeting your macOS version. Some projects tag builds by OS version (e.g., `*-sonoma-arm64`, `*-macos14`).

3. **Build from source** — If the tool is open-source, compile it locally:
   ```bash
   git clone <repo>
   cd <repo>
   # Use the system's Xcode/CLI tools to build for the running OS version
   make build
   ```

4. **Use a different tool** — If the binary can't be matched to your macOS version, find an alternative that supports it (e.g., ComfyUI instead of a pre-compiled app backend).

## Prevention

- Before downloading a pre-built binary, check its "minimum macOS version" requirement
- For Electron apps, the Electron shell usually runs fine (it bundles its own Chromium); the native binary backend (daemon, CLI) is the problem
- Check `brew` formulas — they typically build from source and work on the current macOS version
- Open-source tools can usually be built from source for any supported macOS version
