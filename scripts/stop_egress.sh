#!/bin/bash

# Script to stop a specific egress recording

EGRESS_ID=${1:-""}

if [ -z "$EGRESS_ID" ]; then
    echo "Usage: $0 <egress_id>"
    echo "Example: $0 EG_xxxxxxxxxxxxx"
    echo ""
    echo "To find egress IDs, use:"
    echo "  ./scripts/list_egress.sh <room_name>"
    exit 1
fi

echo "Stopping egress: $EGRESS_ID"
echo ""

curl -X POST "https://voiceagent-k30eze42.livekit.cloud/twirp/livekit.Egress/StopEgress" \
  -H "Authorization: Bearer $(echo -n 'APIwePTs7c8bxGq:5eFJ7nZOSqadUrpND9KFenxwadDQqCUAqqt5i7CZBr9' | base64)" \
  -H "Content-Type: application/json" \
  -d '{"egress_id":"'$EGRESS_ID'"}' | jq '.'

echo ""
echo "✅ Egress stop request sent for: $EGRESS_ID"
