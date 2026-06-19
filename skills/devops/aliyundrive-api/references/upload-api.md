# AliyunDrive Upload API

Трёхшаговый протокол загрузки файлов.

## Step 1: Create file with proof

```bash
curl -s -X POST 'https://api.aliyundrive.com/v2/file/create_with_proof' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <access_token>' \
  -d '{
    "drive_id": "<drive_id>",
    "parent_file_id": "root",
    "name": "file.txt",
    "size": 1234,
    "type": "file",
    "check_name_mode": "ignore"
  }'
```

**Параметры:**
- `check_name_mode`: `ignore` | `auto_rename` | `refuse` | `check_name_and_hash`
- `parent_file_id`: `root` для корня, или file_id папки

**Ответ:**
```json
{
  "part_info_list": [{"upload_url": "https://...oss...", "internal_upload_url": "https://..."}],
  "upload_id": "8EAA2A648D45460BA5DD85EB35744414",
  "rapid_upload": false,
  "file_id": "6a2e052070aa7c8dc8e847cea24bfa4725979caf",
  "revision_id": "6a2e052056cdb7bf30a84234b5a31514f7e480e6"
}
```

Ключевые поля: `part_info_list[0].upload_url`, `file_id`, `upload_id`.

## Step 2: Upload content

```bash
curl -X PUT -T /path/to/file "<upload_url>"
```

Одноразовая pre-signed URL из шага 1. Можно использовать `-T` (file upload).

## Step 3: Complete

```bash
curl -s -X POST 'https://api.aliyundrive.com/v2/file/complete' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer <access_token>' \
  -d '{
    "drive_id": "<drive_id>",
    "file_id": "<file_id>",
    "upload_id": "<upload_id>"
  }'
```

**Важно:** `upload_id` обязателен. Без него — `InvalidParameter.UploadId`.

## Питфоллы

- `check_name_mode` не принимает `overwrite`. Использовать `ignore` или `auto_rename`.
- `upload_id` из шага 1 обязателен для шага 3.
- `rapid_upload=true` — файл уже существует, повторная загрузка не нужна.
- Размер файла (`size`) должен совпадать с реальным размером PUT-запроса.
- OSS upload URL expires — если не загрузить вовремя, нужно создать новый proof.
