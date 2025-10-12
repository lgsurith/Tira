#!/bin/bash

# Simple test script for Auto Egress without jq dependency

echo "🧪 Testing Auto Egress Implementation"
echo "===================================="

ROOM_NAME="test-egress-$(date +%s)"
PHONE_NUMBER="+919962461579"

echo "📋 Test Details:"
echo "  Room: $ROOM_NAME"
echo "  Phone: $PHONE_NUMBER"
echo ""

# Test 1: Create room with egress
echo "🏗️  Step 1: Creating room with Auto Egress..."
ROOM_RESPONSE=$(curl -s -X POST "https://voiceagent-k30eze42.livekit.cloud/twirp/livekit.RoomService/CreateRoom" \
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
  }')

echo "Room Creation Response:"
echo "$ROOM_RESPONSE"
echo ""

# Test 2: Dispatch agent
echo "🤖 Step 2: Dispatching agent..."
DISPATCH_RESPONSE=$(curl -s -X POST "https://voiceagent-k30eze42.livekit.cloud/twirp/livekit.AgentService/DispatchJob" \
  -H "Authorization: Bearer $(echo -n 'APIwePTs7c8bxGq:5eFJ7nZOSqadUrpND9KFenxwadDQqCUAqqt5i7CZBr9' | base64)" \
  -H "Content-Type: application/json" \
  -d '{
    "job": {
      "type": "agent",
      "agent_name": "riverline-agent",
      "room": "'$ROOM_NAME'",
      "metadata": "{\"phone_number\": \"'$PHONE_NUMBER'\"}"
    }
  }')

echo "Agent Dispatch Response:"
echo "$DISPATCH_RESPONSE"
echo ""

# Test 3: Check egress status
echo "🎬 Step 3: Checking egress status..."
EGRESS_RESPONSE=$(curl -s -X POST "https://voiceagent-k30eze42.livekit.cloud/twirp/livekit.Egress/ListEgress" \
  -H "Authorization: Bearer $(echo -n 'APIwePTs7c8bxGq:5eFJ7nZOSqadUrpND9KFenxwadDQqCUAqqt5i7CZBr9' | base64)" \
  -H "Content-Type: application/json" \
  -d '{"room_name":"'$ROOM_NAME'"}')

echo "Egress Status Response:"
echo "$EGRESS_RESPONSE"
echo ""

echo "✅ Test completed!"
echo ""
echo "📋 Summary:"
echo "  Room: $ROOM_NAME"
echo "  Expected Recording: recordings/$ROOM_NAME-{timestamp}.mp4"
echo ""
echo "🔍 What to look for:"
echo "  ✅ Room creation should return room details"
echo "  ✅ Agent dispatch should return job details"  
echo "  ✅ Egress list should show active recording with status 'EGRESS_ACTIVE'"
echo ""
echo "📞 If successful, you should receive a call at: $PHONE_NUMBER"
