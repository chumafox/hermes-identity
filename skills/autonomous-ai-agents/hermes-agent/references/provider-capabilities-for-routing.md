# Provider Capabilities for Task Routing

## Why This Matters

Not all providers have equal tool-use competence. A model that's excellent
at codegen may refuse to SSH into a remote machine, say "this requires
manual intervention," or simply fail at multi-step terminal operations.
When routing tasks between providers, the model's _capability profile_
matters as much as its cost or speed.

## Observed Capability Profiles

### DeepSeek (V4 Flash, Chat)

| Task | Rating | Notes |
|------|--------|-------|
| SSH / remote shell | Strong | Executes SSH sequences reliably; handles sudo, copy, verify chains |
| Code generation | Good | Adequate for most tasks; weaker than Claude for complex refactoring |
| Multi-step terminal ops | Strong | Tolerates long tool-call chains |
| Chinese services | Strong | Good knowledge of Chinese mirror sites |
| Tool-use refusal rate | Low | Rarely refuses valid tool calls |

**Best for:** system administration, deployments, remote management,
pipeline orchestration.

### Kimi (kimi-coding, K2)

| Task | Rating | Notes |
|------|--------|-------|
| SSH / remote shell | Weak | Refuses with "can't do this, needs your hands" — model-level limitation, not config |
| Code generation | Strong | K2 is excellent for complex refactoring, architecture |
| Multi-step terminal ops | Weak | Struggles with long chains; may lose context |
| Chinese services | Strong | Native knowledge of Moonshot ecosystem |
| Tool-use refusal rate | Moderate | Refuses certain operations it deems "out of scope" |

**Best for:** code review, complex refactoring, architecture discussions.

**Pitfall:** if Kimi is your primary provider and you need to SSH to a remote
machine, Hermes cannot delegate automatically — Kimi won't call
`delegate_task` for SSH because it believes it can't do it. You must either:
- Use DeepSeek/Claude as primary and delegate code tasks to Kimi via
  `delegation.provider: kimi-coding`
- Or manually switch provider with `/model`

### Claude (Sonnet, Haiku)

| Task | Rating | Notes |
|------|--------|-------|
| SSH / remote shell | Strong | Reliable tool-use for terminal operations |
| Code generation | Very Strong | Best-in-class for complex code tasks |
| Multi-step terminal ops | Strong | Handles long chains well |
| Chinese services | Weak | Limited knowledge of Chinese-specific services |
| Tool-use refusal rate | Very Low | Rarely refuses |

**Best for:** complex coding, any tool-use task where availability/cost isn't
a concern.

### Gemini (Flash, Pro)

| Task | Rating | Notes |
|------|--------|-------|
| SSH / remote shell | Good | Competent, though occasionally verbose |
| Code generation | Good | Adequate |
| Multi-step terminal ops | Good | Reasonable chain tolerance |
| Chinese services | Weak | Limited Chinese-specific knowledge |
| Tool-use refusal rate | Low | Reliable |

**Best for:** general-purpose when DeepSeek is unavailable.

## Routing Decision Tree

```
Task starts
├── Need to SSH/remote shell/terminal ops?
│   ├── Primary is DeepSeek/Claude → go ahead
│   ├── Primary is Kimi → delegate to DeepSeek (`delegation.provider: deepseek`)
│   └── Primary is local/small model → delegate or spawn another agent
│
├── Need complex codegen/refactoring?
│   ├── Primary is Claude/Kimi → go ahead
│   └── Primary is DeepSeek/Gemini → delegate to Claude/Kimi
│
├── Need Chinese service access (ModelScope, Gitee)?
│   ├── Primary is Kimi/DeepSeek → go ahead
│   └── Primary is Claude/Gemini → delegate to Chinese-friendly provider
│
├── Simple query / quick answer?
│   └── Any cheap model works → keep primary, or swap to DeepSeek Flash
│
└── Task with subskills (web automation + SSH + file analysis)?
    └── Decompose into sub-tasks → delegate each to its optimal provider
```

## Automatic Routing: Simple vs Complex Tasks

**Hermes does NOT auto-classify "simple" vs "complex" tasks and route to different providers.** The model itself must recognize when a task is too complex and delegate it. This is a known limitation:

- A **weak local model** used as primary will NOT call `delegate_task` for hard problems — it doesn't know they're hard
- A **strong model** (DeepSeek, Claude) used as primary CAN delegate subtasks, but only if configured to do so via `delegation.*` in config

### The Two-Provider Model (Simple + Complex)

The closest Hermes gets to auto-routing is the **fallback model** mechanism:

```yaml
# ~/.hermes/config.yaml
model:
  provider: deepseek
  default: deepseek-v4-flash     # strong, cheap per-token

fallback_model:
  provider: openrouter
  model: anthropic/claude-sonnet-4-20250514  # strong for complex logic
```

But this only activates on **errors/rate limits** — not on task complexity. It's a failover, not a router.

### Practical Patterns for Task-Based Provider Routing

**A) Weak primary + strong fallback (not recommended):**
Gemma-4 4B as primary (fast for simple answers), fallback to DeepSeek. Problem: the weak model can't recognize when it needs to delegate. Result: it tries to answer complex questions itself and fails, or hallucinates.

**B) Smart primary + delegation (recommended):**
DeepSeek/Claude as primary, with `delegation.provider` set to another capable model for specific subtasks:
```yaml
delegation:
  provider: anthropic
  model: claude-sonnet-4-20250514
  max_iterations: 50
```
The smart primary recognizes tool-heavy subtasks and delegates them. The delegate uses a different (possibly stronger) provider.

**C) Multi-profile per workflow (most reliable):**
```bash
# Quick queries → cheap, fast
alias hfast='hermes -p quick -q'

# Heavy code → strong model
alias hcode='hermes -p coder'

# SSH/ops → reliable tool-user
alias hsys='hermes -p sysadmin'
```

**D) tmux multi-agent with provider separation:**
```bash
# Agent A: scraping agent (cheap provider)
tmux new-session -d -s scraper \
  'hermes -p quick chat -q "Scrape all product prices from example.com"'

# Agent B: analysis agent (expensive, smart provider)
tmux new-session -d -s analyzer \
  'hermes -p coder chat -q "Analyze scraped data and build a report"'
```

### Subagents with Specific Skills + Providers

You CAN create subagents with specific skills and tie them to different providers:

1. **Delegate_task** inherits parent's config by default but can override the provider:
   - This is handled automatically by Hermes when `delegation.provider` is set
   - The subagent runs with the delegated provider but the SAME toolset as the parent
   - Skills loaded in the parent context are NOT inherited by the subagent

2. **Profile-level separation** (for persistent agents):
   - Create profile A with provider X + certain skills preloaded
   - Create profile B with provider Y + different skills
   - Spawn via `hermes -p A` and `hermes -p B` in separate terminal/tmux sessions
   - Agents run independently, with their own config, skills, and provider

3. **Limited inheritance with delegate_task:**
   The subagent spawned via `delegate_task` uses:
   - Its own provider (from `delegation` config or parent's provider if unset)
   - Its own terminal session (isolated CWD)
   - The parent's toolset (can't be narrowed per-subtask)
   - Skills: only loaded if explicitly passed as context or set in config

4. **What's NOT possible:**
   - A single Hermes process cannot run TWO providers simultaneously for different sub-tasks within one turn (multi-turn via loops only)
   - `delegate_task` cannot preload different skills for different subtasks — all delegations share the same `delegation` config
   - No built-in task classifier that routes "simple question → cheap API, codegen → expensive API" automatically
   - Skills are session-level, not subagent-level — you can't attach different skill sets to different subagents within one session

## Implementation Patterns

### Profile-based separation (recommended for multi-role use)

```bash
# Create profiles with different providers
hermes profile create sysadmin --clone
# Edit ~/.hermes/profiles/sysadmin/config.yaml → DeepSeek provider

hermes profile create coder --clone
# Edit ~/.hermes/profiles/coder/config.yaml → Kimi or Claude provider

# Use via
alias hsys='hermes -p sysadmin'
alias hcode='hermes -p coder'
```

### Delegation-based separation (task-level routing)

```yaml
# ~/.hermes/config.yaml
delegation:
  provider: deepseek          # subagents use DeepSeek for SSH/ops
  model: deepseek-v4-flash
```

This works when your primary model is capable enough to call `delegate_task` —
the subagent handles the SSH work using a different provider.

### Cron-based separation (scheduled routing)

```bash
# Daily SSH health check → use DeepSeek (reliable SSH)
hermes cron create "0 6 * * *" \
  --model deepseek/deepseek-v4-flash \
  --prompt "SSH to headless-mac and run health checks"

# Weekly code review → use Kimi K2 (strong code analysis)
hermes cron create "0 10 * * 1" \
  --model kimi-coding/kimi-k2 \
  --prompt "Review open PRs in ~/projects"
```

## Evolving This Document

As you use more providers, add their profiles here. Key signals to capture:
- Provider refuses a tool call (document which tool/operation)
- Provider succeeds where others fail (document the scenario)
- Provider loses context in long chains (document chain length)
