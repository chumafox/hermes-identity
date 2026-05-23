#!/usr/bin/env python3
"""Bulk convert MP4 files to 16kHz mono WAV for Whisper transcription.

Usage:
    python3 bulk_convert_to_wav.py /path/to/videos /path/to/output

The script skips files that already have a corresponding WAV.
"""
import os
import subprocess
import sys
from pathlib import Path


def convert_all(src_dir: str, dst_dir: str) -> None:
    src = Path(src_dir).resolve()
    dst = Path(dst_dir).resolve()
    total = 0
    ok = 0
    skipped = 0
    failed = 0

    for mp4 in sorted(src.rglob("*.mp4")):
        total += 1
        rel = mp4.relative_to(src)
        wav = dst / rel.with_suffix(".wav")

        if wav.exists():
            print(f"  SKIP: {rel}")
            skipped += 1
            continue

        wav.parent.mkdir(parents=True, exist_ok=True)
        print(f"  CONV: {rel} ...", end=" ", flush=True)

        result = subprocess.run(
            [
                "ffmpeg",
                "-i", str(mp4),
                "-vn",
                "-acodec", "pcm_s16le",
                "-ar", "16000",
                "-ac", "1",
                str(wav),
                "-y",
                "-loglevel", "error",
            ],
            capture_output=True,
            text=True,
        )

        if wav.exists() and wav.stat().st_size > 0:
            size_mb = wav.stat().st_size / (1024 * 1024)
            print(f"OK ({size_mb:.1f} MB)")
            ok += 1
        else:
            print("FAILED")
            if result.stderr:
                for line in result.stderr.strip().split("\n")[-3:]:
                    print(f"    {line}")
            failed += 1

    print(f"\nDone: {total} total, {ok} OK, {skipped} skipped, {failed} failed")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python3 bulk_convert_to_wav.py <source_video_dir> <output_audio_dir>")
        sys.exit(1)
    convert_all(sys.argv[1], sys.argv[2])
