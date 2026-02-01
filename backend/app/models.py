from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum
import uuid
import time


class GameMode(str, Enum):
    ALIAS = "alias"
    TABOO = "taboo"


class GameStatus(str, Enum):
    LOBBY = "lobby"
    PLAYING = "playing"
    FINISHED = "finished"


class Difficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    MIXED = "mixed"


# User models
class UserBase(BaseModel):
    username: str
    email: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: uuid.UUID
    total_score: int = 0
    games_played: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


# Game Settings
class GameSettings(BaseModel):
    timed_mode: bool = True  # True = with timer, False = unlimited time
    round_time: int = 60  # seconds (60, 180, 300)
    rounds_total: int = 5
    difficulty: Difficulty = Difficulty.MEDIUM
    language: str = "en"  # "en" for now, can add "ru" later
    word_pack: str = "general"
    score_to_win: int = 30  # Points needed to win (30, 50, 100)
    team_count: int = 2  # Number of teams (2, 3, 4)
    show_translations: bool = True  # Show Russian translations during game


# Team
class Player(BaseModel):
    user_id: str
    username: str
    is_explaining: bool = False


class GuessedWord(BaseModel):
    word: str
    taboo_words: List[str] = []
    timestamp: float  # Unix timestamp when guessed
    used_translation: bool = False  # True if translation was shown
    translation: str = ""  # Russian translation (for round summary)


class Team(BaseModel):
    id: int  # 1 or 2
    name: str
    players: List[Player] = []
    score: int = 0


# Game Room
class GameRoom(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    room_code: str
    mode: GameMode
    status: GameStatus = GameStatus.LOBBY
    teams: List[Team] = []
    current_round: int = 0
    current_team_index: int = 0  # Index of team currently playing
    settings: GameSettings = Field(default_factory=GameSettings)
    host_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    current_round_words: List[GuessedWord] = []  # Words guessed in current round
    is_paused: bool = False  # Pause state
    paused_time_left: int = 0  # Time remaining when paused
    current_word: Optional["Word"] = None  # Current word being played
    timer_ended: bool = False  # True when timer reaches 0
    awaiting_team_selection: bool = False  # True when waiting for team selection for last word


# Word
class Word(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    word: str
    taboo_words: List[str] = []
    difficulty: float = 0.5  # 0.0 - 1.0 (legacy field)
    category: str = "general"
    popularity_score: float = 0.0
    translation: str = ""  # Russian translation (empty if not available)


# WebSocket Messages
class WSMessage(BaseModel):
    type: str
    data: Optional[dict] = None


class JoinTeamMessage(BaseModel):
    type: str = "join_team"
    team: int
    user_id: str
    username: str


class StartGameMessage(BaseModel):
    type: str = "start_game"


class WordActionMessage(BaseModel):
    type: str  # "word_guessed", "word_skip", "word_taboo"
    word: Optional[str] = None


# Game State
class GameState(BaseModel):
    room_code: str
    mode: GameMode
    status: GameStatus
    teams: List[Team]
    current_round: int
    current_team: int
    current_word: Optional[Word] = None
    time_left: int = 0
    settings: GameSettings
