---
name: aliyundrive-api
description: "Work with AliyunDrive (阿里云盘) — get API tokens, CLI wrapper, upload/download, WebDAV alternatives, and Safari token extraction"
tags: ["devops", "cloud-storage"]
---

# AliyunDrive (阿里云盘) API & CLI

## Overview
AliyunDrive (aliyundrive.com) — китайское облачное хранилище от Alibaba Group.
Два Mac (dispo/pro) используют его для обмена файлами через Китай.

## CLI wrapper (`alipan`)

Основной инструмент — `~/bin/alipan`. Bash + curl + jq, без лишних зависимостей.

**Установка:**
```bash
cp ~/.hermes/skills/devops/aliyundrive-api/templates/alipan.sh ~/bin/alipan
chmod +x ~/bin/alipan
# Добавить ~/bin в PATH если нет:
echo 'export PATH="$HOME/bin:$PATH"' >> ~/.zshrc
alipan refresh <refresh_token>
```

**Команды:**
| Команда | Что делает |
|---------|-----------|
| `alipan info` | Квота диска (used/total) |
| `alipan ls [folder_id]` | Список файлов (по умолч. root) |
| `alipan cat <file_id>` | Скачать файл в stdout |
| `alipan dl <file_id>` | Скачать в тек. папку |
| `alipan up <file> [folder_id]` | Загрузить файл |
| `alipan refresh [token]` | Сохранить/обновить токен |

**Токен:** `~/.config/alipan-token.json`. Автообновляется.
**Drive ID:** `default_drive_id` — основной. `default_sbox_drive_id` — backup, может быть locked ("drive is locked").

### Upload flow (если делать руками)
```
create_with_proof → PUT на upload_url → complete с upload_id
```
Параметры:
- `check_name_mode`: только `ignore`, `auto_rename`, `refuse`, `check_name_and_hash`. `overwrite` невалиден.
- `upload_id` обязателен для complete — без него 400.
- Размер: `stat -f%z` (macOS) / `stat -c%s` (Linux).

### HTTP file server (альтернатива WebDAV)

`alipan-webdav` — Python HTTP сервер для просмотра файлов в браузере.
```bash
python3 ~/.hermes/skills/devops/aliyundrive-api/templates/alipan-webdav.py
# → http://localhost:18080
```
Не монтируется в Finder (не WebDAV), но удобно для быстрого просмотра.

## Получение refresh_token из Safari

Если пользователь уже залогинен в Safari:
```bash
osascript -e '
tell application "Safari"
    do JavaScript "
        var t = JSON.parse(localStorage.getItem(\"token\"));
        t.refresh_token;
    " in current tab of window 1
end tell
'
```
Требуется: Safari → Settings → Advanced → Show Develop menu + Allow JavaScript from Apple Events.

## WebDAV (legacy)

### aliyundrive-webdav (open source)
```bash
pip3 install aliyundrive-webdav
aliyundrive-webdav --refresh-token <token> --port 18080 --root /
```

**Проблема v2.3.3:** отвергает refresh_token (32 hex) с `"Invalid refresh token value"`, хотя токен валидный и работает через REST API.
**Решение:** QR login (`aliyundrive-webdav qr login`) или CLI-wrapper вместо WebDAV.

**Finder mount:** Cmd+K → http://localhost:18080 → Connect (только с работающим WebDAV сервером).

## Pitfalls

- **SSL на macOS:** `urlopen` падает с `CERTIFICATE_VERIFY_FAILED`. Фикс: `pip3 install certifi`, создать контекст с `cafile=certifi.where()`.
- **wsgidav 4.x:** API изменился — `DAVResource` → `DAVNonCollection`, `get_resource_instances()` → `get_resource_inst()` (возвращает один ресурс, не список). `simple_dc: {"user_mapping": {"*": True}}` обязателен.
- **`model.base_url` в config.yaml:** НЕ ставить для built-in провайдеров — сломает `/model` команду.
- **token rotation:** refresh_token меняется после каждого использования — сохранять новый.
- **~/.hermes/config.yaml:** patch/write_file блокируются — только `hermes config set`.
- **hermes config set custom_providers:** перезаписывает ВЕСЬ массив, а не добавляет элемент. Читать существующий, дополнять, писать целиком.
