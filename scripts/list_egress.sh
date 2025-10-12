#!/bin/bash

# Script to list active egress recordings for a room

ROOM_NAME=${1:-""}

if [ -z "$ROOM_NAME" ]; then
    echo "Usage: $0 <room_name>"
    echo "Example: $0 auto-recording-test-1234567890"
    exit 1
fi

echo "Listing egress for room: $ROOM_NAME"
echo ""

curl -X POST "https://voiceagent-k30eze42.livekit.cloud/twirp/livekit.Egress/ListEgress" \
  -H "Authorization: Bearer $(echo -n 'APIwePTs7c8bxGq:5eFJ7nZOSqadUrpND9KFenxwadDQqCUAqqt5i7CZBr9' | base64)" \
  -H "Content-Type: application/json" \
  -d '{"room_name":"'$ROOM_NAME'"}' | jq '.'

echo ""
echo "To stop a specific egress:"
echo "  ./scripts/stop_egress.sh <egress_id>"
