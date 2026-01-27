from fastapi import APIRouter

router = APIRouter()


@router.get("/{user_id}/stats")
async def get_user_stats(user_id: str):
    """Get user statistics (placeholder)"""
    return {
        "user_id": user_id,
        "total_score": 0,
        "games_played": 0,
        "wins": 0,
        "avg_words_per_game": 0.0
    }


@router.get("/{user_id}/history")
async def get_user_history(user_id: str, limit: int = 10):
    """Get user game history (placeholder)"""
    return {
        "games": []
    }
