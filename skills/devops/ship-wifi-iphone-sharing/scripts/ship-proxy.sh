#!/bin/bash
# ship-proxy.sh — Включить/выключить HTTP прокси на экранном Mac
# Весь трафик экранного Mac пойдёт через безголовый (ZTE 4G/5G интернет)
# 
# Установка: поместить на экранный Mac, chmod +x
# Использование:
#   ./ship-proxy.sh on     — включить прокси (трафик через ZTE)
#   ./ship-proxy.sh off    — выключить прокси (прямой WiFi корабля)
#   ./ship-proxy.sh status — показать состояние

PROXY_HOST="192.168.103.70"
PROXY_PORT="8888"
SERVICE="Wi-Fi"

case "${1:-status}" in
  on)
    echo "Включаю HTTP прокси ${PROXY_HOST}:${PROXY_PORT}..."
    sudo networksetup -setwebproxy "$SERVICE" $PROXY_HOST $PROXY_PORT
    sudo networksetup -setwebproxystate "$SERVICE" on
    sudo networksetup -setsecurewebproxy "$SERVICE" $PROXY_HOST $PROXY_PORT
    sudo networksetup -setsecurewebproxystate "$SERVICE" on
    echo "Готово. Весь трафик через безголовый Mac (ZTE)."
    echo "Проверка: curl -4 -s ifconfig.me"
    echo "Должен показать ZTE IP (123.147.x.x)"
    ;;
  off)
    echo "Выключаю прокси..."
    sudo networksetup -setwebproxystate "$SERVICE" off
    sudo networksetup -setsecurewebproxystate "$SERVICE" off
    echo "Готово. Прямой WiFi корабля."
    echo "Проверка: curl -4 -s ifconfig.me"
    echo "Должен показать IP WiFi корабля (106.85.x.x)"
    ;;
  status)
    echo "=== HTTP Proxy ==="
    networksetup -getwebproxy "$SERVICE"
    echo "=== HTTPS Proxy ==="
    networksetup -getsecurewebproxy "$SERVICE"
    echo "=== Внешний IP ==="
    ip=$(curl -4 -s --max-time 5 ifconfig.me 2>/dev/null || echo "нет ответа")
    echo "$ip"
    ;;
  *)
    echo "Использование: $0 {on|off|status}"
    exit 1
    ;;
esac
