# Create the identity sync cron job

```
hermes cron create "0 4 * * *" \
  --name "identity-sync" \
  --prompt "Обнови файлы identity в ~/hermes-identity/:
1. memory-backup.md — скопировать свежий дамп памяти (пользователь, железо, проекты)
2. AGENTS.md — скопировать из ~/.hermes/AGENTS.md
3. skills/ — скопировать новые/изменённые skills из ~/.hermes/skills/
4. soul.md — проверить, не устарели ли принципы
Затем: cd ~/hermes-identity && git add -A && git commit -m \"auto-update \$(date +%Y-%m-%d)\" && git push 2>&1 || echo \"push failed\""
```

To check status: `hermes cron list`
To run immediately: `hermes cron run identity-sync`
