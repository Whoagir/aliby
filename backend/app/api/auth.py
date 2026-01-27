from fastapi import APIRouter

router = APIRouter()


@router.post("/register")
async def register(username: str, email: str, password: str):
    """Register new user (placeholder)"""
    return {
        "user_id": "temp_user_id",
        "username": username,
        "email": email
    }


@router.post("/login")
async def login(email: str, password: str):
    """Login user (placeholder)"""
    return {
        "access_token": "temp_token",
        "token_type": "bearer",
        "user_id": "temp_user_id"
    }
