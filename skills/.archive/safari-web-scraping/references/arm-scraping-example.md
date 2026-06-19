Concrete scraping script for Cloudflare-protected sites via Safari.
Used to scrape ~900 ARM programs from appstorrent.ru filter page.
Pattern: collect URLs from pagination, then extract descriptions from each program page.

Key adaptations for this site:
- URLs are numeric IDs (appstorrent.ru/ID-name.html)
- Descriptions found in long text blocks (>60 chars) in <p> tags
- Navigation/footer text filtered out via skip words list
- Pagination: /filter/.../page/N/ with ~21 pages of ~47 items each
- 5 second waits between pages, 3 seconds between programs (safe, not detected as bot)

Script location: /tmp/parse_arm_v5.py
Tested: ~900 URLs in ~2.5 hours with ~90% success rate
Failures: pages that wouldn't load (Cloudflare timeout) - max 10 retries with 30s wait