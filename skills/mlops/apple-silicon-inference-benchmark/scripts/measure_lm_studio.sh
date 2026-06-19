#!/usr/bin/env bash
# Замер скорости модели через LM Studio API
# Использование: ./measure_lm_studio.sh <model_name> [prompt] [max_tokens]
set -e

MODEL="${1:-qwen2.5-3b-instruct}"
PROMPT="${2:-Напиши одно предложение про искусственный интеллект.}"
MAX_TOKENS="${3:-50}"

START=$(date +%s%N)

RESPONSE=$(curl -s -X POST http://localhost:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"$MODEL\",
    \"messages\": [{\"role\": \"user\", \"content\": \"$PROMPT\"}],
    \"max_tokens\": $MAX_TOKENS,
    \"temperature\": 0,
    \"stream\": false
  }")

ELAPSED=$(echo "($(date +%s%N) - $START) / 1000000000" | bc -l)

TOKENS=$(echo "$RESPONSE" | python3 -c "import json,sys; print(json.load(sys.stdin)['usage']['completion_tokens'])" 2>/dev/null)
TEXT=$(echo "$RESPONSE" | python3 -c "import json,sys; print(json.load(sys.stdin)['choices'][0]['message']['content'])" 2>/dev/null)
TOK_S=$(echo "scale=1; $TOKENS / $ELAPSED" | bc -l 2>/dev/null || echo "?")

echo "model: $MODEL"
echo "tok/s: $TOK_S"
echo "time: ${ELAPSED}s"
echo "tokens: $TOKENS"
echo "response: ${TEXT:0:150}"
