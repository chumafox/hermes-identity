# networksetup CLI — Output Parsing Pitfalls

## The Bug: `"Enabled:" in line` Matches Wrong Line

`networksetup -getsocksfirewallproxy <service>` returns 4 lines:

```
Enabled: Yes
Server: 127.0.0.1
Port: 1080
Authenticated Proxy Enabled: 0
```

**WRONG:** `if "Enabled:" in line:` matches BOTH line 1 AND line 4 (the last line contains `"Enabled:"` in `"Authenticated Proxy Enabled: 0"`), overwriting the correct value with `False`.

**FIX:** Use `line.startswith("Enabled:")` instead.

Applies to all: `-getsocksfirewallproxy`, `-getwebproxy`, `-getsecurewebproxy`.
