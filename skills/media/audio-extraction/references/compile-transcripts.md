# Compiling Multiple Transcripts into One Document

After transcribing a set of lecture videos into individual .md files (one per lecture with Obsidian frontmatter), you may want to combine them into a single compiled reference document for easier searching and reading.

## Python Script Pattern

```python
import os, glob

AUDIO_DIR = "/path/to/audio/output"
output_path = "/path/to/compiled-course.md"

md_files = sorted(glob.glob(os.path.join(AUDIO_DIR, "**/*.md"), recursive=True))

lines = []
lines.append("---")
lines.append('title: "Course Name — Full Transcript"')
lines.append('source: "course-source"')
lines.append('created_at: "2026-05-23"')
lines.append("---")
lines.append("")
lines.append("# Course Title")
lines.append("")

current_section = None

for md_path in md_files:
    rel = os.path.relpath(md_path, AUDIO_DIR)
    parts = rel.split(os.sep)
    section_name = parts[0] if len(parts) > 1 else ""
    
    if section_name != current_section:
        current_section = section_name
        lines.append("")
        lines.append(f"## {section_name}")
        lines.append("")
    
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Strip frontmatter, keep body
    if content.startswith("---"):
        parts_split = content.split("---", 2)
        body = parts_split[2].strip() if len(parts_split) >= 3 else content
    else:
        body = content
    
    # Downgrade title level from # to ###
    if body.startswith("# "):
        first_nl = body.find("\n")
        title = body[:first_nl]
        rest = body[first_nl:].strip()
        lines.append(f"### {title[2:]}")
        lines.append("")
        if rest:
            lines.append(rest)
            lines.append("")
    
    lines.append("---")
    lines.append("")

with open(output_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
```

## Structure

The compiled document uses Obsidian-compatible frontmatter and hierarchical headings:

- `#` — course title (top)
- `##` — section/module name (from folder names like "01 - Nutrition")
- `###` — individual lecture title (from each .md file)
- `---` — separator between lectures

## Skipping Already-Compiled Files

The script re-reads existing .md files rather than re-transcribing. Run it anytime after transcription to regenerate the compiled doc.
