#!/usr/bin/env bash
# scan_projects.sh — сканирует ~/, выводит классификацию папок проекта
# Usage: bash scan_projects.sh
set -euo pipefail

SYSTEM_DIRS="Library|Applications|Music|Movies|Pictures|Public|Downloads|Desktop|Documents|\.cache|\.config|\.npm|\.cargo|\.nvm|\.ssh|\.Trash|\.hermes|\.openclaw|\.gemini|\.codex|^bin$|^var$"

cd ~
for dir in */ ; do
    [ -d "$dir" ] || continue
    name="${dir%/}"
    # skip system / hidden
    skip=0
    case "$name" in
        .*) skip=1 ;;
        *) if echo "$name" | grep -qE "^($SYSTEM_DIRS)$"; then skip=1; fi ;;
    esac
    [ $skip -eq 1 ] && continue

    size=$(du -sh "$dir" 2>/dev/null | cut -f1 || echo "?")
    count=$(find "$dir" -maxdepth 2 \
        -not -path '*/node_modules/*' \
        -not -path '*/.git/*' \
        -not -path '*/.nvm/*' \
        2>/dev/null | wc -l | tr -d ' ')
    hasgit=""
    [ -d "$dir/.git" ] && hasgit="GIT"
    top=$(ls "$dir" 2>/dev/null | head -5 | tr '\n' ' ')
    printf "%s|%s|%s|%s|%s\n" "$name" "$size" "$count" "$hasgit" "$top"
done | sort -t'|' -k2 -rh