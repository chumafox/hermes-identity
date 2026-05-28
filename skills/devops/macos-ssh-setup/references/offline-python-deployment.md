# Offline Python Deployment Between Macs

Pattern for transferring Python applications to a Mac with restricted/no internet.

## Step 1: Bundle on Source (with internet)
```bash
BUNDLE=/tmp/hermes_bundle
mkdir -p $BUNDLE

# Clone/copy application code
git clone --depth 1 https://github.com/org/repo.git /tmp/repo-src
cp -R /tmp/repo-src $BUNDLE/app

# Copy portable Python (RESOLVE SYMLINKS!)
cp -RL ~/.local/share/uv/python/cpython-3.11-macos-aarch64-none $BUNDLE/python

# Copy uv binary
cp ~/.local/bin/uv $BUNDLE/

# Copy pre-built venv (has all dependencies)
cp -R ~/.hermes/app/venv $BUNDLE/venv
```

## Step 2: Transfer
```bash
# Option A: SCP
scp -i key /tmp/bundle.tar.gz admin@target:/tmp/

# Option B: HTTP server (no scp approval needed)
# On source: python3 -m http.server 8080
# On target: curl -o /tmp/bundle.tar.gz http://SOURCE_IP:8080/bundle.tar.gz
```

## Step 3: Install on Target
```bash
cd /tmp && tar xzf bundle.tar.gz

# Place code
cp -R bundle/app ~/.hermes/app

# Place venv
cp -R bundle/venv ~/.hermes/app/venv

# Fix shebangs (source username → target username)
find ~/.hermes/app/venv/bin -type f -exec \
  sed -i '' 's|/Users/SOURCE_USER/|/Users/TARGET_USER/|g' {} \;

# Fix editable install paths
find ~/.hermes/app/venv/lib -name "__editable___*.py" -exec \
  sed -i '' 's|/Users/SOURCE_USER/.hermes|/Users/TARGET_USER/.hermes|g' {} \;

# Create wrapper
cat > /usr/local/bin/app-cli << 'EOF'
#!/bin/bash
export PATH="/tmp/bundle/python/bin:$PATH"
exec /Users/TARGET_USER/.hermes/app/venv/bin/cli "$@"
EOF
chmod +x /usr/local/bin/app-cli
```

## Critical Rules
1. **`cp -RL`** for Python directory — resolves symlinks to real files. Without `-L`, `python/bin/python3` becomes a broken symlink
2. **Edit `__editable___*.py`** — these files contain absolute source paths that break after transfer
3. **`~/.zshenv`** for PATH — non-interactive SSH reads `.zshenv`, not `.zshrc`
4. **Match architecture** — ARM64 Python for M1/M2/M3, x86_64 for Intel
