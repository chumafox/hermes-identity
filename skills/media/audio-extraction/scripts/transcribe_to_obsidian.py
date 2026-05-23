#!/usr/bin/env python3
\"\"\"Bulk transcribe WAV files to Obsidian markdown using mlx-whisper.

Usage:
    python3 transcribe_to_obsidian.py /path/to/wav_dir [--model MODEL] [--source NAME] [--tags "tag1,tag2"]
\"\"\"
import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

import mlx_whisper


def main():
    parser = argparse.ArgumentParser(description="Transcribe WAV files to Obsidian markdown")
    parser.add_argument("input_dir", type=str, help="Directory with WAV files (recursive)")
    parser.add_argument("--model", default="mlx-community/whisper-large-v3-turbo",
                        help="MLX Whisper model to use")
    parser.add_argument("--source", default="transcription",
                        help="Source tag for Obsidian frontmatter (e.g., 'udemy-course-name')")
    parser.add_argument("--tags", default="",
                        help="Comma-separated tags for Obsidian frontmatter (e.g., 'lecture,anti-age')")
    parser.add_argument("--skip-existing", action="store_true", default=True,
                        help="Skip files that already have .md output")
    parser.add_argument("--no-skip", dest="skip_existing", action="store_false",
                        help="Re-transcribe even if .md exists")
    args = parser.parse_args()

    # Parse tags
    tag_list = []
    if args.tags:
        tag_list = [t.strip() for t in args.tags.split(",") if t.strip()]
    tags_yaml = f"\ntags: [{', '.join(tag_list)}]" if tag_list else ""

    src = Path(args.input_dir)
    if not src.is_dir():
        print(f"Error: {src} is not a directory")
        sys.exit(1)

    wav_files = sorted(src.rglob("*.wav"))
    total = len(wav_files)
    if total == 0:
        print("No WAV files found")
        return

    print(f"Found {total} WAV files (source: {args.source})")
    success = 0
    skipped = 0

    for i, wav in enumerate(wav_files, 1):
        md = wav.with_suffix(".md")

        if args.skip_existing and md.exists():
            print(f"[{i}/{total}] SKIP (exists): {wav.relative_to(src)}")
            skipped += 1
            continue

        rel = wav.relative_to(src)
        wav_size = wav.stat().st_size
        duration_sec = wav_size / (16000 * 2)  # approx: 16kHz mono 16-bit = 32000 B/s

        print(f"[{i}/{total}] Transcribing: {rel} (~{duration_sec/60:.1f} min)...")
        sys.stdout.flush()

        t0 = time.time()
        try:
            result = mlx_whisper.transcribe(
                str(wav),
                path_or_hf_repo=args.model,
                verbose=False
            )
            elapsed = time.time() - t0
            text = result["text"].strip()

            # Obsidian markdown with frontmatter
            md_content = f"""---
title: "{wav.stem}"
source: "{args.source}"
duration_min: {duration_sec/60:.1f}
transcribed_at: "{datetime.now():%Y-%m-%d %H:%M}"
model: "{args.model}"{tags_yaml}
---

{text}
"""
            md.write_text(md_content, encoding="utf-8")

            word_count = len(text.split())
            speedup = duration_sec / elapsed if elapsed > 0 else 0
            print(f"  OK — {word_count} words, {elapsed:.1f}s (x{speedup:.0f} realtime)")
            success += 1

        except Exception as e:
            print(f"  ERROR: {e}")
            continue

    print(f"\nDone! {success} transcribed, {skipped} skipped, {total} total.")


if __name__ == "__main__":
    main()
