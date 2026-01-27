from fastapi import APIRouter

router = APIRouter()


@router.get("")
async def get_leaderboard(period: str = "all", limit: int = 50):
    """Get leaderboard (placeholder)"""
    return {
        "period": period,
        "leaders": []
    }
