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
}

const useGameWebSocket = (roomCode: string) => {
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [currentWord, setCurrentWord] = useState<string>('');
  const [currentTabooWords, setCurrentTabooWords] = useState<string[]>([]);
  const [timeLeft, setTimeLeft] = useState<number>(0);
  const [isConnected, setIsConnected] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [roundSummary, setRoundSummary] = useState<GuessedWord[] | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const timerIntervalRef = useRef<NodeJS.Timeout | null>(null);

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
          break;
        case 'timer_start':
          // Start client-side countdown timer
          if (timerIntervalRef.current) {
            clearInterval(timerIntervalRef.current);
          }
          
          if (message.duration === -1) {
            // Unlimited time
            setTimeLeft(-1);
          } else {
            // Timed mode - countdown on client
            const endTime = Date.now() + message.duration * 1000;
            setTimeLeft(message.duration);
            
            timerIntervalRef.current = setInterval(() => {
              const remaining = Math.max(0, Math.ceil((endTime - Date.now()) / 1000));
              setTimeLeft(remaining);
              
              if (remaining === 0 && timerIntervalRef.current) {
                clearInterval(timerIntervalRef.current);
                timerIntervalRef.current = null;
              }
            }, 100); // Update every 100ms for smooth countdown
          }
          break;
        case 'round_summary':
          // Show round summary modal
          setRoundSummary(message.guessed_words || []);
          break;
        case 'game_paused':
          setIsPaused(true);
          // Stop timer on pause
          if (timerIntervalRef.current) {
            clearInterval(timerIntervalRef.current);
            timerIntervalRef.current = null;
          }
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
          setTimeLeft(0);
          setRoundSummary(null); // ВАЖНО: очистить модальное окно для всех!
          break;
        case 'round_end':
          // Handle round end
          break;
        case 'game_end':
          alert(`Game Over! Winner: ${message.winner}`);
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
      // Clean up timer
      if (timerIntervalRef.current) {
        clearInterval(timerIntervalRef.current);
        timerIntervalRef.current = null;
      }
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
    timeLeft,
    isConnected,
    isPaused,
    roundSummary,
    setRoundSummary,
    sendMessage,
  };
};

export default useGameWebSocket;
