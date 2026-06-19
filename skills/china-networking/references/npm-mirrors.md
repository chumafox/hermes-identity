# npm Mirror Setup (China)

## Primary Mirror

```bash
# Single install with npmmirror
npm install -g <package> --registry=https://registry.npmmirror.com

# Persist mirror for the session
npm config set registry https://registry.npmmirror.com

# Or use ~/.npmrc
echo "registry=https://registry.npmmirror.com" >> ~/.npmrc
```

## Global Install Fix (macOS EACCES)

When `npm install -g` fails with `EACCES: permission denied`:

```bash
sudo npm install -g <package> --registry=https://registry.npmmirror.com
```

Or fix npm prefix permanently:

```bash
mkdir ~/.npm-global
npm config set prefix ~/.npm-global
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.zshrc
```

## Node.js Version Check

Always check before installing packages that have strict `engines.node` requirements:

```bash
node --version
# If nvm is installed:
source ~/.nvm/nvm.sh && nvm ls
# Install a specific version:
nvm install <version>
nvm use <version>
```

However, nvm downloads from `nodejs.org` which may be slow in China. The system-installed Node (from brew or official pkg) is usually sufficient even with minor version mismatch — most packages work with just a warning.

## wechat-tui (Пример)

```bash
# Node >=22.19.0 требуется, но 22.16.0 работает (только warning)
sudo npm install -g wechat-tui --registry=https://registry.npmmirror.com

# Запуск
wechat-tui
```
