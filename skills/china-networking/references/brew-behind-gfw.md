# Brew behind GFW

When `brew install` times out or fails with SSL errors, the package server (ghcr.io) is blocked.

## Option 1: Through local tunnel

If Internet Pro (or any HTTP proxy) is active:

```bash
HTTPS_PROXY=http://127.0.0.1:8888 brew install <package>
```

This routes brew's download through the HTTP bridge on the display Mac.

## Option 2: rsync Cellar from pro

If the target machine has no tunnel but pro can access brew:

```bash
# On pro (has internet):
brew install <package>

# On dispo (no internet):
rsync -avz -e "ssh -i ~/.ssh/id_ed25519_headless" \
  admin@192.168.103.70:/opt/homebrew/Cellar/<pkg>/ \
  /opt/homebrew/Cellar/<pkg>/
brew link --overwrite <package>
```

Works for any brew package. The `-a` flag preserves library links, and `brew link` creates the symlinks.

Check dependencies with:
```bash
ssh admin-remote "otool -L /opt/homebrew/bin/<binary> | grep homebrew"
# Copy each dependency's Cellar.
```

## Option 3: ghcr mirror (if available)

```bash
export HOMEBREW_BREW_GIT_REMOTE="https://mirrors.tuna.tsinghua.edu.cn/git/homebrew/brew.git"
export HOMEBREW_CORE_GIT_REMOTE="https://mirrors.tuna.tsinghua.edu.cn/git/homebrew/homebrew-core.git"
```

Not always reliable for bottle downloads — bottles are on ghcr.io.
