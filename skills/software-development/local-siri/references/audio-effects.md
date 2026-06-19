# Audio Effects for Silero TTS

Все эффекты применяются через ffmpeg после синтеза Silero TTS.

## Pitch Down (approved)

```bash
ffmpeg -y -i input.wav \
  -af "asetrate=48000*0.85,aresample=48000,atempo=1.176" \
  output.wav
```

pitch 0.85 = approved by user. pitch 0.8 tested (too low). pitch 0.75 (too low + slow speech).

## Robot Voice (tested, not approved)

### Type 1: Vibrato + pitch up
```bash
ffmpeg -y -i input.wav \
  -af "vibrato=f=8:d=0.2,asetrate=44100*1.2,aresample=44100,volume=1.5" \
  output.wav
```

### Type 2: Deep robot (pitch down + vibrato)
```bash
ffmpeg -y -i input.wav \
  -af "asetrate=44100*0.75,aresample=44100,atempo=1.33,vibrato=f=5:d=0.2,volume=1.5" \
  output.wav
```

### Type 3: Classic robot (vibrato + phaser)
```bash
ffmpeg -y -i input.wav \
  -af "vibrato=f=10:d=0.1,aphaser=in_gain=0.7:out_gain=0.8:delay=5:decay=0.7:speed=0.5" \
  output.wav
```

Note: aphaser `type` parameter is NOT supported (causes "Invalid argument" error).

## Important Notes

- pitch < 0.8 sounds too low AND makes speech slower (atempo compensation is imperfect)
- pitch < 0.7 = "монстр", user rejected
- vibrato without pitch change = chill robot, user rejected
- User's final preference: **clean pitch-down female voice** (xenia, pitch 0.85), no robot effects
