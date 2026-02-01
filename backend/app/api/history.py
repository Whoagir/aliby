"""
Game history API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime
from ..database import get_db
from ..db_models import User, GameHistory
from ..auth import get_current_user

router = APIRouter(prefix="/history", tags=["history"])

class GameHistoryResponse(BaseModel):
    id: int
    room_code: str
    played_at: datetime
    teams: list
    winner: str
    final_scores: dict
    guessed_words: list

@router.get("/my-games", response_model=List[GameHistoryResponse])
def get_my_games(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50
):
    """Get game history for current user"""
    games = db.query(GameHistory)\
        .filter(GameHistory.user_id == current_user.id)\
        .order_by(GameHistory.played_at.desc())\
        .limit(limit)\
        .all()
    
    return [{
        "id": game.id,
        "room_code": game.room_code,
        "played_at": game.played_at,
        "teams": game.teams,
        "winner": game.winner,
        "final_scores": game.final_scores,
        "guessed_words": game.guessed_words
    } for game in games]

class SaveGameRequest(BaseModel):
    room_code: str
    winner: str
    final_scores: dict
    teams: list
    guessed_words: list = []

@router.post("/save-game")
def save_game(
    request: SaveGameRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Save game to history (called from game-end)"""
    game_history = GameHistory(
        user_id=current_user.id,
        room_code=request.room_code,
        teams=request.teams,
        winner=request.winner,
        final_scores=request.final_scores,
        guessed_words=request.guessed_words
    )
    db.add(game_history)
    db.commit()
    
    return {"status": "saved", "game_id": game_history.id}
