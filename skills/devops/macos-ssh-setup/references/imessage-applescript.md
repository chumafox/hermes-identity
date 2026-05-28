# iMessage via AppleScript

Send iMessages from macOS terminal without `imsg` or brew dependencies.

## Quick Send
```bash
osascript -e 'tell application "Messages" to send "MESSAGE" to buddy "RECIPIENT" of (service 1 whose service type is iMessage)'
```

Recipient can be:
- Phone number: `"+1234567890"`
- Apple ID email: `"user@me.com"`
- iMessage email: `"user@icloud.com"`

## Delayed Send
```bash
# Send after 5 minutes (300 seconds)
(sleep 300 && osascript -e 'tell application "Messages" to send "text" to buddy "email@me.com" of (service 1 whose service type is iMessage)') &
```

## Service Types
- `iMessage` — blue bubble
- `SMS` — green bubble (requires iPhone relay)

## Notes
- Messages.app must be signed in to iCloud
- First use may trigger permission prompt
- No API key or brew install needed
- Works even when `imsg` CLI install fails (brew timeout on slow internet)
