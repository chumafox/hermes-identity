#!/usr/bin/env python3
"""
Grab one Udemy HLS lecture: m3u8 -> fetch all .ts via CDP -> ffmpeg concat.
Call from execute_code. Usage:
  import importlib.util, sys, os
  spec = importlib.util.spec_from_file_location("grab",
    os.path.expanduser("~/.hermes/skills/web-automation/udemy-lecture-downloader/scripts/udemy-grab.py"))
  mod = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(mod)
  mod.download_lecture(26)
"""

import base64, json, os, re, shutil, subprocess, sys, time
from pathlib import Path

COURSE_SLUG = "romikwvf"
OUT = Path.home() / "Downloads/udemy"

LECTURES = {
    25: (31807710, "25-umenshit-biologicheskiy-vozrast.mp4"),
    26: (39347530, "26-n-atsetiltsistein-glistsin.mp4"),
    27: (40817042, "27-krem-protiv-stareniya-kozhi.mp4"),
    28: (41797154, "28-dieta-imitiruyushchaya-golodanie.mp4"),
    29: (43738734, "29-standartnaya-lipidogramma.mp4"),
    30: (43739072, "30-normy-lipidogrammy.mp4"),
    31: (43742974, "31-apolipoprotein-b-lipoprotein-a.mp4"),
    32: (43751938, "32-kak-opredelit-blyashki.mp4"),
    33: (43849692, "33-umenshenie-blyashek-mekhanizm.mp4"),
    34: (43850198, "34-pravilnye-nagruzki-dlya-lipoproteinov.mp4"),
    35: (43850626, "35-kletchatka-dlya-normalizatsii-lipidov.mp4"),
    36: (43851272, "36-dieta-dlya-snizheniya-ldl.mp4"),
    37: (43851584, "37-beta-sitosterol.mp4"),
    38: (43851848, "38-ekstrakt-bergamota.mp4"),
    39: (43857644, "39-berberin.mp4"),
    40: (43857964, "40-omega-3.mp4"),
    41: (43859454, "41-ubiraem-faktory-riska-ateroskleroza.mp4"),
    42: (43862790, "42-proshlo-2-mesyatsa-otsenka-rezultatov.mp4"),
    43: (31807716, "43-zaklyuchitelnaya-lektsiya.mp4"),
}


def download_lecture(num, target_id=None):
    """
    Download one lecture.
    
    Параметры:
      num: номер лекции (26-43)
      target_id: ID вкладки CDP (строка из Target.getTargets). Если None,
                 использует последнюю attached вкладку.
    
    Возвращает True/False.
    
    ⚠️ ВАЖНО: Эта функция вызывается из execute_code, но не может
    использовать browser_navigate/browser_console напрямую.
    **Перед вызовом** нужно:
    1. Перейти на лекцию через browser_navigate или CDP Runtime.evaluate
    2. Подождать 15-20с
    3. Передать target_id вкладки
    """
    from hermes_tools import terminal
    
    lecture_id, filename = LECTURES.get(num, (None, None))
    if not lecture_id:
        print(f"ERROR: unknown lecture {num}")
        return False
    
    outpath = OUT / filename
    if outpath.exists():
        mb = outpath.stat().st_size / 1_000_000
        print(f"SKIP {outpath.name} ({mb:.0f} MB)")
        return True
    
    print(f"\n=== {num}: {filename} ===")
    
    # Get m3u8 URLs via performance entries (on the target tab)
    r = terminal(f'''osascript -e '
tell application "Safari"
    do JavaScript "
        var entries = performance.getEntriesByType(\\\"resource\\\");
        var m3u8s = entries.filter(function(r) {{ return r.name.includes(\\\".m3u8\\\") }}).map(function(r) {{ return r.name }});
        m3u8s[0] || \\\"\\\";
    " in current tab of window 1
end tell' 2>&1 | head -1''')
    
    # ... (метод через osascript + Safari ограничен)
    
    OUT.mkdir(parents=True, exist_ok=True)
    return False  # stub - actual implementation depends on CDP context
