#!/bin/bash
# AliyunDrive CLI — REST API wrapper (standalone, no WebDAV needed)
# Usage: alipan ls [path]    — list files
#        alipan cat <file>   — download + print to stdout
#        alipan info          — drive info / quota
#        alipan dl <file>    — download to current dir
#        alipan refresh      — refresh token
#        alipan help         — this help

set -euo pipefail

TOKEN_FILE="$HOME/.config/alipan-token.json"

# --- Token management ---
get_token() {
    if [ ! -f "$TOKEN_FILE" ]; then
        echo "No token file. Run: alipan refresh <refresh_token>" >&2
        exit 1
    fi
    local rt
    rt=$(jq -r '.refresh_token' "$TOKEN_FILE")
    resp=$(curl -s -X POST 'https://api.aliyundrive.com/v2/account/token' \
        -H 'Content-Type: application/json' \
        -d "{\"refresh_token\":\"$rt\",\"grant_type\":\"refresh_token\"}")

    new_rt=$(echo "$resp" | jq -r '.refresh_token // empty')
    new_at=$(echo "$resp" | jq -r '.access_token // empty')
    # Prefer default_drive_id (main) over default_sbox_drive_id (backup — may be locked)
    drive_id=$(echo "$resp" | jq -r '.default_drive_id // .default_sbox_drive_id // empty')

    if [ -z "$new_at" ]; then
        echo "Token refresh failed: $(echo "$resp" | jq -r '.message // .code')" >&2
        exit 1
    fi

    printf '{"refresh_token":"%s","access_token":"%s","drive_id":"%s"}\n' \
        "$new_rt" "$new_at" "$drive_id" > "$TOKEN_FILE"
    echo "$new_at" "$drive_id"
}

# --- Commands ---
cmd_refresh() {
    if [ $# -lt 1 ]; then
        echo "Usage: alipan refresh <refresh_token>" >&2
        exit 1
    fi
    local rt="$1"
    resp=$(curl -s -X POST 'https://api.aliyundrive.com/v2/account/token' \
        -H 'Content-Type: application/json' \
        -d "{\"refresh_token\":\"$rt\",\"grant_type\":\"refresh_token\"}")

    new_rt=$(echo "$resp" | jq -r '.refresh_token // empty')
    new_at=$(echo "$resp" | jq -r '.access_token // empty')
    drive_id=$(echo "$resp" | jq -r '.default_drive_id // .default_sbox_drive_id // empty')

    if [ -z "$new_at" ]; then
        echo "Error: $(echo "$resp" | jq -r '.message // "unknown"')" >&2
        exit 1
    fi

    printf '{"refresh_token":"%s","access_token":"%s","drive_id":"%s"}\n' \
        "$new_rt" "$new_at" "$drive_id" > "$TOKEN_FILE"
    echo "Token saved. Drive: $drive_id"
}

cmd_info() {
    read -r at did <<< "$(get_token)"
    curl -s -X POST 'https://api.aliyundrive.com/v2/drive/get' \
        -H 'Content-Type: application/json' \
        -H "Authorization: Bearer $at" \
        -d "{\"drive_id\":\"$did\"}" | jq '{used: .used_size, total: .total_size, status: .status}'
}

cmd_ls() {
    local path="${1:-root}"
    read -r at did <<< "$(get_token)"
    curl -s -X POST 'https://api.aliyundrive.com/v2/file/list' \
        -H 'Content-Type: application/json' \
        -H "Authorization: Bearer $at" \
        -d "{\"drive_id\":\"$did\",\"parent_file_id\":\"$path\",\"limit\":100}" | \
        jq -r '.items[] | "\(.type[0:1]) \(.file_id) \(.size // 0 | ./1024/1024 | floor)M  \(.name)"' 2>/dev/null || \
        echo "(empty or error)"
}

cmd_cat() {
    local file_id="$1"
    read -r at did <<< "$(get_token)"
    dl_url=$(curl -s -X POST 'https://api.aliyundrive.com/v2/file/get_download_url' \
        -H 'Content-Type: application/json' \
        -H "Authorization: Bearer $at" \
        -d "{\"drive_id\":\"$did\",\"file_id\":\"$file_id\"}" | jq -r '.url // empty')
    [ -z "$dl_url" ] && { echo "Failed to get download URL" >&2; exit 1; }
    curl -s "$dl_url"
}

cmd_dl() {
    local file_id="$1"
    read -r at did <<< "$(get_token)"
    info=$(curl -s -X POST 'https://api.aliyundrive.com/v2/file/get' \
        -H 'Content-Type: application/json' \
        -H "Authorization: Bearer $at" \
        -d "{\"drive_id\":\"$did\",\"file_id\":\"$file_id\"}")
    name=$(echo "$info" | jq -r '.name')
    dl_url=$(curl -s -X POST 'https://api.aliyundrive.com/v2/file/get_download_url' \
        -H 'Content-Type: application/json' \
        -H "Authorization: Bearer $at" \
        -d "{\"drive_id\":\"$did\",\"file_id\":\"$file_id\"}" | jq -r '.url')
    echo "Downloading: $name"
    curl -o "$name" "$dl_url"
}

cmd_up() {
    local filepath="${1:-}"
    local parent_id="${2:-root}"
    if [ ! -f "$filepath" ]; then
        echo "Usage: alipan up <local_file> [parent_folder_id]"
        exit 1
    fi
    local filename; filename=$(basename "$filepath")
    local filesize; filesize=$(stat -f%z "$filepath")
    read -r at did <<< "$(get_token)"

    resp=$(curl -s -X POST 'https://api.aliyundrive.com/v2/file/create_with_proof' \
        -H 'Content-Type: application/json' \
        -H "Authorization: Bearer $at" \
        -d "{\"drive_id\":\"$did\",\"parent_file_id\":\"$parent_id\",\"name\":\"$filename\",\"size\":$filesize,\"type\":\"file\",\"check_name_mode\":\"ignore\"}")

    upload_url=$(echo "$resp" | jq -r '.part_info_list[0].upload_url // ""')
    file_id=$(echo "$resp" | jq -r '.file_id // ""')
    upload_id=$(echo "$resp" | jq -r '.upload_id // ""')
    rapid_upload=$(echo "$resp" | jq -r '.rapid_upload // false')

    if [ "$rapid_upload" = "true" ]; then
        echo "Rapid upload (file already exists): $filename"
        return
    fi

    if [ -z "$upload_url" ]; then
        echo "Upload failed: $(echo "$resp" | jq -r '.message // "no upload URL"')"
        exit 1
    fi

    echo "Uploading: $filename ($(echo "scale=1; $filesize/1024/1024" | bc)MB)"
    curl -s -X PUT -T "$filepath" "$upload_url" | cat

    if [ -n "$file_id" ]; then
        curl -s -X POST 'https://api.aliyundrive.com/v2/file/complete' \
            -H 'Content-Type: application/json' \
            -H "Authorization: Bearer $at" \
            -d "{\"drive_id\":\"$did\",\"file_id\":\"$file_id\",\"upload_id\":\"$upload_id\"}" > /dev/null
        echo "Done: $filename"
    fi
}

case "${1:-help}" in
    refresh) shift; cmd_refresh "$@" ;;
    info) cmd_info ;;
    ls) shift; cmd_ls "$@" ;;
    cat) shift; cmd_cat "$@" ;;
    dl) shift; cmd_dl "$@" ;;
    up) shift; cmd_up "$@" ;;
    *) echo "Usage: alipan {refresh|info|ls|cat|dl|up}"; exit 1 ;;
esac
