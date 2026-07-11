---
name: hermes-config-auxiliary
description: "Configure Hermes auxiliary features (title generation, vision, TTS, triage) when the primary provider has a non-standard API endpoint. Fixes 'HTTP 404' on title_generation and other aux tasks."
version: 1.0.0
created_by: agent
---

# Hermes Config: Auxiliary Provider Routing

## Problem

When using a custom provider with a **non-standard API endpoint** (e.g.
Volc Coding at `https://ark.cn-beijing.volces.com/api/coding/v3/v1` instead
of the standard `/v1/chat/completions`), Hermes auxiliary features that use
`provider: auto` inherit the same base URL and fail with HTTP 404.

Affected aux features:
- `title_generation` — fails on model switch: `⚠ Auxiliary title generation failed: HTTP 404`
- `auxiliary.vision` — likely fails
- `auxiliary.tts_audio_tags` — likely fails
- `auxiliary.triage_specifier` — likely fails

## Root Cause: `DEEPSEEK_API_KEY` is actually an ark-key

The most common hidden cause: `DEEPSEEK_API_KEY` contains a Volcengine ark-key
(prefix `ark-...`) instead of a real DeepSeek API key (prefix `sk-...`). When
auxiliary tasks are set to `provider: deepseek`, Hermes sends requests to
`https://api.deepseek.com/v1` with an ark-key → 404.

**Check:**
```bash
grep 'DEEPSEEK_API_KEY' ~/.hermes/.env
# If it starts with 'ark-' — this is the problem
```

## Fix A: Explicit provider (real DeepSeek key available)

Explicitly set a standard API provider for each failing aux feature:

```bash
hermes config set title_generation.provider deepseek
hermes config set title_generation.model deepseek-chat
```

For other aux features as needed:
```bash
hermes config set auxiliary.vision.provider deepseek
hermes config set auxiliary.tts_audio_tags.provider deepseek
hermes config set auxiliary.triage_specifier.provider deepseek
```

**Must verify `DEEPSEEK_API_KEY` is a real sk-key, not an ark-key!**
If the key is `ark-...`, use Fix B or Fix C instead.

## Fix B: Use deepseek-fallback custom provider

If the real DeepSeek key is in `DEEPSEEK_FALLBACK_API_KEY`:

```bash
hermes config set title_generation.provider custom:deepseek-fallback
hermes config set title_generation.model deepseek-chat
```

This routes aux requests through the fallback provider which has a valid
sk-key. For other aux features, set the same way.

## Fix C: Disable title generation entirely (quick workaround)

When neither Fix A nor Fix B works because of proxy/key conflicts:

Use `hermes config edit` to set the provider and model to empty strings:
```yaml
# In the auxiliary section:
  title_generation:
    provider: ''
    model: ''
    base_url: ''
    api_key: ''
    timeout: 30
```

Or edit in-place with sed:
```bash
sed -i '' 's/    provider: deepseek/    provider:/' ~/.hermes/config.yaml
sed -i '' "s/    model: deepseek-chat/    model:/" ~/.hermes/config.yaml
```

With empty provider+model, Hermes skips the aux request entirely — no
warning, no error. Session titles come from the first user message.

## Pitfall: Duplicate Entries in config.yaml

`hermes config set` creates a **new top-level entry** in `config.yaml`. It
does NOT remove any existing `title_generation:` block that may already exist
inside the `agent:` section or a profile section. This creates a duplicate
that Hermes ignores (reads the first one, usually the old `auto` value).

**After every `hermes config set` on aux features, verify:**

```bash
grep -n 'title_generation' ~/.hermes/config.yaml
```

If two blocks exist, the first one is the active one. To fix:

1. Note the line numbers of both blocks
2. The second (duplicate) block is at a higher line number
3. Find its exact extent (3-4 lines including indented content)
4. Delete with sed:
```bash
sed -i '' '612,614d' ~/.hermes/config.yaml
```

Then verify the original block has the correct values:
```bash
grep -A 5 'title_generation' ~/.hermes/config.yaml | head -8
# Should show: provider: deepseek, model: deepseek-chat
```

Or directly edit the original block with sed instead of adding a dupe:
```bash
sed -i '' 's/    provider: auto/    provider: deepseek/' ~/.hermes/config.yaml
sed -i '' "s/    model: ''/    model: deepseek-chat/" ~/.hermes/config.yaml
```

## Prevention

Before running `hermes config set` on any aux feature, check if it already
exists in config.yaml. If it does, use `sed` to edit in place instead.

## Verification

After fixing, switch models or create a new session:
```
/model deepseek-v4-flash-260425
```
The `⚠ Auxiliary title generation failed` warning should no longer appear.
