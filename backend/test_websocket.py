"""
WebSocket integration test
Run: python test_websocket.py
"""
import asyncio
import websockets
import json
import requests

BASE_URL = "http://localhost:8050"
WS_URL = "ws://localhost:8050"

async def test_websocket_connection():
    """Test WebSocket connection and game flow"""
    print("=" * 50)
    print("Testing WebSocket Game Flow")
    print("=" * 50)
    
    # 1. Create room
    print("\n1. Creating room...")
    response = requests.post(f"{BASE_URL}/rooms/create?mode=alias&difficulty=medium")
    assert response.status_code == 200
    data = response.json()
    room_code = data["room_code"]
    print(f"✓ Created room: {room_code}")
    
    # 2. Connect to WebSocket
    print(f"\n2. Connecting to WebSocket...")
    ws_url = f"{WS_URL}/ws/game/{room_code}"
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print("✓ WebSocket connected")
            
            # 3. Receive initial game state
            print("\n3. Receiving initial game state...")
            message = await websocket.recv()
            data = json.loads(message)
            assert data["type"] == "game_state"
            assert data["data"]["room_code"] == room_code
            assert data["data"]["status"] == "lobby"
            print(f"✓ Received game state: {data['data']['status']}")
            
            # 4. Join team
            print("\n4. Joining team 1...")
            join_msg = {
                "type": "join_team",
                "team": 1,
                "user_id": "test_user_1",
                "username": "TestPlayer"
            }
            await websocket.send(json.dumps(join_msg))
            
            # Receive updated state
            message = await websocket.recv()
            data = json.loads(message)
            assert data["type"] == "game_state"
            team1 = next(t for t in data["data"]["teams"] if t["id"] == 1)
            assert len(team1["players"]) == 1
            assert team1["players"][0]["username"] == "TestPlayer"
            print(f"✓ Joined team, players in team 1: {len(team1['players'])}")
            
            # 5. Start game
            print("\n5. Starting game...")
            start_msg = {"type": "start_game"}
            await websocket.send(json.dumps(start_msg))
            
            # Receive messages
            messages = []
            for _ in range(3):  # game_state, new_word, timer
                try:
                    msg = await asyncio.wait_for(websocket.recv(), timeout=2)
                    messages.append(json.loads(msg))
                except asyncio.TimeoutError:
                    break
            
            # Check we got the right messages
            msg_types = [m["type"] for m in messages]
            print(f"✓ Received messages: {msg_types}")
            
            assert "game_state" in msg_types
            assert "new_word" in msg_types
            assert "timer" in msg_types
            
            # Check game state updated to playing
            game_state_msg = next(m for m in messages if m["type"] == "game_state")
            assert game_state_msg["data"]["status"] == "playing"
            print("✓ Game status changed to 'playing'")
            
            # Check word was sent
            word_msg = next(m for m in messages if m["type"] == "new_word")
            assert "word" in word_msg
            print(f"✓ Received word: {word_msg['word']}")
            
            # 6. Guess word
            print("\n6. Guessing word...")
            guess_msg = {"type": "word_guessed"}
            await websocket.send(json.dumps(guess_msg))
            
            # Receive new word and updated score
            messages = []
            for _ in range(2):
                try:
                    msg = await asyncio.wait_for(websocket.recv(), timeout=2)
                    messages.append(json.loads(msg))
                except asyncio.TimeoutError:
                    break
            
            # Check score increased
            game_state_msg = next((m for m in messages if m["type"] == "game_state"), None)
            if game_state_msg:
                team1 = next(t for t in game_state_msg["data"]["teams"] if t["id"] == 1)
                print(f"✓ Team 1 score: {team1['score']}")
                assert team1["score"] == 1
            
            # Check new word received
            word_msg = next((m for m in messages if m["type"] == "new_word"), None)
            if word_msg:
                print(f"✓ Received new word: {word_msg['word']}")
            
            print("\n" + "=" * 50)
            print("WEBSOCKET TEST PASSED!")
            print("=" * 50)
            return True
            
    except websockets.exceptions.WebSocketException as e:
        print(f"\n✗ WebSocket error: {e}")
        return False
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_websocket_connection())
    exit(0 if success else 1)
