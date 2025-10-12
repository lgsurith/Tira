#!/bin/bash

# Script to create a room with Auto Egress configuration
# This is the CORRECT way to implement Auto Egress according to LiveKit docs

ROOM_NAME=${1:-"auto-recording-test-$(date +%s)"}
PHONE_NUMBER=${2:-"+919962461579"}

echo "Creating room with Auto Egress: $ROOM_NAME"

# Step 1: Create room with egress configuration
curl -X POST "https://voiceagent-k30eze42.livekit.cloud/twirp/livekit.RoomService/CreateRoom" \
  -H "Authorization: Bearer $(echo -n 'APIwePTs7c8bxGq:5eFJ7nZOSqadUrpND9KFenxwadDQqCUAqqt5i7CZBr9' | base64)" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "'$ROOM_NAME'",
    "max_participants": 5,
    "egress": {
      "room_composite": {
        "file": {
          "filepath": "recordings/'$ROOM_NAME'-{time}.mp4"
        }
      }
    }
  }' | jq '.'

echo ""
echo "Room created! Now dispatching agent..."
echo ""

# Step 2: Dispatch agent to the room
curl -X POST "https://voiceagent-k30eze42.livekit.cloud/twirp/livekit.AgentService/DispatchJob" \
  -H "Authorization: Bearer $(echo -n 'APIwePTs7c8bxGq:5eFJ7nZOSqadUrpND9KFenxwadDQqCUAqqt5i7CZBr9' | base64)" \
  -H "Content-Type: application/json" \
  -d '{
    "job": {
      "type": "agent",
      "agent_name": "riverline-agent",
      "room": "'$ROOM_NAME'",
      "metadata": "{\"phone_number\": \"'$PHONE_NUMBER'\"}"
    }
  }' | jq '.'

echo ""
echo "✅ Room created with Auto Egress: $ROOM_NAME"
echo "📞 Calling: $PHONE_NUMBER"
echo "🎬 Recording will start automatically when participants join"
echo ""
echo "To check egress status:"
echo "  ./scripts/list_egress.sh $ROOM_NAME"
