#!/usr/bin/env python3
"""
Safari osascript Scraper — Template for Cloudflare-protected sites.

Usage:
  1. Put URLs in /tmp/target_urls.txt (one per line, or let the script collect
     them from a paginated listing page)
  2. Adjust SELECTORS at the top to match the target site
  3. Adjust PAGINATION range
  4. Run: python3 safari_scraper.py

Features:
  - Pagination navigation (collect URLs from each page)
  - Retry with backoff for network drops (10 retries, 30s wait)
  - Checkpoint resume — restart after crash at last saved position
  - Progress save every 50 items
  - JSON output
"""

import subprocess, time, json, re, os, random

# ---- CONFIG ----
OUTPUT_FILE = "/tmp/scraped_programs.json"
LOG_FILE = "/tmp/scraper.log"
PAGINATION_PAGES = 21          # adjust
ITEM_COUNT = 989               # adjust
BASE_URL = "https://example.com/filter/cat=10/page/{}"
SKIP_WORDS = {"DMCA", "Правообладателям", "Программы", "Игры", "Расширения",
              "Версии", "Товары", "ИЗБРАННОЕ", "Telegram", "Комментарии",
              "FAQ", "Повреждено", "Поможем", "Показать ещё"}
MAX_RETRIES = 10
# -----------------

def log(msg):
    with open(LOG_FILE, "a") as f:
        f.write(f"{time.strftime('%c')} {msg}\n")

def osa(script):
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=20)
    return r.stdout.strip()

def navigate(url):
    osa(f'tell application "Safari" to set URL of current tab of window 1 to "{url}"')
    time.sleep(random.uniform(3, 6))

def get_text():
    return osa('tell application "Safari" to return text of current tab of window 1')

def get_urls_via_text(text):
    """Extract program URLs from page text."""
    return list(set(re.findall(r'(https://appstorrent\.ru/\d+[a-z0-9\-]*\.html)', text)))

def retry_navigate(url):
    """Navigate and verify page loaded."""
    for attempt in range(1, MAX_RETRIES + 1):
        navigate(url)
        text = get_text()
        if len(text) > 200:
            return text
        log(f"RETRY {attempt}/{MAX_RETRIES}: short text ({len(text)} chars)")
        time.sleep(30)
    return get_text()

def extract_program(text, url):
    """Extract title and description from page text."""
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    title = ""
    desc_parts = []
    for line in lines:
        if not title and len(line) > 2 and line not in SKIP_WORDS \
                and not any(s in line for s in SKIP_WORDS):
            title = line.split(" ")[0] if " " in line[:10] else line
        if len(line) > 50 and not any(s in line for s in SKIP_WORDS) \
                and not line.startswith("http"):
            desc_parts.append(line)
    return {"title": title, "description": " ".join(desc_parts)[:2000], "url": url}


# ---- STEP 1: Collect URLs ----
log("STEP 1: Collect URLs from pagination")
all_urls = set()

for page in range(1, PAGINATION_PAGES + 1):
    url = BASE_URL.format(page)
    text = retry_navigate(url)
    urls = get_urls_via_text(text)
    for u in urls:
        all_urls.add(u)
    log(f"Page {page}: {len(all_urls)} total")
    time.sleep(random.uniform(2, 5))

urls = sorted(all_urls)
log(f"Total: {len(urls)} URLs collected")

# ---- STEP 2: Parse descriptions ----
log("STEP 2: Parse descriptions")

# Resume from checkpoint
results = []
start = 0
try:
    with open("/tmp/scraper_checkpoint.txt") as f:
        start = int(f.read().strip())
    log(f"Resuming from index {start}")
except:
    pass

for i in range(start, len(urls)):
    url = urls[i]
    text = retry_navigate(url)
    entry = extract_program(text, url)
    results.append(entry)

    if (i + 1) % 50 == 0:
        with open(OUTPUT_FILE, "w") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        log(f"Saved {i+1}/{len(urls)}")

    with open("/tmp/scraper_checkpoint.txt", "w") as f:
        f.write(str(i + 1))

    time.sleep(random.uniform(2, 5))

# Final save
with open(OUTPUT_FILE, "w") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

log(f"DONE: {len(results)} programs")
print(f"Done: {len(results)} programs -> {OUTPUT_FILE}")
