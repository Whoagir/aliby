import json
import random
from pathlib import Path
from typing import List, Optional
from app.models import Word, GameMode, Difficulty

# Load word data
DATA_DIR = Path(__file__).parent.parent / "data"
ALIAS_WORDS = json.loads((DATA_DIR / "words_alias.json").read_text())
TABOO_WORDS = json.loads((DATA_DIR / "words_taboo.json").read_text())


class WordService:
    def __init__(self):
        # Track used words per room: {room_code: set(word1, word2, ...)}
        self.used_words_per_room = {}
    
    def get_random_word(
        self, 
        mode: GameMode, 
        difficulty: Difficulty,
        room_code: str
    ) -> Optional[Word]:
        """Get random UNIQUE word based on mode and difficulty"""
        
        # Initialize room's used words set
        if room_code not in self.used_words_per_room:
            self.used_words_per_room[room_code] = set()
        
        used_words = self.used_words_per_room[room_code]
        
        # Handle mixed difficulty (random selection)
        if difficulty == Difficulty.MIXED:
            difficulty = random.choice([Difficulty.EASY, Difficulty.MEDIUM, Difficulty.HARD])
        
        # Select word pool
        if mode == GameMode.ALIAS:
            words = ALIAS_WORDS.get(difficulty.value, [])
        elif mode == GameMode.TABOO:
            words = TABOO_WORDS.get(difficulty.value, [])
        else:
            return None
        
        # Filter out already used words
        available_words = [w for w in words if w["word"] not in used_words]
        
        # If all words used, reset the pool
        if not available_words:
            print(f"[WordService] All words used in room {room_code}, resetting pool")
            used_words.clear()
            available_words = words
        
        if not available_words:
            return None
        
        # Pick random word
        word_data = random.choice(available_words)
        
        # Mark as used
        used_words.add(word_data["word"])
        
        # Return Word object
        return Word(
            word=word_data["word"],
            taboo_words=word_data.get("taboo_words", []),
            difficulty=0.5,  # Legacy field, not used
            category="general"
        )
    
    def clear_room_words(self, room_code: str):
        """Clear used words for a room (when game ends)"""
        if room_code in self.used_words_per_room:
            del self.used_words_per_room[room_code]
    
    def get_word_by_difficulty_mixed(
        self,
        mode: GameMode,
        room_code: str
    ) -> Optional[Word]:
        """Get word with mixed difficulty (random)"""
        difficulties = [Difficulty.EASY, Difficulty.MEDIUM, Difficulty.HARD]
        chosen_difficulty = random.choice(difficulties)
        return self.get_random_word(mode, chosen_difficulty, room_code)


# Global instance
word_service = WordService()
