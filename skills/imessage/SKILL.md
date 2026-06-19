---
name: imessage
description: "Send and receive iMessages/SMS via the imsg CLI on macOS."
tags: ["iMessage", "SMS", "messaging", "macOS", "Apple"]
---

# iMessage

Send iMessage/SMS via macOS Messages.app.

## Prerequisites

- **macOS** with Messages.app signed in (any Apple ID)

## Primary Method — `imsg` CLI

Install: `brew install steipete/tap/imsg`  
Grant Full Disk Access for terminal, then Automation permission when prompted.

## Fallback — AppleScript (no brew needed)

When brew is unavailable or slow (e.g. China WiFi), use `osascript` directly:

```bash
# Send
osascript -e 'tell application "Messages" to send "text" to buddy "user@me.com" of (service 1 whose service type is iMessage)'

# Send after delay (background)
# (sleep 300 && osascript -e 'tell application "Messages" to send "Сейчас $(date)" to buddy "user@me.com" of (service 1 whose service type is iMessage)') &
```

AppleScript supports iMessage only (not SMS). For SMS (green bubble), use `sms` service type or `imsg send --service sms`.

## When to Use

- User asks to send an iMessage or text message
- Reading iMessage conversation history
- Checking recent Messages.app chats
- Sending to phone numbers or Apple IDs

## When NOT to Use

- Telegram/Discord/Slack/WhatsApp messages → use the appropriate gateway channel
- Group chat management (adding/removing members) → not supported
- Bulk/mass messaging → always confirm with user first

### Quick Reference

**Fallback (no brew): AppleScript** — use when `imsg` not installed or brew times out:
```bash
osascript -e 'tell application "Messages" to send "text" to buddy "user@me.com" of (service 1 whose service type is iMessage)'
```
For delayed sends: `(sleep 300 && osascript -e 'tell application "Messages" ...') &`

### List Chats

```bash
imsg chats --limit 10 --json
```

### View History

```bash
# By chat ID
imsg history --chat-id 1 --limit 20 --json

# With attachments info
imsg history --chat-id 1 --limit 20 --attachments --json
```

### Send Messages

```bash
# Text only
imsg send --to "+14155551212" --text "Hello!"

# With attachment
imsg send --to "+14155551212" --text "Check this out" --file /path/to/image.jpg

# Force iMessage or SMS
imsg send --to "+14155551212" --text "Hi" --service imessage
imsg send --to "+14155551212" --text "Hi" --service sms
```

### Watch for New Messages

```bash
imsg watch --chat-id 1 --attachments
```

## Service Options

- `--service imessage` — Force iMessage (requires recipient has iMessage)
- `--service sms` — Force SMS (green bubble)
- `--service auto` — Let Messages.app decide (default)

## Rules

1. **Always confirm recipient and message content** before sending
2. **Never send to unknown numbers** without explicit user approval
3. **Verify file paths** exist before attaching
4. **Don't spam** — rate-limit yourself

## Example Workflow

User: "Text mom that I'll be late"

```bash
# 1. Find mom's chat
imsg chats --limit 20 --json | jq '.[] | select(.displayName | contains("Mom"))'

# 2. Confirm with user: "Found Mom at +1555123456. Send 'I'll be late' via iMessage?"

# 3. Send after confirmation
imsg send --to "+1555123456" --text "I'll be late"
```
