#!/bin/bash
# Останавливает Happ и Shadowrocket, гасит utun интерфейсы
# Устанавливается как launchd агент для автозапуска после ребута
#
# Установка:
#   chmod +x ~/bin/fix-network-after-reboot.sh
#   launchctl load ~/Library/LaunchAgents/com.user.fix-network.plist

/usr/sbin/scutil --nc stop "Happ" 2>/dev/null
/usr/sbin/scutil --nc stop "Shadowrocket" 2>/dev/null
sleep 2

for iface in utun0 utun1 utun2 utun3 utun4 utun5 utun9; do
  /sbin/ifconfig "$iface" down 2>/dev/null
done

if /usr/sbin/netstat -rn -f inet | grep -q "^default.*en5"; then
  echo "OK: Internet via en5 (iPhone USB)"
else
  echo "WARN: default route not via en5"
  /usr/sbin/netstat -rn -f inet | grep "^default"
fi
