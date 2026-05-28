#!/bin/bash
# tcc-copy.sh - Copy files from TCC-protected directories via GUI Terminal
#
# Usage: ./tcc-copy.sh <source> <destination>
# Example: ./tcc-copy.sh ~/Documents/Project /tmp/project_copy
#
# macOS 15+ blocks even root from reading ~/Documents over SSH.
# This script launches cp via the GUI Terminal.app which has FDA.

SRC="$1"
DST="$2"

if [ -z "$SRC" ] || [ -z "$DST" ]; then
    echo "Usage: $0 <source> <destination>"
    echo "Copies files from TCC-protected dirs (like ~/Documents) via GUI Terminal"
    exit 1
fi

SCRIPT="/tmp/tcc_copy_$$.sh"
cat > "$SCRIPT" << EOF
#!/bin/bash
cp -R "$SRC" "$DST" 2>/tmp/tcc_copy_error_$$.log
echo \$? > /tmp/tcc_copy_exit_$$.log
chmod -R 755 "$DST" 2>/dev/null
EOF

chmod +x "$SCRIPT"
open -a Terminal "$SCRIPT"

echo "Launched Terminal for copy. Waiting..."
sleep 5

if [ -f "/tmp/tcc_copy_exit_$$.log" ]; then
    EXIT_CODE=$(cat "/tmp/tcc_copy_exit_$$.log")
    if [ "$EXIT_CODE" = "0" ]; then
        echo "Done. Files at: $DST"
    else
        echo "Error (exit $EXIT_CODE):"
        cat "/tmp/tcc_copy_error_$$.log"
    fi
else
    echo "Copy may still be running. Check: $DST"
fi

rm -f "$SCRIPT" "/tmp/tcc_copy_exit_$$.log" "/tmp/tcc_copy_error_$$.log"
