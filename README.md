# Alias/Taboo Online

Online multiplayer word game for playing Alias and Taboo with friends.

## Features

- Real-time multiplayer via WebSockets
- Two game modes: Alias and Taboo
- Customizable game settings:
  - Timer mode (with timer / unlimited time)
  - Round duration (1 min / 3 min / 5 min)
  - Difficulty levels (Easy / Medium / Hard / Random)
  - Language selection (English, more coming soon)
- Real-time countdown timer with automatic round ending
- **Pause/Resume functionality** - pause the game and hide the word
- **Meme-based team names** - randomly generated fun team names
- **Round summary review** - review and remove incorrectly guessed words after each round
- Word difficulty based on modern popularity
- Room-based system with shareable 4-letter codes
- Multiple word databases by difficulty
- Global leaderboard and game history (coming soon)

## Tech Stack

### Backend
- FastAPI (Python)
- WebSockets for real-time communication
- PostgreSQL for persistent data
- Redis for game sessions

### Frontend
- React + TypeScript
- Tailwind CSS
- WebSocket client

## Quick Start

### Prerequisites
- Docker and Docker Compose
- WSL (for Windows users)

### Run with Docker

```bash
# Start all services
docker-compose up -d

# Services will be available at:
# - Frontend: http://localhost:3050
# - Backend API: http://localhost:8050
# - API docs: http://localhost:8050/docs
# - PostgreSQL: localhost:5433
# - Redis: localhost:6380
```

### Check Status

```bash
# View running containers
docker-compose ps

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop all services
docker-compose down
```

### Development

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### Frontend
```bash
cd frontend
npm install
npm start
```

## Project Structure

```
alias-game/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app
│   │   ├── models.py         # Database models
│   │   ├── websocket.py      # WebSocket handlers
│   │   ├── api/              # REST endpoints
│   │   └── services/         # Business logic
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── hooks/            # Custom hooks
│   │   ├── pages/            # Page components
│   │   └── api/              # API client
│   ├── package.json
│   └── Dockerfile
└── docker-compose.yml
```

## API Endpoints

### REST
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login
- `GET /users/{id}/stats` - User statistics
- `POST /rooms/create` - Create game room
- `GET /rooms/{code}` - Get room info
- `POST /rooms/{code}/join` - Join room
- `GET /leaderboard` - Global leaderboard

### WebSocket
- `WS /ws/game/{room_code}` - Game room connection

## Game Flow

1. **Create Room**: Host creates a room and selects game settings:
   - Game mode (Alias or Taboo)
   - Timer mode (with countdown or unlimited)
   - Round duration (1, 3, or 5 minutes)
   - Difficulty (Easy, Medium, Hard, or Random)

2. **Join Room**: Players join using 4-letter room code

3. **Team Selection**: Players choose their teams

4. **Game Starts**: Host initiates the game

5. **Gameplay**:
   - Timer counts down from selected duration (e.g., 60s → 59s → ... → 0s)
   - Explaining player describes the word
   - Teammates guess
   - Actions:
     - "Guessed" (+1 point, next word)
     - "Skip" (next word, no points)
     - "Pause" (hide word, freeze timer)
     - "Resume" (show word, continue timer)
   - Taboo mode: Additional "Taboo Violation" button for rule breaches
   - When timer reaches 0, all buttons are disabled
   - "Review Round" button appears

6. **Round Review**:
   - Modal shows all guessed words from the round
   - Players can remove incorrectly guessed words (e.g., same root word)
   - Removing a word deducts 1 point
   - Click "Continue to Next Round" to proceed

7. **Round End**: Game proceeds to next round or ends after all rounds

8. **Game End**: After all rounds complete, winner is announced

## License

MIT
