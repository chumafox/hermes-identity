#!/bin/bash
# doubao-inject — Inject audio into Doubao voice chat via BlackHole
# Installed at ~/bin/doubao-inject
#
# Usage:
#   doubao-inject start          — switch to BlackHole, open voice, inject tone
#   doubao-inject stop           — close voice, switch back to mic
#   doubao-inject speak <file>   — play audio file into BlackHole
#   doubao-inject tts <text>     — TTS + inject into BlackHole
#   doubao-inject toggle         — just toggle audio input device
#   doubao-inject read           — read voice chat transcript
#   doubao-inject status         — show current state

CDP_PORT=9223
SWITCH="/opt/homebrew/bin/SwitchAudioSource"

get_voice_ws() {
  curl -s http://127.0.0.1:$CDP_PORT/json 2>/dev/null | python3 -c "
import sys,json
for t in json.load(sys.stdin):
    if 'voice' in t.get('url',''):
        print(t.get('webSocketDebuggerUrl',''))
" 2>/dev/null
}

get_page_ws() {
  local filter="$1"
  curl -s http://127.0.0.1:$CDP_PORT/json 2>/dev/null | python3 -c "
import sys,json
for t in json.load(sys.stdin):
    if '$filter' in t.get('url','').lower():
        print(t.get('webSocketDebuggerUrl',''))
" 2>/dev/null
}

open_voice_chat() {
  local launcher_ws=$(get_page_ws "launcher")
  [ -z "$launcher_ws" ] && { echo "Launcher page not found"; return 1; }
  python3 << PYEOF
import asyncio, json, websockets
async def main():
    async with websockets.connect("$launcher_ws", max_size=1000000) as ws:
        for ev in ['mousePressed','mouseReleased']:
            await ws.send(json.dumps({'id':1,'method':'Input.dispatchMouseEvent','params':{'type':ev,'x':341,'y':25,'button':'left','clickCount':1}}))
            await asyncio.sleep(0.1)
        print('Phone button clicked')
asyncio.run(main())
PYEOF
}

close_voice_chat() {
  local voice_ws=$(get_voice_ws)
  [ -z "$voice_ws" ] && return 0
  python3 << PYEOF
import asyncio, json, websockets
async def main():
    async with websockets.connect("$voice_ws", max_size=1000000) as ws:
        for ev in ['mousePressed','mouseReleased']:
            await ws.send(json.dumps({'id':1,'method':'Input.dispatchMouseEvent','params':{'type':ev,'x':140,'y':241,'button':'left','clickCount':1}}))
            await asyncio.sleep(0.1)
        print('Voice chat closed')
asyncio.run(main())
PYEOF
}

inject_audio() {
  local file="$1"
  ffmpeg -i "$file" -f audiotoolbox -audio_device_index 0 "" 2>/dev/null &
  echo $!
}

get_voice_text() {
  local voice_ws=$(get_voice_ws)
  [ -z "$voice_ws" ] && { echo "Voice chat not active"; return 1; }
  python3 << PYEOF
import asyncio, json, websockets
async def main():
    async with websockets.connect("$voice_ws", max_size=1000000) as ws:
        req = json.dumps({'id':1,'method':'Runtime.evaluate','params':{'expression':'document.body.innerText','returnByValue':True}})
        await ws.send(req)
        resp = json.loads(await asyncio.wait_for(ws.recv(),5))
        print(resp.get('result',{}).get('result',{}).get('value',''))
asyncio.run(main())
PYEOF
}

case "${1:-}" in
  start)
    echo "1. Switching to BlackHole..."
    $SWITCH -s "BlackHole 2ch" -t input 2>/dev/null
    echo "2. Opening voice chat..."
    close_voice_chat
    sleep 1
    open_voice_chat
    sleep 3
    voice_ws=$(get_voice_ws)
    if [ -n "$voice_ws" ]; then
      echo "3. Voice chat ready"
      echo "4. To inject: doubao-inject speak <file>"
      echo "5. To read:  doubao-inject read"
    else
      echo "Voice chat didn't open"
    fi
    ;;
  stop)
    echo "Closing voice chat..."
    close_voice_chat
    sleep 1
    echo "Switching back to mic..."
    $SWITCH -s "MacBook Air Microphone" -t input 2>/dev/null
    echo "Done"
    ;;
  speak)
    shift
    inject_audio "$1"
    ;;
  tts)
    shift
    text="$*"
    tmpfile=$(mktemp /tmp/doubao_tts_XXXXXX.aiff)
    say -o "$tmpfile" "$text"
    inject_audio "$tmpfile"
    echo "Playing TTS: $text"
    sleep 1
    rm -f "$tmpfile"
    ;;
  toggle)
    $SWITCH -n -t input 2>/dev/null
    echo "Current:"
    $SWITCH -c -t input
    ;;
  read)
    get_voice_text
    ;;
  status)
    echo "=== Audio Device ==="
    $SWITCH -c -t input
    echo "=== Voice Chat ==="
    voice_ws=$(get_voice_ws)
    if [ -n "$voice_ws" ]; then
      echo "ACTIVE"
    else
      echo "CLOSED"
    fi
    echo "=== CDP Pages ==="
    curl -s http://127.0.0.1:$CDP_PORT/json 2>/dev/null | python3 -c "
import sys,json
for t in json.load(sys.stdin):
    print(f'  {t[\"title\"][:30]} | {t[\"url\"][:60]}')
" 2>/dev/null
    ;;
  *)
    echo "Usage: doubao-inject {start|stop|speak <file>|tts <text>|toggle|read|status}"
    ;;
esac
