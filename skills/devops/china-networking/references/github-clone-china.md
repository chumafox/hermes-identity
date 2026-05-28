# GitHub Clone from China — Practical Notes

## What Works

### Small repos (<50 files, <5MB)
Direct HTTPS with `--depth 1 --single-branch` usually works:
```bash
git clone --depth 1 --single-branch https://github.com/owner/repo.git
```

### Medium repos (50-500 files, 5-50MB)
Add `--filter=tree:0` to skip blob download during clone:
```bash
git clone --filter=tree:0 --depth 1 --single-branch https://github.com/owner/repo.git
```

### Large repos (500+ files, 50MB+)
These often timeout even with filters. Options:
1. Pre-clone on HK Mac, transfer over Type-C/Thunderbolt
2. Use `aria2c` with resume for the zip archive
3. Try Gitee mirror first

## Parallel Cloning for Batches

When cloning 5-15 small repos, launch all in parallel:
```bash
for repo in "owner/repo1" "owner/repo2"; do
  git clone --depth 1 --single-branch "https://github.com/$repo.git" &
done
wait
```

Or via Hermes background processes for monitoring.

## Common Errors

| Error | Meaning | Fix |
|-------|---------|-----|
| `RPC failed; curl 18 transfer closed` | Connection dropped mid-pack | Retry with `--filter=tree:0` |
| `early EOF` | Pack too large for unstable connection | Use shallower clone or pre-download |
| `invalid index-pack output` | Corrupted pack stream | `rm -rf repo` and retry |
| `Could not resolve host` | DNS blocked | Try direct IP or different DNS |

## What Does NOT Work

- Mirror proxies (ghp.ci, gitclone.com, mirror.ghproxy.com) — SSL errors or timeouts for large repos
- SSH on port 22 — blocked by some carriers
- `--depth 1` alone without `--filter` for repos >1000 files

## SeamlessM4T Projects Batch Clone (Example)

Repos cloned successfully in one session (all small-medium):
- TTS-WebUI (3142★, ~500MB) — succeeded with `--filter=tree:0 --depth=1`
- NeuroSandboxWebUI (106★) — succeeded in parallel
- SeamlessM4TApp (57★) — succeeded
- Fast-SeamlessM4T-ONNX (43★) — succeeded
- SeamlessM4t-Translator (13★) — succeeded
- seamlessly (10★) — succeeded
- AutoTranslate (9★) — succeeded
- SeamlessM4T-finetune (4★) — succeeded
- SeamlessM4Tv2-API (4★) — succeeded

All cloned to `~/shelf/seamlessm4t-projects/`.
