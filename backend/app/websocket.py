from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import asyncio
import time
from app.models import GameRoom, GameState, GameMode, GameStatus, Team, Player, GameSettings, GuessedWord
from app.services.word_service import word_service

router = APIRouter()

# In-memory storage for MVP (move to Redis later)
active_rooms: Dict[str, GameRoom] = {}
room_connections: Dict[str, Set[WebSocket]] = {}
active_timers: Dict[str, asyncio.Task] = {}  # Track active timer tasks


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_code: str):
        await websocket.accept()
        if room_code not in self.active_connections:
            self.active_connections[room_code] = set()
        self.active_connections[room_code].add(websocket)

    def disconnect(self, websocket: WebSocket, room_code: str):
        if room_code in self.active_connections:
            self.active_connections[room_code].discard(websocket)
            if not self.active_connections[room_code]:
                del self.active_connections[room_code]

    async def broadcast(self, room_code: str, message: dict):
        if room_code in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[room_code]:
                try:
                    await connection.send_json(message)
                except:
                    disconnected.add(connection)
            
            # Clean up disconnected
            for conn in disconnected:
                self.active_connections[room_code].discard(conn)


manager = ConnectionManager()


async def monitor_round_timer(room_code: str, duration: int):
    """Monitor round timer and send timeout when duration expires (client handles countdown)"""
    try:
        await asyncio.sleep(duration)
        
        if room_code not in active_rooms:
            return
            
        room = active_rooms[room_code]
        if room.status != GameStatus.PLAYING:
            return
        
        # Time's up - send round summary with guessed words
        await manager.broadcast(room_code, {
            "type": "round_summary",
            "reason": "timeout",
            "guessed_words": [
                {
                    "word": gw.word,
                    "taboo_words": gw.taboo_words,
                    "timestamp": gw.timestamp
                }
                for gw in room.current_round_words
            ]
        })
    except asyncio.CancelledError:
        # Timer was cancelled (e.g., round ended early or paused)
        pass
    finally:
        # Clean up timer reference
        if room_code in active_timers:
            del active_timers[room_code]


def get_game_state(room: GameRoom) -> dict:
    """Convert GameRoom to GameState for broadcasting"""
    return {
        "type": "game_state",
        "data": {
            "room_code": room.room_code,
            "mode": room.mode.value if hasattr(room.mode, 'value') else room.mode,
            "status": room.status.value if hasattr(room.status, 'value') else room.status,
            "host_id": room.host_id,
            "teams": [
                {
                    "id": team.id,
                    "name": team.name,
                    "players": [
                        {
                            "user_id": p.user_id,
                            "username": p.username,
                            "is_explaining": p.is_explaining
                        }
                        for p in team.players
                    ],
                    "score": team.score
                }
                for team in room.teams
            ],
            "current_round": room.current_round,
            "current_team_index": room.current_team_index,
            "settings": room.settings.dict(),
            "is_paused": room.is_paused
        }
    }


@router.websocket("/ws/game/{room_code}")
async def websocket_endpoint(websocket: WebSocket, room_code: str):
    await manager.connect(websocket, room_code)
    
    print(f"[WebSocket] Client connected to room: {room_code}")
    print(f"[WebSocket] Active rooms: {list(active_rooms.keys())}")
    
    # Send current state if room exists
    if room_code in active_rooms:
        room = active_rooms[room_code]
        print(f"[WebSocket] Room found, sending game state")
        await websocket.send_json(get_game_state(room))
    else:
        print(f"[WebSocket] ERROR: Room {room_code} not found in active_rooms!")
        await websocket.send_json({
            "type": "error",
            "message": f"Room {room_code} not found"
        })
    
    try:
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            if room_code not in active_rooms:
                await websocket.send_json({
                    "type": "error",
                    "message": "Room not found"
                })
                continue
            
            room = active_rooms[room_code]
            
            if message_type == "join_team":
                # Add player to team
                team_id = data.get("team")
                user_id = data.get("user_id")
                username = data.get("username")
                
                # Find or create team
                team = next((t for t in room.teams if t.id == team_id), None)
                if not team:
                    team = Team(
                        id=team_id,
                        name=f"Team {team_id}",
                        players=[],
                        score=0
                    )
                    room.teams.append(team)
                
                # Remove player from other teams
                for t in room.teams:
                    t.players = [p for p in t.players if p.user_id != user_id]
                
                # Add to new team
                team.players.append(Player(
                    user_id=user_id,
                    username=username,
                    is_explaining=False
                ))
                
                # Broadcast updated state
                await manager.broadcast(room_code, get_game_state(room))
            
            elif message_type == "start_game":
                # Move from LOBBY to PLAYING, but don't start round yet
                if room.status == GameStatus.LOBBY:
                    room.status = GameStatus.PLAYING
                    room.current_round = 1
                    
                    # Set first explainer
                    if room.teams and room.teams[0].players:
                        room.teams[0].players[0].is_explaining = True
                    
                    # Broadcast state - GamePage will show "Start Round" button
                    await manager.broadcast(room_code, get_game_state(room))
            
            elif message_type == "start_round":
                # Actually start the round with word and timer
                if room.status == GameStatus.PLAYING:
                    user_id = data.get("user_id")
                    
                    # ВАЖНО: Проверяем что игрок находится в ТЕКУЩЕЙ команде
                    current_team = room.teams[room.current_team_index]
                    player_in_current_team = any(
                        p.user_id == user_id for p in current_team.players
                    )
                    
                    if not player_in_current_team:
                        print(f"[start_round] ERROR: Player {user_id} не в текущей команде {current_team.name}!")
                        await websocket.send_json({
                            "type": "error",
                            "message": f"Only {current_team.name} can start the round!"
                        })
                        continue
                    
                    print(f"[start_round] Player {user_id} from {current_team.name} starting round")
                    
                    # Reset all players' explaining status
                    for team in room.teams:
                        for player in team.players:
                            player.is_explaining = False
                    
                    # Set requesting player as explaining
                    for player in current_team.players:
                        if player.user_id == user_id:
                            player.is_explaining = True
                            break
                    
                    # Broadcast updated state with current explaining team
                    await manager.broadcast(room_code, get_game_state(room))
                    
                    # Send first word from word service
                    word = word_service.get_random_word(
                        room.mode, 
                        room.settings.difficulty,
                        room_code
                    )
                    
                    if word:
                        await manager.broadcast(room_code, {
                            "type": "new_word",
                            "word": word.word,
                            "taboo": word.taboo_words
                        })
                    
                    # Start timer if timed mode is enabled
                    if room.settings.timed_mode:
                        # Cancel existing timer if any
                        if room_code in active_timers:
                            active_timers[room_code].cancel()
                        
                        # Send timer start message (client handles countdown)
                        start_time = time.time()
                        await manager.broadcast(room_code, {
                            "type": "timer_start",
                            "start_time": start_time,
                            "duration": room.settings.round_time
                        })
                        
                        # Start background monitor task
                        timer_task = asyncio.create_task(
                            monitor_round_timer(room_code, room.settings.round_time)
                        )
                        active_timers[room_code] = timer_task
                    else:
                        # No timer - send unlimited indicator
                        await manager.broadcast(room_code, {
                            "type": "timer_start",
                            "duration": -1  # -1 indicates unlimited time
                        })
            
            elif message_type == "word_guessed":
                # Save the guessed word before moving to next
                current_word_text = data.get("word", "")
                current_word_taboo = data.get("taboo_words", [])
                
                if current_word_text:
                    room.current_round_words.append(GuessedWord(
                        word=current_word_text,
                        taboo_words=current_word_taboo,
                        timestamp=time.time()
                    ))
                
                # Increment score for the CURRENT team (by index)
                current_team = room.teams[room.current_team_index]
                current_team.score += 1
                
                # Check if team reached score_to_win
                if current_team.score >= room.settings.score_to_win:
                    # Cancel timer
                    if room_code in active_timers:
                        active_timers[room_code].cancel()
                        del active_timers[room_code]
                    
                    # Game over!
                    room.status = GameStatus.FINISHED
                    await manager.broadcast(room_code, {
                        "type": "game_end",
                        "winner": current_team.name,
                        "reason": "score_reached",
                        "scores": {t.name: t.score for t in room.teams}
                    })
                    continue
                
                await manager.broadcast(room_code, get_game_state(room))
                
                # Send next word
                word = word_service.get_random_word(
                    room.mode,
                    room.settings.difficulty,
                    room_code
                )
                
                if word:
                    await manager.broadcast(room_code, {
                        "type": "new_word",
                        "word": word.word,
                        "taboo": word.taboo_words
                    })
            
            elif message_type == "word_skip":
                # Send next word
                word = word_service.get_random_word(
                    room.mode,
                    room.settings.difficulty,
                    room_code
                )
                
                if word:
                    await manager.broadcast(room_code, {
                        "type": "new_word",
                        "word": word.word,
                        "taboo": word.taboo_words
                    })
            
            elif message_type == "pause_game":
                # Pause the game
                if not room.is_paused:
                    room.is_paused = True
                    await manager.broadcast(room_code, {
                        "type": "game_paused",
                        "is_paused": True
                    })
            
            elif message_type == "resume_game":
                # Resume the game
                if room.is_paused:
                    room.is_paused = False
                    await manager.broadcast(room_code, {
                        "type": "game_resumed",
                        "is_paused": False
                    })
            
            elif message_type == "remove_word":
                # Remove a word from guessed list and deduct point
                word_to_remove = data.get("word")
                if word_to_remove:
                    # Find and remove the word
                    room.current_round_words = [
                        gw for gw in room.current_round_words 
                        if gw.word != word_to_remove
                    ]
                    
                    # Deduct point from current team
                    current_team = next((t for t in room.teams if any(p.is_explaining for p in t.players)), None)
                    if current_team and current_team.score > 0:
                        current_team.score -= 1
                    
                    await manager.broadcast(room_code, {
                        "type": "word_removed",
                        "word": word_to_remove,
                        "guessed_words": [
                            {
                                "word": gw.word,
                                "taboo_words": gw.taboo_words,
                                "timestamp": gw.timestamp
                            }
                            for gw in room.current_round_words
                        ]
                    })
                    await manager.broadcast(room_code, get_game_state(room))
            
            elif message_type == "confirm_round_end":
                # User confirmed round end after reviewing words
                # Clear round words and proceed to next round
                room.current_round_words = []
                room.is_paused = False
                room.paused_time_left = 0
            
            elif message_type == "round_end":
                print(f"[round_end] Current team index: {room.current_team_index}")
                
                # Cancel active timer if any
                if room_code in active_timers:
                    active_timers[room_code].cancel()
                    del active_timers[room_code]
                
                # Clear round words and reset pause
                room.current_round_words = []
                room.is_paused = False
                room.paused_time_left = 0
                
                # Reset all players' explaining status
                for team in room.teams:
                    for player in team.players:
                        player.is_explaining = False
                
                # Switch to next team (round-robin)
                room.current_team_index = (room.current_team_index + 1) % len(room.teams)
                
                print(f"[round_end] New team index: {room.current_team_index}")
                print(f"[round_end] New team: {room.teams[room.current_team_index].name}")
                
                # Increment round counter every full cycle of teams
                if room.current_team_index == 0:
                    room.current_round += 1
                
                if room.current_round > room.settings.rounds_total:
                    room.status = GameStatus.FINISHED
                    winner = max(room.teams, key=lambda t: t.score) if room.teams else None
                    
                    await manager.broadcast(room_code, {
                        "type": "game_end",
                        "winner": winner.name if winner else None,
                        "scores": {t.name: t.score for t in room.teams}
                    })
                else:
                    # Send clear signal that round has ended
                    await manager.broadcast(room_code, {
                        "type": "round_cleared"
                    })
                    
                    # Prepare next round (don't start automatically)
                    # GamePage will show "Start Round" button
                    await manager.broadcast(room_code, get_game_state(room))
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_code)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, room_code)
