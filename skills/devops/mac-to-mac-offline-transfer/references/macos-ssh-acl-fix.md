# macOS SSH: ACL blocking authorized_keys

## Symptom
SSH public key auth fails even though:
- `authorized_keys` exists with correct permissions (600)
- `~/.ssh` has correct permissions (700)
- Public key is correct

SSH debug shows key being offered but rejected: `Permission denied (publickey)`.

## Root cause
macOS user home directories often have ACLs (Access Control Lists)
that SSH considers as "too permissive". If `ls -le ~` shows `drwx------+`
with a `+` sign, ACLs are present.

Common ACL: `group:everyone deny delete` on Desktop/Documents — this
is enough for SSH to reject the entire home directory path.

## Fix

```bash
# Check ACLs
ls -le ~

# Remove ALL ACLs from home directory
sudo chmod -N /Users/<username>

# Also fix .ssh directory
sudo chmod -N /Users/<username>/.ssh

# Verify no + sign
ls -ld ~  # should show drwx------ (no +)
```

## Verification

After fixing:
```bash
ssh -vvv user@host 2>&1 | grep -E "Offering|Accepted|Failed"
```

Should show `Accepted publickey` instead of silent rejection.
