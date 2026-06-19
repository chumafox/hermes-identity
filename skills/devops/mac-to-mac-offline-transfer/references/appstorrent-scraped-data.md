# Appstorrent — Scraped Program Database

During a deep-research session (2026-05-14), 800 macOS ARM programs were scraped
from [appstorrent.ru](https://appstorrent.ru) using the Safari web scraping pattern.

## What was collected

**Source URL:** `https://appstorrent.ru/filter/cat=10/n.info-architecture=ARM/sort=date/order/desc/`

**Total entries:** 800 programs
**With descriptions:** 799

JSON format saved to `/tmp/arm_programs.json`:
```json
{
  "title": "DriveDx",
  "description": "Diagnostics text...",
  "url": "https://appstorrent.ru/123-drivedx.html"
}
```

Also available:
- `/tmp/appstorrent_arm_urls.txt` — text list of all 900+ scraped URLs
- `/tmp/arm_scrape.log` — full scraping log with retries and errors

## Data notes

- All programs filtered for ARM architecture (Apple Silicon compatible)
- Descriptions are extracted text, may contain footer/header noise
- ~100 URLs failed to load (Cloudflare timeouts even with 10 retries)
- Pagination: 21 pages × ~47 items/page ≈ 989 total. ~189 items not collected.

## Script used

`/tmp/parse_arm_v5.py` — Python + osascript + Safari JS injection
