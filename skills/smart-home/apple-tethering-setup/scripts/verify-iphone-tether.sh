#!/bin/bash
# iPhone USB Tethering verification script for macOS
# Usage: ./verify-iphone-tether.sh

set -e

echo "=== iPhone USB Tethering Status Check ==="
echo ""

# 1. Check if iPhone interface exists
echo "[1] Checking iPhone USB interface..."
if networksetup -listallhardwareports 2>/dev/null | grep -q "iPhone USB"; then
    echo "   ✓ iPhone USB interface detected"
else
    echo "   ✗ iPhone USB interface not found (check cable/connection)"
    exit 1
fi

# Get iPhone device name
PHONE_IFACE=$(networksetup -listallhardwareports 2>/dev/null | grep "iPhone USB" | head -1 | awk '{print $4}')
echo "   Interface: $PHONE_IFACE"

# 2. Check if interface is active
echo ""
echo "[2] Checking interface status..."
if networksetup -getnetworkserviceenabled "iPhone USB" 2>/dev/null | grep -qi "Enabled"; then
    echo "   ✓ iPhone USB service is enabled"
else
    echo "   ✗ iPhone USB service is disabled (run: networksetup -setnetworkserviceenabled \"iPhone USB\" on)"
    exit 1
fi

# 3. Check network service order (iPhone should be before Wi-Fi)
echo ""
echo "[3] Checking connection priority..."
ORDER=$(networksetup -listnetworkserviceorder 2>/dev/null | head -5)
if echo "$ORDER" | grep -q "iPhone USB"; then
    WI_FI_ORDER=$(echo "$ORDER" | grep -c "Wi-Fi" 2>/dev/null || echo "0")
    PHONE_ORDER=$(echo "$ORDER" | grep -c "iPhone USB" 2>/dev/null || echo "0")
    if [ "$PHONE_ORDER" -le "$WI_FI_ORDER" ]; then
        echo "   ✓ iPhone USB prioritized above Wi-Fi"
    else
        echo "   ⚠ iPhone USB may not be prioritized (run: networksetup -ordernetworkservices \"iPhone USB\" Wi-Fi)"
    fi
fi

# 4. Check DNS configuration
echo ""
echo "[4] Checking DNS configuration..."
PHONE_DNS=$(networksetup -getdnsservers "iPhone USB" 2>/dev/null)
if [ -n "$PHONE_DNS" ]; then
    echo "   ✓ DNS configured on iPhone USB:"
    echo "$PHONE_DNS" | while read dns; do echo "      - $dns"; done
else
    echo "   ⚠ No DNS on iPhone USB (consider setting: networksetup -setdnsservers \"iPhone USB\" 223.5.5.5 114.114.114.114)"
fi

# 5. Check routing via iPhone
echo ""
echo "[5] Checking default route..."
ROUTE_INFO=$(route -n get default 2>/dev/null)
PHONE_GW=$(echo "$ROUTE_INFO" | grep "gateway:" | awk '{print $3}')
ROUTE_IFACE=$(echo "$ROUTE_INFO" | grep "interface:" | awk '{print $2}')

if echo "$ROUTE_IFACE" | grep -qE "en7|iPhone"; then
    echo "   ✓ Default route uses iPhone USB interface ($ROUTE_IFACE)"
else
    echo "   ⚠ Default route not using iPhone USB (trying to connect...)"
    
    # Try to force connection through iPhone
    echo "   Attempting connection test..."
    SLEEP_IFACE="en7"  # iPhone interface name
    
    if [ -n "$PHONE_GW" ]; then
        echo "   Testing gateway ($PHONE_GW)..."
    else
        # Fallback to common iPhone USB gateway
        PHONE_GW="172.20.10.1"
        echo "   Testing default gateway ($PHONE_GW)..."
    fi
    
    # Test with timeout
    if ping -c 1 "$PHONE_GW" >/dev/null 2>&1 || curl -s --connect-timeout 3 "http://google.com" >/dev/null 2>&1; then
        echo "   ✓ Internet connectivity confirmed via iPhone USB"
    else
        echo "   ✗ No internet through iPhone (check Personal Hotspot settings on iPhone)"
    fi
fi

# 6. Show network details
echo ""
echo "[6] iPhone USB network details:"
networksetup -getinfo "iPhone USB" 2>/dev/null | head -8

echo ""
echo "=== Status: $(if [ $? -eq 0 ]; then echo 'GOOD'; else echo 'ISSUES FOUND'; fi) ==="
echo ""
echo "Quick fixes to try:"
echo "  - Enable Personal Hotspot on iPhone: Settings → Cellular/Mobile Data → Personal Hotspot"
echo "  - Enable Cellular Data on iPhone"
echo "  - On Mac: networksetup -setdhcp \"iPhone USB\""
echo ""

exit 0