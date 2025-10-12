#!/bin/bash

# Auto Egress Test Script with proper credentials
# Using credentials from .env.local

echo "🧪 Testing Auto Egress Implementation"
echo "===================================="

# Load environment variables
source .env.local

ROOM_NAME="test-egress-$(date +%s)"
PHONE_NUMBER="+919962461579"

echo "📋 Test Details:"
echo "  Room: $ROOM_NAME"
echo "  Phone: $PHONE_NUMBER"
echo "  API Key: ${LIVEKIT_API_KEY:0:10}..."
echo ""

# Create proper authorization header
AUTH_HEADER="Bearer $(echo -n "${LIVEKIT_API_KEY}:${LIVEKIT_API_SECRET}" | base64)"

# Test 1: Create room with egress
echo "🏗️  Step 1: Creating room with Auto Egress..."
ROOM_RESPONSE=$(curl -s -X POST "${LIVEKIT_URL%wss*}https${LIVEKIT_URL#*wss}/twirp/livekit.RoomService/CreateRoom" \
  -H "Authorization: $AUTH_HEADER" \
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

# Check if room creation was successful
if [[ "$ROOM_RESPONSE" == *"name"* ]] && [[ "$ROOM_RESPONSE" != *"error"* ]]; then
    echo "✅ Room created successfully!"
else
    echo "❌ Room creation failed!"
    exit 1
fi

# Test 2: Dispatch agent
echo "🤖 Step 2: Dispatching agent..."
DISPATCH_RESPONSE=$(curl -s -X POST "${LIVEKIT_URL%wss*}https${LIVEKIT_URL#*wss}/twirp/livekit.AgentService/DispatchJob" \
  -H "Authorization: $AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d '{
    "job": {
      "type": "agent",
      "agent_name": "'$LIVEKIT_AGENT_NAME'",
      "room": "'$ROOM_NAME'",
      "metadata": "{\"phone_number\": \"'$PHONE_NUMBER'\"}"
    }
  }')

echo "Agent Dispatch Response:"
echo "$DISPATCH_RESPONSE"
echo ""

# Check if dispatch was successful
if [[ "$DISPATCH_RESPONSE" == *"job"* ]] && [[ "$DISPATCH_RESPONSE" != *"error"* ]]; then
    echo "✅ Agent dispatched successfully!"
else
    echo "❌ Agent dispatch failed!"
fi

# Test 3: Wait a moment for egress to start
echo "⏳ Waiting 5 seconds for egress to initialize..."
sleep 5

# Test 4: Check egress status
echo "🎬 Step 3: Checking egress status..."
EGRESS_RESPONSE=$(curl -s -X POST "${LIVEKIT_URL%wss*}https${LIVEKIT_URL#*wss}/twirp/livekit.Egress/ListEgress" \
  -H "Authorization: $AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d '{"room_name":"'$ROOM_NAME'"}')

echo "Egress Status Response:"
echo "$EGRESS_RESPONSE"
echo ""

# Analyze results
echo "📊 Test Results Analysis:"
echo "========================"

if [[ "$EGRESS_RESPONSE" == *"egress_id"* ]]; then
    echo "✅ EGRESS WORKING! Recording is active."
    
    # Extract egress ID if possible
    if command -v jq >/dev/null 2>&1; then
        EGRESS_ID=$(echo "$EGRESS_RESPONSE" | jq -r '.items[0].egress_id // empty' 2>/dev/null)
        if [[ -n "$EGRESS_ID" ]]; then
            echo "🎬 Recording ID: $EGRESS_ID"
            echo "📁 Recording File: recordings/$ROOM_NAME-{timestamp}.mp4"
        fi
    fi
elif [[ "$EGRESS_RESPONSE" == *"items"* ]]; then
    echo "⚠️  Room exists but no active egress found."
    echo "   This might mean:"
    echo "   - Egress hasn't started yet (try waiting longer)"
    echo "   - Auto Egress configuration didn't work"
    echo "   - No participants joined yet to trigger recording"
else
    echo "❌ Egress check failed or room not found."
fi

echo ""
echo "🎯 What should happen next:"
echo "1. You should receive a call at: $PHONE_NUMBER"
echo "2. Answer the call to test the agent"
echo "3. Recording should capture the entire conversation"
echo "4. When call ends, recording will be saved automatically"
echo ""
echo "🔍 To monitor the call:"
echo "  - Check agent logs in the terminal where 'uv run python src/agent.py dev' is running"
echo "  - Look for SIP participant connection messages"
echo "  - Recording will continue until call ends"
echo ""

if [[ "$EGRESS_RESPONSE" == *"egress_id"* ]] && command -v jq >/dev/null 2>&1; then
    EGRESS_ID=$(echo "$EGRESS_RESPONSE" | jq -r '.items[0].egress_id // empty' 2>/dev/null)
    if [[ -n "$EGRESS_ID" ]]; then
        echo "🛑 To stop recording manually:"
        echo "  ./scripts/stop_egress.sh $EGRESS_ID"
    fi
fi
