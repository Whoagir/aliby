from fastapi import APIRouter, HTTPException
from app.models import GameRoom, GameMode, GameStatus, GameSettings, Team, Difficulty
from app.websocket import active_rooms
import random
import string
import uuid

router = APIRouter()

# Meme team names
TEAM_ADJECTIVES = [
    "Based", "Cringe", "Dank", "Pepega", "MonkaS", "Poggers", "Gigachad",
    "Sigma", "Chad", "Virgin", "Coomer", "Zoomer", "Boomer", "Doomer",
    "Wojak", "Pepe", "Stonks", "Big Brain", "Smol Brain", "Sussy",
    "Bussin", "Sheesh", "No Cap", "Ratio", "W", "L", "Cursed", "Blessed"
]

TEAM_NOUNS = [
    "Gamers", "Squad", "Gang", "Crew", "Team", "Legends", "Heroes",
    "Champions", "Warriors", "Masters", "Memers", "Chads", "Kings",
    "Queens", "Players", "Bros", "Homies", "Peeps", "Dudes", "Nerds",
    "Geeks", "Pros", "Noobs", "Gods", "Trolls", "Weebs", "Simps"
]

used_team_names = set()


def generate_meme_team_name() -> str:
    """Generate random meme team name"""
    global used_team_names
    
    # Try to generate unique name
    for _ in range(100):
        adj = random.choice(TEAM_ADJECTIVES)
        noun = random.choice(TEAM_NOUNS)
        name = f"{adj} {noun}"
        
        if name not in used_team_names:
            used_team_names.add(name)
            # Clean up if too many names stored
            if len(used_team_names) > 100:
                used_team_names.clear()
            return name
    
    # Fallback to numbered team if all combinations used
    return f"Team {random.randint(1, 9999)}"


def generate_room_code() -> str:
    """Generate unique 4-letter room code"""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase, k=4))
        if code not in active_rooms:
            return code


@router.post("/create")
async def create_room(
    mode: GameMode = GameMode.ALIAS,
    host_id: str = "anonymous",
    timed_mode: bool = True,
    round_time: int = 60,
    difficulty: Difficulty = Difficulty.MEDIUM,
    language: str = "en",
    score_to_win: int = 30,
    team_count: int = 2,
    show_translations: bool = True
):
    """Create new game room with custom settings"""
    room_code = generate_room_code()
    
    # Validate team_count
    if team_count < 2 or team_count > 4:
        team_count = 2
    
    settings = GameSettings(
        timed_mode=timed_mode,
        round_time=round_time,
        rounds_total=5,
        difficulty=difficulty,
        language=language,
        word_pack="general",
        score_to_win=score_to_win,
        team_count=team_count,
        show_translations=show_translations
    )
    
    # Generate teams dynamically based on team_count
    teams = [
        Team(id=i+1, name=generate_meme_team_name(), players=[], score=0)
        for i in range(team_count)
    ]
    
    room = GameRoom(
        id=uuid.uuid4(),
        room_code=room_code,
        mode=mode,
        status=GameStatus.LOBBY,
        teams=teams,
        current_team_index=0,
        settings=settings,
        host_id=host_id
    )
    
    active_rooms[room_code] = room
    
    return {
        "room_code": room_code,
        "mode": mode.value if hasattr(mode, 'value') else mode,
        "status": GameStatus.LOBBY.value,
        "settings": settings.dict()
    }


@router.get("/{room_code}")
async def get_room(room_code: str):
    """Get room info"""
    if room_code not in active_rooms:
        raise HTTPException(status_code=404, detail="Room not found")
    
    room = active_rooms[room_code]
    return {
        "room_code": room.room_code,
        "mode": room.mode.value if hasattr(room.mode, 'value') else room.mode,
        "status": room.status.value if hasattr(room.status, 'value') else room.status,
        "teams": [
            {
                "id": team.id,
                "name": team.name,
                "players": [{"user_id": p.user_id, "username": p.username} for p in team.players],
                "score": team.score
            }
            for team in room.teams
        ],
        "current_round": room.current_round,
        "settings": room.settings.dict()
    }


@router.post("/{room_code}/join")
async def join_room(room_code: str, user_id: str, username: str):
    """Join existing room"""
    if room_code not in active_rooms:
        raise HTTPException(status_code=404, detail="Room not found")
    
    return {"status": "success", "room_code": room_code}
