import { useEffect, useRef, useState } from 'react';

// Determine WebSocket URL based on environment
const getWsUrl = () => {
  // If env variable is set, use it
  if (process.env.REACT_APP_WS_URL) {
    return process.env.REACT_APP_WS_URL;
  }
  
  // If on port 3050 (dev), use backend directly
  if (window.location.port === '3050') {
    return 'ws://localhost:8050';
  }
  
  // Otherwise, use same host:port as current page (nginx routing)
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.hostname}${window.location.port ? ':' + window.location.port : ''}`;
};

const WS_URL = getWsUrl();

interface GameState {
  room_code: string;
  mode: string;
  status: string;
  host_id: string;
  teams: Array<{
    id: number;
    name: string;
    players: Array<{
      user_id: string;
      username: string;
      is_explaining: boolean;
    }>;
    score: number;
  }>;
  current_round: number;
  current_team_index: number;
  settings: any;
  is_paused?: boolean;
}

interface GuessedWord {
  word: string;
  taboo_words: string[];
  timestamp: number;
  translation?: string;
}

const useGameWebSocket = (roomCode: string) => {
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [currentWord, setCurrentWord] = useState<string>('');
  const [currentTabooWords, setCurrentTabooWords] = useState<string[]>([]);
  const [currentTranslation, setCurrentTranslation] = useState<string>('');
  const [timeLeft, setTimeLeft] = useState<number>(0);
  const [isConnected, setIsConnected] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [roundSummary, setRoundSummary] = useState<GuessedWord[] | null>(null);
  const [timerEnded, setTimerEnded] = useState(false);
  const [teamSelection, setTeamSelection] = useState<{ teams: { id: number; name: string }[]; last_word: string } | null>(null);
  const [gameWinner, setGameWinner] = useState<{ winner: string; scores: Record<string, number> } | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!roomCode) return;

    const ws = new WebSocket(`${WS_URL}/ws/game/${roomCode}`);

    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      console.log('Received message:', message);

      switch (message.type) {
        case 'game_state':
          setGameState(message.data);
          setIsPaused(message.data.is_paused || false);
          break;
        case 'new_word':
          setCurrentWord(message.word);
          setCurrentTabooWords(message.taboo || []);
          setCurrentTranslation(message.translation || '');
          break;
        case 'timer_start':
          // Backend will send timer_update messages every second
          if (message.duration === -1) {
            // Unlimited time
            setTimeLeft(-1);
          } else {
            // Set initial time
            setTimeLeft(message.duration);
          }
          break;
        case 'timer_update':
          // Receive timer updates from backend
          setTimeLeft(message.time_left);
          break;
        case 'round_summary':
          // Show round summary modal
          setRoundSummary(message.guessed_words || []);
          setTeamSelection(null); // Close team selection if open
          break;
        case 'game_paused':
          setIsPaused(true);
          break;
        case 'game_resumed':
          setIsPaused(false);
          break;
        case 'word_removed':
          // Update summary after word removal
          setRoundSummary(message.guessed_words || []);
          break;
        case 'round_cleared':
          // Clear current word AND round summary for next team
          setCurrentWord('');
          setCurrentTabooWords([]);
          setCurrentTranslation('');
          setTimeLeft(0);
          setRoundSummary(null); // ВАЖНО: очистить модальное окно для всех!
          setTimerEnded(false);
          setTeamSelection(null);
          break;
        case 'timer_ended':
          // Timer reached 0 - mark it but keep word visible
          setTimerEnded(true);
          setTimeLeft(0);
          break;
        case 'select_team':
          // Show team selection modal for last word
          setTeamSelection({
            teams: message.teams || [],
            last_word: message.last_word || ''
          });
          break;
        case 'round_end':
          // Handle round end
          break;
        case 'game_end':
          // Show winner screen with scores
          setGameWinner({
            winner: message.winner,
            scores: message.scores || {}
          });
          break;
        case 'error':
          console.error('Game error:', message.message);
          break;
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
    };

    wsRef.current = ws;

    return () => {
      ws.close();
    };
  }, [roomCode]);

  const sendMessage = (message: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  };

  return {
    gameState,
    currentWord,
    currentTabooWords,
    currentTranslation,
    timeLeft,
    isConnected,
    isPaused,
    roundSummary,
    setRoundSummary,
    timerEnded,
    teamSelection,
    gameWinner,
    sendMessage,
  };
};

export default useGameWebSocket;
