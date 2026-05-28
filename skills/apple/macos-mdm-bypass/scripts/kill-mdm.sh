#!/bin/bash
# Kill MDM/DEP enrollment processes on macOS
# Use standalone:   ssh user@mac 'sudo bash /usr/local/bin/kill-mdm.sh'
# Use as watchdog:  see templates/com.user.kill-mdm.plist
exec 2>/dev/null
pkill -9 -f "mdmclient"
pkill -9 -f "Setup Assistant"
