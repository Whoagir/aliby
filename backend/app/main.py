from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.websocket import router as ws_router
from app.api import auth, rooms, users, leaderboard

app = FastAPI(title="Alias/Taboo API")

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
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(rooms.router, prefix="/rooms", tags=["rooms"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(leaderboard.router, prefix="/leaderboard", tags=["leaderboard"])

@app.get("/")
async def root():
    return {"message": "Alias/Taboo API", "status": "online"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
