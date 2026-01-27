"""
Simple integration tests for Alias/Taboo API
Run: python test_api.py
"""
import requests
import json
import time

BASE_URL = "http://localhost:8050"

def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    print("✓ Health check passed")

def test_create_room():
    """Test room creation"""
    print("\nTesting room creation...")
    
    # Test Alias room with default settings
    response = requests.post(f"{BASE_URL}/rooms/create?mode=alias")
    assert response.status_code == 200
    data = response.json()
    assert "room_code" in data
    assert data["mode"] == "alias"
    assert data["status"] == "lobby"
    print(f"✓ Created Alias room: {data['room_code']}")
    
    # Test Taboo room with custom settings
    params = {
        "mode": "taboo",
        "timed_mode": "true",
        "round_time": "180",
        "difficulty": "hard",
        "language": "en"
    }
    response = requests.post(f"{BASE_URL}/rooms/create", params=params)
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "taboo"
    assert data["settings"]["round_time"] == 180
    assert data["settings"]["difficulty"] == "hard"
    print(f"✓ Created Taboo room with custom settings: {data['room_code']}")
    
    return data["room_code"]

def test_get_room(room_code):
    """Test getting room info"""
    print(f"\nTesting get room info for {room_code}...")
    response = requests.get(f"{BASE_URL}/rooms/{room_code}")
    assert response.status_code == 200
    data = response.json()
    assert data["room_code"] == room_code
    assert "teams" in data
    assert len(data["teams"]) == 2
    print(f"✓ Room info retrieved: {data['mode']} mode, {len(data['teams'])} teams")

def test_get_nonexistent_room():
    """Test getting non-existent room"""
    print("\nTesting non-existent room...")
    response = requests.get(f"{BASE_URL}/rooms/XXXX")
    assert response.status_code == 404
    print("✓ Correctly returns 404 for non-existent room")

def test_settings_variations():
    """Test different setting combinations"""
    print("\nTesting setting variations...")
    
    # Test without timer
    params = {"mode": "alias", "timed_mode": "false", "difficulty": "easy"}
    response = requests.post(f"{BASE_URL}/rooms/create", params=params)
    assert response.status_code == 200
    data = response.json()
    assert data["settings"]["timed_mode"] == False
    print("✓ Room created without timer")
    
    # Test mixed difficulty
    params = {"mode": "taboo", "difficulty": "mixed"}
    response = requests.post(f"{BASE_URL}/rooms/create", params=params)
    assert response.status_code == 200
    data = response.json()
    assert data["settings"]["difficulty"] == "mixed"
    print("✓ Room created with mixed difficulty")

def run_all_tests():
    """Run all tests"""
    print("=" * 50)
    print("Running API Tests")
    print("=" * 50)
    
    try:
        test_health()
        room_code = test_create_room()
        test_get_room(room_code)
        test_get_nonexistent_room()
        test_settings_variations()
        
        print("\n" + "=" * 50)
        print("ALL TESTS PASSED!")
        print("=" * 50)
        return True
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return False
    except requests.exceptions.ConnectionError:
        print("\n✗ Cannot connect to backend. Make sure it's running on http://localhost:8050")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
