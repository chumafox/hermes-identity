---
name: hermes-skills-deploy
description: "Deploy all Hermes skills to all CLI agents: Claude Code, Cursor, agy. Pipeline: Hermes SKILL.md -> unified skill.yaml -> agents/*.md -> symlink. OpenCode removed from deploy targets."
tags: [deploy, skills, claude, cursor, agy, pipeline, automation]
---

# Deploy Hermes skills to all CLI agents

## Quick start

```bash
cd ~/cli-common && bash deploy-skills.sh
```

## What it does

1. **convert-hermes-to-unified.py** — scan `~/.hermes/skills/*/*/SKILL.md`, generate `~/cli-common/skills/<name>/skill.yaml`
2. **convert-skills.py** — convert unified skill.yaml -> `~/cli-common/agents/<name>.md`
3. **deploy.sh** — symlink to:
   - `~/.claude/agents/` (Claude Code)
   - `~/.cursor/agents/` (Cursor)
   - `~/.config/agy/agents/` (agy, dirs only)
4. MCP and AGENTS.md also updated

## After adding/modifying a skill

```bash
cd ~/cli-common && bash deploy-skills.sh
```

## Skipped skills (Hermes-specific)

- debugging-hermes-tui-commands
- design-md
- hermes-agent-skill-authoring
- plan
- subagent-driven-development

Edit `SKIP_LIST` in `~/cli-common/convert-hermes-to-unified.py` to add/remove.

## Real-run reference

From initial mass deploy (June 2026):
- 189 SKILL.md scanned → 184 unified skill.yaml created
- 5 skipped (Hermes-specific): debugging-hermes-tui-commands, design-md, hermes-agent-skill-authoring, plan, subagent-driven-development
- 187 agents/*.md generated (184 new + 3 pre-existing: code-quality-reviewer, coder, redfin-county)
- Symlinked into Claude (187), Cursor (187), OpenCode (187, format-converted), agy (dirs created)

## Verify

```bash
echo "Unified: $(ls ~/cli-common/skills/ | wc -l)"
echo "Agents:  $(ls ~/cli-common/agents/*.md | wc -l)"
echo "Claude:  $(ls ~/.claude/agents/*.md 2>/dev/null | wc -l)"
echo "Cursor:  $(ls ~/.cursor/agents/*.md 2>/dev/null | wc -l)"
```

## Pitfalls

- **Duplicate skill names across categories**: If two skills in different categories share the same name, `convert-skills.py` overwrites the agents file. Rename or merge before deploy.
- **Root-level skills**: Skills in `~/.hermes/skills/<name>/` (no category dir) are also found. `convert-hermes-to-unified.py` scans recursively.
- **Supporting files**: `references/`, `templates/`, `scripts/`, `assets/` dirs under a Hermes skill are copied to the unified skill dir. Keep them small.
- **Hermes SKILL.md that were also deployed as agents/*.md**: `convert-skills.py` overwrites Hermes SKILL.md from unified → this is by design (unified is the source of truth now).
