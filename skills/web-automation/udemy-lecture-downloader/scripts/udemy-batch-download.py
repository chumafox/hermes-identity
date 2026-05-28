#!/usr/bin/env python3
"""
Udemy batch lecture downloader via Hermes browser tools.
Usage: invoke via execute_code or python3 (hermes_tools required)
"""

import argparse
import json
import os
import random
import re
import subprocess
import sys
import time
from pathlib import Path

COURSE_SLUG = "romikwvf"
LECTURE_LIST_PATH = Path.home() / ".hermes/skills/web-automation/udemy-lecture-downloader/references/lecture-list.md"
PROGRESS_PATH = Path.home() / ".hermes/scripts/udemy-progress.json"
OUTPUT_DIR_DEFAULT = Path.home() / "Downloads/udemy"

def human_delay(min_sec=3, max_sec=5):
    """Random delay to mimic human behavior."""
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)
    return delay

# Lecture IDs — extend as needed
LECTURES = {
    25: {"id": 31807710, "title": "25-umenshit-biologicheskiy-vozrast"},
    26: {"id": 39347530, "title": "26-n-atsetiltsistein-glistsin"},
    27: {"id": 40817042, "title": "27-krem-protiv-stareniya-kozhi"},
    28: {"id": 41797154, "title": "28-dieta-imitiruyushchaya-golodanie"},
    29: {"id": 43738734, "title": "29-standartnaya-lipidogramma"},
    30: {"id": 43739072, "title": "30-normy-lipidogrammy"},
    31: {"id": 43742974, "title": "31-apolipoprotein-b-lipoprotein-a"},
    32: {"id": 43751938, "title": "32-kak-opredelit-blyashki"},
    33: {"id": 43849692, "title": "33-umenshenie-blyashek-mekhanizm"},
    34: {"id": 43850198, "title": "34-pravilnye-nagruzki-dlya-lipoproteinov"},
    35: {"id": 43850626, "title": "35-kletchatka-dlya-normalizatsii-lipidov"},
    36: {"id": 43851272, "title": "36-dieta-dlya-snizheniya-ldl"},
    37: {"id": 43851584, "title": "37-beta-sitosterol"},
    38: {"id": 43851848, "title": "38-ekstrakt-bergamota"},
    39: {"id": 43857644, "title": "39-berberin"},
    40: {"id": 43857964, "title": "40-omega-3"},
    41: {"id": 43859454, "title": "41-ubiraem-faktory-riska-ateroskleroza"},
    42: {"id": 43862790, "title": "42-proshlo-2-mesyatsa-otsenka-rezultatov"},
    43: {"id": 31807716, "title": "43-zaklyuchitelnaya-lektsiya"},
}

def load_progress():
    if PROGRESS_PATH.exists():
        return json.loads(PROGRESS_PATH.read_text())
    return {"downloaded": [], "failed": []}

def save_progress(progress):
    PROGRESS_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS_PATH.write_text(json.dumps(progress, indent=2, ensure_ascii=False))

def get_video_url_js():
    return """
    (function() {
        var entries = performance.getEntriesByType('resource');
        var mp4 = entries.filter(function(r) { return r.name.indexOf('mp4-cdn') > -1 && r.name.indexOf('WebHD') > -1; }).map(function(r) { return r.name; })[0];
        if (mp4) return mp4;
        var video = document.querySelector('video');
        return video ? video.currentSrc : null;
    })()
    """.strip()

def download_lecture(lecture_num, output_dir):
    """Download a single lecture using browser_navigate + browser_console + curl."""
    info = LECTURES.get(lecture_num)
    if not info:
        print(f"ERROR: Unknown lecture #{lecture_num}")
        return False

    output_path = output_dir / f"{info['title']}.mp4"
    if output_path.exists():
        print(f"SKIP: {output_path.name} exists")
        return True

    url = f"https://www.udemy.com/course/{COURSE_SLUG}/learn/lecture/{info['id']}"
    print(f"\n=== {info['title']} ===")
    print(f"Navigate: {url}")

    try:
        from hermes_tools import browser_navigate, browser_console
    except ImportError:
        print("ERROR: run this via execute_code (hermes_tools required)")
        return False

    browser_navigate(url=url)
    time.sleep(15)

    video_url = None
    for attempt in range(3):
        print(f"Attempt {attempt+1}/3...")
        result = browser_console(expression=get_video_url_js())
        if result and isinstance(result, dict):
            val = result.get("output") or result.get("result", "")
            if isinstance(val, str) and val.startswith("http"):
                video_url = val.strip().strip('"')
                break
        time.sleep(10)

    if not video_url:
        print(f"FAILED: no video URL for lecture {lecture_num}")
        return False

    print(f"URL: {video_url[:80]}...")

    cookie_result = browser_console(expression="document.cookie")
    cookies = cookie_result.get("output", "") if isinstance(cookie_result, dict) else ""

    human_delay(3, 5)

    cmd = [
        "curl", "-L", "-o", str(output_path),
        "-H", "Referer: https://www.udemy.com/",
        "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "--cookie", cookies or "",
        video_url
    ]
    print(f"Downloading to {output_path}...")
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    proc.wait()

    if proc.returncode == 0:
        size = os.path.getsize(output_path) / (1024*1024)
        print(f"SUCCESS: {size:.0f} MB")
        return True
    else:
        stderr = proc.stderr.read().decode()[:200] if proc.stderr else ""
        print(f"FAILED: curl {proc.returncode}: {stderr}")
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lecture", type=int, help="Single lecture number")
    parser.add_argument("--output-dir", type=str, default=str(OUTPUT_DIR_DEFAULT))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    output_dir = Path(args.output_dir).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)

    progress = load_progress()

    if args.lecture:
        lectures = [args.lecture]
    else:
        lectures = sorted(LECTURES.keys())

    print(f"Output: {output_dir}")
    print(f"Lectures: {lectures}")

    for i, num in enumerate(lectures):
        if num in progress["downloaded"]:
            print(f"SKIP {num}: already in progress")
            continue

        ok = download_lecture(num, output_dir)
        if ok:
            progress.setdefault("downloaded", []).append(num)
        else:
            progress.setdefault("failed", []).append(num)
        save_progress(progress)

        if i < len(lectures) - 1:
            delay = human_delay(3, 5)
            print(f"Pause {delay:.1f}s...")

    print(f"\nDone. {len(progress.get('downloaded', []))}/{len(LECTURES)}")

if __name__ == "__main__":
    main()
