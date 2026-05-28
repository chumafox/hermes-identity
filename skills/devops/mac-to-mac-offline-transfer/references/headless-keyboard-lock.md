# Headless Mac Keyboard Lock/Unlock

When a headless Mac without display is transported (e.g. in a backpack), physical
keys press against the laptop body and trigger system sounds. Use hidutil to
blank all key mappings.

## Lock Keyboard (no keypresses processed)

```bash
hidutil property --set '{"UserKeyMapping":[{"HIDKeyboardModifierMappingSrc":0x700000000,"HIDKeyboardModifierMappingDst":0}]}'
```

## Unlock Keyboard

```bash
hidutil property --set '{"UserKeyMapping":[]}'
```

## Verify Status

```bash
hidutil property --get UserKeyMapping
# Empty array = unlocked
# Array with entry = locked
```

## Create Convenience Commands

```bash
echo "0000" | sudo -S tee /usr/local/bin/kbd-lock > /dev/null << 'LOCK'
#!/bin/bash
hidutil property --set '{"UserKeyMapping":[{"HIDKeyboardModifierMappingSrc":0x700000000,"HIDKeyboardModifierMappingDst":0}]}'
LOCK
sudo chmod +x /usr/local/bin/kbd-lock

echo "0000" | sudo -S tee /usr/local/bin/kbd-unlock > /dev/null << 'UNLOCK'
#!/bin/bash
hidutil property --set '{}'
UNLOCK
sudo chmod +x /usr/local/bin/kbd-unlock
```

**Pitfall:** When creating these scripts via SSH with `sudo tee`, use echo+sudo+bash -c
to avoid the password leaking into the heredoc:

```bash
echo "0000" | sudo -S bash -c "cat > /usr/local/bin/kbd-lock << 'LO'
#!/bin/bash
hidutil property --set '{}'
LO
chmod +x /usr/local/bin/kbd-lock"
```

## SSH Alias from Remote Mac

```bash
alias kbdlock='ssh -i ~/.ssh/key user@host /usr/local/bin/kbd-lock'
alias kbdunlock='ssh -i ~/.ssh/key user@host /usr/local/bin/kbd-unlock'
alias kbdstatus='ssh -i ~/.ssh/key user@host hidutil property --get UserKeyMapping'
```

## Pitfalls

- **Locked keyboard cannot be unlocked from the keyboard itself** — hidutil blocks
  EVERY key, including modifier combos. Always have a remote unlock method:
  - SSH from another machine: `ssh user@host /usr/local/bin/kbd-unlock`
  - Or plug in an external USB keyboard (uses a different HID stack)
- **hidutil changes are not persistent** — they reset on reboot. No need to
  "unlock before reboot".
- **System sounds during password prompt** — if the Mac is asleep and wakes briefly,
  keys may trigger login screen beeps. Lock before bagging.
- **Requires user to be logged in** — hidutil only works when a user session is active.
  At the login screen, keyboard still works.
- **`Ctrl+C` doesn't work while locked** — SIGINT relies on the keyboard being
  processed by the terminal. With hidutil active, Ctrl+C cannot send interrupt.

## ⚠ CRITICAL: safe script creation via SSH

When creating the lock/unlock scripts via SSH, use `echo "PASS" | sudo -S bash -c` to avoid having the password leaked into the heredoc:

```bash
# WRONG — password ends up in /usr/local/bin/kbd-lock:
echo "0000" | sudo -S tee /usr/local/bin/kbd-lock > /dev/null << 'LOCK'
#!/bin/bash
hidutil property --set '{"UserKeyMapping":[{"HIDKeyboardModifierMappingSrc":0x700000000,"HIDKeyboardModifierMappingDst":0}]}'
LOCK

# RIGHT — password doesn't end up in the script:
echo "0000" | sudo -S bash -c "cat > /usr/local/bin/kbd-lock << 'LO'
#!/bin/bash
hidutil property --set '{"UserKeyMapping":[{"HIDKeyboardModifierMappingSrc":0x700000000,"HIDKeyboardModifierMappingDst":0}]}'
LO
chmod +x /usr/local/bin/kbd-lock"

# Unlock variant:
echo "0000" | sudo -S bash -c "cat > /usr/local/bin/kbd-unlock << 'UN'
#!/bin/bash
# hidutil with empty {} also works: hidutil property --set '{}'
hidutil property --set '{\"UserKeyMapping\":[]}'
UN
chmod +x /usr/local/bin/kbd-unlock"
```

## ⚠ CRITICAL: Do NOT use kextunload or killall on HID services

On Apple Silicon Macs (M1/M2/M3/M4), the built-in keyboard and trackpad
are connected through the AppleSEP (Secure Enclave Processor), NOT through
standard IOKit kexts. The following commands can **permanently disable** the
internal keyboard and trackpad until a full DFU restore:

```bash
# ⚠ DO NOT RUN — will permanently disable built-in keyboard:
sudo kextunload /System/Library/Extensions/AppleHIDKeyboard.kext
sudo killall -HID ioService  # DO NOT USE
```

**What happens:** Unlike hidutil (which resets on reboot), these commands
corrupt the SEP's internal state for the built-in HID devices. After reboot:
- `ioreg -r -c IOHIDKeyboard` returns 0 — device not found
- Keyboard and trackpad are completely invisible to the OS
- Even full SMC/NVRAM reset (shutdown + holding power button) does NOT fix it
- The devices work again ONLY after a **DFU restore** using Apple Configurator 2

**Diagnosing the issue:**
```bash
ioreg -r -c IOHIDKeyboard | grep -c "IOHIDKeyboard"    # returns 0 if broken
ioreg -r -c IOHIDPointing | grep -c "IOHIDPointing"    # returns 0 if broken
system_profiler SPUSBDataType | grep -i "Keyboard"     # empty if broken
```

**The ONLY fix:**
1. Connect a secondary Mac (or any Mac with Apple Configurator 2)
2. Connect a USB-C cable between the two Macs
3. Put the affected Mac into **DFU mode** (Power + Ctrl + Option + Cmd for 10s)
4. Run **Actions → Restore** in Apple Configurator 2
5. The restore preserves user data but reinstalls the firmware/SEP

**Workaround while waiting for restore:**
- External USB keyboard and mouse work immediately (they use a different USB HID
  stack not routed through the SEP)
- The Mac is otherwise fully functional via SSH
- The Mac's display (if connected) shows the desktop and apps — only the built-in
  input devices are dead

**Lesson:** Never use `kextunload` or `killall` on HID/IOHID services on Apple Silicon.
Always use hidutil for keyboard blocking — it's the safe, macOS-approved API.
