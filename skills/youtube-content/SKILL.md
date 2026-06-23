---
name: youtube-content
description: "YouTube transcripts to summaries, threads, blogs."
tags: ["media"]
---

# YouTube Content Tool

## When to use

Use when the user shares a YouTube URL or video link, asks to summarize a video, requests a transcript, wants to download audio, or wants to extract and reformat content from any YouTube video. Transforms transcripts into structured content (chapters, summaries, threads, blog posts). Also handles audio download via yt-dlp.

## Setup

### Transcripts
Use `uv` so the dependency is installed into the same Hermes-managed environment
that runs the helper script:

```bash
uv pip install youtube-transcript-api
```

### Audio download
yt-dlp is required. Check with `which yt-dlp`. Update if old:

```bash
# Old yt-dlp (< 2026) fails with "Signature extraction failed" on YouTube
# Update via proxy if in China:
pip install --proxy socks5://127.0.0.1:1080 --upgrade yt-dlp
```

### ALL_PROXY trap (China networking)
If `ALL_PROXY=socks5://127.0.0.1:1080` is set in the environment, `pip install` will fail with `Missing dependencies for SOCKS support`. Fixes (in order of preference):

1. Use explicit `--proxy` flag: `pip install --proxy socks5://127.0.0.1:1080 ...`
2. Install pysocks first: `env -u ALL_PROXY pip install pysocks` then normal pip works
3. Unset: `env -u ALL_PROXY pip install ...`
`SKILL_DIR` is the directory containing this SKILL.md file. The script accepts any standard YouTube URL format, short links (youtu.be), shorts, embeds, live links, or a raw 11-character video ID.

```bash
# JSON output with metadata
python3 SKILL_DIR/scripts/fetch_transcript.py "https://youtube.com/watch?v=VIDEO_ID"

# Plain text (good for piping into further processing)
python3 SKILL_DIR/scripts/fetch_transcript.py "URL" --text-only

# With timestamps
python3 SKILL_DIR/scripts/fetch_transcript.py "URL" --timestamps

# Specific language with fallback chain
python3 SKILL_DIR/scripts/fetch_transcript.py "URL" --language tr,en
```

## Output Formats

After fetching the transcript, format it based on what the user asks for:

- **Chapters**: Group by topic shifts, output timestamped chapter list
- **Summary**: Concise 5-10 sentence overview of the entire video
- **Chapter summaries**: Chapters with a short paragraph summary for each
- **Thread**: Twitter/X thread format — numbered posts, each under 280 chars
- **Blog post**: Full article with title, sections, and key takeaways
- **Quotes**: Notable quotes with timestamps

### Example — Chapters Output

```
00:00 Introduction — host opens with the problem statement
03:45 Background — prior work and why existing solutions fall short
12:20 Core method — walkthrough of the proposed approach
24:10 Results — benchmark comparisons and key takeaways
31:55 Q&A — audience questions on scalability and next steps
```

## Workflow

1. **Fetch** the transcript using the helper script with `--text-only --timestamps`.
2. **Validate**: confirm the output is non-empty and in the expected language. If empty, retry without `--language` to get any available transcript. If still empty, tell the user the video likely has transcripts disabled.
3. **Chunk if needed**: if the transcript exceeds ~50K characters, split into overlapping chunks (~40K with 2K overlap) and summarize each chunk before merging.
4. **Transform** into the requested output format. If the user did not specify a format, default to a summary.
5. **Verify**: re-read the transformed output to check for coherence, correct timestamps, and completeness before presenting.

## Error Handling

- **Transcript disabled**: tell the user; suggest they check if subtitles are available on the video page.
- **Private/unavailable video**: relay the error and ask the user to verify the URL.
- **No matching language**: retry without `--language` to fetch any available transcript, then note the actual language to the user.
- **Dependency missing**: run `uv pip install youtube-transcript-api` and retry.

## China / Proxy Pitfall

YouTube is blocked in China. The `youtube-transcript-api` library uses `requests` which respects `HTTP_PROXY`/`HTTPS_PROXY` env vars. Two approaches:

**A) System proxy (inpro bridge):**
```bash
http_proxy="http://127.0.0.1:8888" https_proxy="http://127.0.0.1:8888" python3 fetch_transcript.py ...
```

**B) NO_PROXY for localhost (when using CDP/WebSocket):**
```bash
NO_PROXY="*" python3 fetch_transcript.py ...
```

If `yt-dlp` is used as fallback, it also needs proxy and may fail with "not available on this app" errors — try `youtube-transcript-api` instead.

**Verify proxy is running** before attempting: `scutil --proxy | grep HTTPEnable` should show 1.
