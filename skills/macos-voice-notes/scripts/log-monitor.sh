#!/bin/bash
# Handy log monitor: captures transcriptions from Handy log and appends to .md file
# Usage: bash ~/.handy-log-monitor.sh [output_file]
# Default output: ~/Handy_Voice_Notes.md

LOG="$HOME/Library/Logs/com.pais.handy/handy.log"
FILE="${1:-$HOME/Handy_Voice_Notes.md}"

if [ ! -f "$LOG" ]; then
    echo "Handy log not found: $LOG" >&2
    echo "Start Handy first, then run this monitor." >&2
    exit 1
fi

touch "$FILE"
LAST_LINE=""

echo "Handy Voice Notes monitor started. PID: $$"
echo "Output: $FILE"

tail -F -n0 "$LOG" 2>/dev/null | while read -r line; do
    if echo "$line" | grep -q 'Transcription result:'; then
        TEXT=$(echo "$line" | sed -n 's/.*Transcription result: //p')
        if [ -n "$TEXT" ] && [ "$TEXT" != "$LAST_LINE" ]; then
            LAST_LINE="$TEXT"
            TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")
            printf "\n## %s\n\n%s\n" "$TIMESTAMP" "$TEXT" >> "$FILE"
            echo "[+] Saved: ${TEXT:0:50}..." >&2
        fi
    fi
done
