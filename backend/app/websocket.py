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
    """Monitor round timer and send updates every second"""
    try:
        time_left = duration
        
        while time_left > 0:
            await asyncio.sleep(1)
            time_left -= 1
            
            if room_code not in active_rooms:
                return
                
            room = active_rooms[room_code]
            if room.status != GameStatus.PLAYING:
                return
            
            # Send timer update every second
            await manager.broadcast(room_code, {
                "type": "timer_update",
                "time_left": time_left
            })
        
        # Time's up - mark timer as ended (don't send round_summary yet!)
        room.timer_ended = True
        
        # Notify all clients that timer ended (but keep last word visible)
        await manager.broadcast(room_code, {
            "type": "timer_ended"
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
                    
                    # Get current team
                    current_team = room.teams[room.current_team_index]
                    
                    # ВАЖНО: Проверяем что игрок находится в ТЕКУЩЕЙ команде (кроме solo_device режима)
                    if not room.settings.solo_device:
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
                        room.current_word = word  # Save current word with translation
                        await manager.broadcast(room_code, {
                            "type": "new_word",
                            "word": word.word,
                            "taboo": word.taboo_words,
                            "translation": word.translation if room.settings.show_translations else ""
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
                used_translation = data.get("used_translation", False)
                
                # Check if timer ended - last word needs team selection
                if room.timer_ended:
                    # Timer ended - save word for team selection (no score yet)
                    if current_word_text:
                        room.current_round_words.append(GuessedWord(
                            word=current_word_text,
                            taboo_words=current_word_taboo,
                            timestamp=time.time(),
                            used_translation=False,  # Last word always 1 point
                            translation=room.current_word.translation if room.current_word else ""
                        ))
                    
                    room.awaiting_team_selection = True
                    # Send team selection prompt with all team names
                    await manager.broadcast(room_code, {
                        "type": "select_team",
                        "teams": [{"id": t.id, "name": t.name} for t in room.teams],
                        "last_word": current_word_text
                    })
                else:
                    # Normal flow - add word and score
                    if current_word_text:
                        room.current_round_words.append(GuessedWord(
                            word=current_word_text,
                            taboo_words=current_word_taboo,
                            timestamp=time.time(),
                            used_translation=used_translation,
                            translation=room.current_word.translation if room.current_word else ""
                        ))
                    
                    # Increment score for the CURRENT team (by index)
                    # 0.5 points if translation was used, 1.0 otherwise
                    current_team = room.teams[room.current_team_index]
                    points = 0.5 if used_translation else 1.0
                    current_team.score += points
                    
                    # NOTE: Victory is checked at the end of a full cycle (in round_end handler)
                    # Not immediately after reaching score_to_win
                    
                    await manager.broadcast(room_code, get_game_state(room))
                    
                    # Send next word
                    word = word_service.get_random_word(
                        room.mode,
                        room.settings.difficulty,
                        room_code
                    )
                    
                    if word:
                        room.current_word = word  # Save current word with translation
                        await manager.broadcast(room_code, {
                            "type": "new_word",
                            "word": word.word,
                            "taboo": word.taboo_words,
                            "translation": word.translation if room.settings.show_translations else ""
                        })
            
            elif message_type == "end_round":
                # For unlimited mode - manually end the round
                # Mark timer as ended (same as when timer reaches 0)
                room.timer_ended = True
                
                # Notify all clients that round ended
                await manager.broadcast(room_code, {
                    "type": "timer_ended"
                })
            
            elif message_type == "word_skip":
                # Deduct 1 point for skip (minimum 0)
                current_team = room.teams[room.current_team_index]
                current_team.score = max(0, current_team.score - 1)
                
                # Check if timer ended - if so, skip means round ends
                if room.timer_ended:
                    # Timer ended and word skipped → go to round summary
                    await manager.broadcast(room_code, {
                        "type": "round_summary",
                        "reason": "timeout",
                        "guessed_words": [
                            {
                                "word": gw.word,
                                "taboo_words": gw.taboo_words,
                                "timestamp": gw.timestamp,
                                "translation": gw.translation if room.settings.show_translations else ""
                            }
                            for gw in room.current_round_words
                        ]
                    })
                    # Send updated game state with new score
                    await manager.broadcast(room_code, get_game_state(room))
                else:
                    # Normal flow - send next word
                    await manager.broadcast(room_code, get_game_state(room))
                    
                    word = word_service.get_random_word(
                        room.mode,
                        room.settings.difficulty,
                        room_code
                    )
                    
                    if word:
                        room.current_word = word  # Save current word with translation
                        await manager.broadcast(room_code, {
                            "type": "new_word",
                            "word": word.word,
                            "taboo": word.taboo_words,
                            "translation": word.translation if room.settings.show_translations else ""
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
                                "timestamp": gw.timestamp,
                                "translation": gw.translation if room.settings.show_translations else ""
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
            
            elif message_type == "team_selected":
                # Handle team selection for last word after timer ended
                print(f"[team_selected] Awaiting selection: {room.awaiting_team_selection}")
                print(f"[team_selected] Words count: {len(room.current_round_words)}")
                if room.awaiting_team_selection:
                    selected_team_id = data.get("team_id")
                    print(f"[team_selected] Selected team ID: {selected_team_id}")
                    
                    # Find the selected team and add 1 point
                    selected_team = next((t for t in room.teams if t.id == selected_team_id), None)
                    if selected_team:
                        print(f"[team_selected] Team found: {selected_team.name}, current score: {selected_team.score}")
                        selected_team.score += 1.0  # Always 1 point for last word
                        print(f"[team_selected] New score: {selected_team.score}")
                        
                        # Reset flags
                        room.awaiting_team_selection = False
                        room.timer_ended = False
                        
                        # Send round summary
                        print(f"[team_selected] Sending round_summary with {len(room.current_round_words)} words")
                        await manager.broadcast(room_code, {
                            "type": "round_summary",
                            "reason": "timeout",
                            "guessed_words": [
                                {
                                    "word": gw.word,
                                    "taboo_words": gw.taboo_words,
                                    "timestamp": gw.timestamp,
                                    "translation": gw.translation if room.settings.show_translations else ""
                                }
                                for gw in room.current_round_words
                            ]
                        })
                        
                        # Broadcast updated game state
                        await manager.broadcast(room_code, get_game_state(room))
            
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
                room.timer_ended = False
                room.awaiting_team_selection = False
                
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
                    print(f"[round_end] Cycle completed! Round: {room.current_round}")
                    
                    # Check for winner ONLY at the end of a full cycle
                    if room.teams:
                        max_score = max(t.score for t in room.teams)
                        print(f"[round_end] Max score: {max_score}, Score to win: {room.settings.score_to_win}")
                        
                        # Check if anyone reached score_to_win
                        if max_score >= room.settings.score_to_win:
                            # Count how many teams have the max score
                            teams_with_max = [t for t in room.teams if t.score == max_score]
                            print(f"[round_end] Teams with max score: {[t.name for t in teams_with_max]}")
                            
                            # Winner only if there's exactly ONE team with max score
                            if len(teams_with_max) == 1:
                                winner = teams_with_max[0]
                                room.status = GameStatus.FINISHED
                                
                                # Cancel timer if any
                                if room_code in active_timers:
                                    active_timers[room_code].cancel()
                                    del active_timers[room_code]
                                
                                print(f"[round_end] WINNER: {winner.name}")
                                print(f"[round_end] Broadcasting game_end to {room_code}...")
                                await manager.broadcast(room_code, {
                                    "type": "game_end",
                                    "winner": winner.name,
                                    "reason": "score_reached_cycle_end",
                                    "scores": {t.name: t.score for t in room.teams}
                                })
                                print(f"[round_end] game_end broadcast complete!")
                                # Don't send round_cleared, game is over
                                continue
                            else:
                                print(f"[round_end] TIE-BREAK! Multiple teams with {max_score} points, continuing...")
                
                # Check if we exceeded rounds_total (fallback for timed mode)
                if room.current_round > room.settings.rounds_total and room.settings.rounds_total > 0:
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
