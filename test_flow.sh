#!/bin/bash

echo "=========================================="
echo "Testing Complete Game Flow"
echo "=========================================="

echo ""
echo "1. Testing health endpoint..."
curl -s http://localhost:8050/health | jq .
echo ""

echo "2. Creating Alias room with custom settings..."
RESPONSE=$(curl -s -X POST "http://localhost:8050/rooms/create?mode=alias&timed_mode=true&round_time=60&difficulty=medium&language=en")
echo $RESPONSE | jq .
ROOM_CODE=$(echo $RESPONSE | jq -r .room_code)
echo "Created room: $ROOM_CODE"
echo ""

echo "3. Getting room info..."
curl -s "http://localhost:8050/rooms/$ROOM_CODE" | jq .
echo ""

echo "4. Testing Frontend is running..."
curl -s -I http://localhost:3050 | head -5
echo ""

echo "=========================================="
echo "All tests completed!"
echo "=========================================="
echo ""
echo "Frontend: http://localhost:3050"
echo "Backend API: http://localhost:8050"
echo "API Docs: http://localhost:8050/docs"
echo "Room Code: $ROOM_CODE"
