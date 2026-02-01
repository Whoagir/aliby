"""
SQLAlchemy database models for users and game history
"""
from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to game history
    games = relationship("GameHistory", back_populates="user")

class GameHistory(Base):
    __tablename__ = "game_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    room_code = Column(String(10), nullable=False)
    played_at = Column(DateTime, default=datetime.utcnow)
    
    # Game data (JSON)
    teams = Column(JSON, nullable=False)  # [{"name": "Team1", "score": 10, "players": [...]}]
    winner = Column(String(100), nullable=False)
    final_scores = Column(JSON, nullable=False)  # {"Team1": 10, "Team2": 8}
    guessed_words = Column(JSON, nullable=False)  # [{"word": "house", "team": "Team1", "translation": "дом", "used_translation": true}]
    
    # Relationship
    user = relationship("User", back_populates="games")
