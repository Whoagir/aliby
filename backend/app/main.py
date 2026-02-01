from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.websocket import router as ws_router
from app.api import auth, rooms, users, leaderboard, history, room_access
from app.database import engine, Base

# Create database tables
Base.metadata.create_all(bind=engine)

# Rate limiter (40 requests per minute)
limiter = Limiter(key_func=get_remote_address, default_limits=["40/minute"])

app = FastAPI(title="Alias/Taboo API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS - allow all origins for development (nginx proxies from different ports/IPs)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for nginx access from different devices
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ws_router)
app.include_router(auth.router)
app.include_router(history.router)
app.include_router(room_access.router)
app.include_router(rooms.router, prefix="/rooms", tags=["rooms"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(leaderboard.router, prefix="/leaderboard", tags=["leaderboard"])

@app.get("/")
async def root():
    return {"message": "Alias/Taboo API", "status": "online"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
