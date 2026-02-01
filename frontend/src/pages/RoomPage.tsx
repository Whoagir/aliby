import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import useGameWebSocket from '../hooks/useGameWebSocket';

// Determine API URL based on environment
const getApiUrl = () => {
  if (process.env.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }
  if (window.location.port === '3050') {
    return 'http://localhost:8050';
  }
  return `${window.location.protocol}//${window.location.hostname}${window.location.port ? ':' + window.location.port : ''}`;
};

const API_URL = getApiUrl();

interface Player {
  user_id: string;
  username: string;
}

interface Team {
  id: number;
  name: string;
  players: Player[];
  score: number;
}

const RoomPage: React.FC = () => {
  const { encryptedLink } = useParams<{ encryptedLink: string }>();
  const navigate = useNavigate();
  const username = localStorage.getItem('username') || 'Anonymous';
  const userId = localStorage.getItem('user_id') || Date.now().toString();
  
  const [roomCode, setRoomCode] = useState<string>('');
  const [hasPassword, setHasPassword] = useState(false);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [password, setPassword] = useState('');
  const [passwordError, setPasswordError] = useState('');
  const [decrypting, setDecrypting] = useState(true);
  
  const { gameState, sendMessage, isConnected } = useGameWebSocket(roomCode);
  const [selectedTeam, setSelectedTeam] = useState<number | null>(null);

  // Decrypt room link on mount
  useEffect(() => {
    const decryptLink = async () => {
      if (!encryptedLink) {
        navigate('/');
        return;
      }

      try {
        const response = await fetch(`${API_URL}/room-access/decrypt`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ encrypted_link: encryptedLink })
        });

        if (!response.ok) {
          throw new Error('Invalid room link');
        }

        const data = await response.json();
        setRoomCode(data.room_code);
        setHasPassword(data.has_password);
        
        if (data.has_password) {
          setShowPasswordModal(true);
        }
        
        setDecrypting(false);
      } catch (err) {
        console.error('Failed to decrypt link:', err);
        alert('Invalid or expired room link');
        navigate('/');
      }
    };

    decryptLink();
  }, [encryptedLink, navigate]);

  const joinTeam = (teamId: number) => {
    sendMessage({
      type: 'join_team',
      team: teamId,
      user_id: userId,
      username: username,
    });
    setSelectedTeam(teamId);
  };

  const startGame = () => {
    sendMessage({ type: 'start_game' });
  };

  const verifyPassword = async () => {
    setPasswordError('');
    
    try {
      const response = await fetch(`${API_URL}/room-access/verify-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          room_code: roomCode,
          password: password 
        })
      });

      if (!response.ok) {
        throw new Error('Incorrect password');
      }

      setShowPasswordModal(false);
    } catch (err: any) {
      setPasswordError(err.message || 'Incorrect password');
    }
  };

  useEffect(() => {
    if (gameState?.status === 'playing') {
      navigate(`/room/${encryptedLink}/play`);
    }
  }, [gameState?.status, encryptedLink, navigate]);

  if (decrypting) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-white text-xl">Loading room...</div>
      </div>
    );
  }

  if (showPasswordModal) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-2xl p-8 max-w-md w-full">
          <h2 className="text-3xl font-bold text-gray-800 mb-4">Private Room</h2>
          <p className="text-gray-600 mb-6">This room is password protected</p>
          
          {passwordError && (
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
              {passwordError}
            </div>
          )}

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && verifyPassword()}
              placeholder="Enter room password"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div className="flex gap-3">
            <button
              onClick={verifyPassword}
              className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 font-medium"
            >
              Join
            </button>
            <button
              onClick={() => navigate('/')}
              className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-400 font-medium"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!isConnected || !gameState || !roomCode) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-white text-xl">Connecting to game...</div>
      </div>
    );
  }

  const teams: Team[] = gameState.teams || [];
  const mode = gameState.mode || 'alias';
  const isHost = gameState.host_id === userId;

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">
            Room: {roomCode}
          </h1>
          <p className="text-blue-200 text-lg capitalize">
            Mode: {mode}
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-6 mb-8">
          {teams.map((team) => (
            <div
              key={team.id}
              className={`bg-white rounded-lg shadow-xl p-6 ${
                selectedTeam === team.id ? 'ring-4 ring-yellow-400' : ''
              }`}
            >
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-2xl font-bold text-gray-800">{team.name}</h2>
                <span className="text-lg text-gray-600">
                  {team.players.length} player{team.players.length !== 1 ? 's' : ''}
                </span>
              </div>

              <div className="space-y-2 mb-4 min-h-[100px]">
                {team.players.length === 0 ? (
                  <p className="text-gray-400 italic">No players yet</p>
                ) : (
                  team.players.map((player) => (
                    <div
                      key={player.user_id}
                      className="bg-gray-100 rounded px-4 py-2 font-medium text-gray-800"
                    >
                      {player.username}
                      {player.user_id === userId && ' (You)'}
                    </div>
                  ))
                )}
              </div>

              <button
                onClick={() => joinTeam(team.id)}
                className={`w-full py-2 px-4 rounded-lg font-semibold transition duration-200 ${
                  selectedTeam === team.id
                    ? 'bg-gray-300 text-gray-600 cursor-not-allowed'
                    : 'bg-blue-600 hover:bg-blue-700 text-white'
                }`}
                disabled={selectedTeam === team.id}
              >
                {selectedTeam === team.id ? 'In This Team' : 'Join Team'}
              </button>
            </div>
          ))}
        </div>

        <div className="text-center space-y-4">
          {isHost ? (
            <button
              onClick={startGame}
              disabled={teams.every((t) => t.players.length === 0)}
              className="bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-bold py-4 px-8 rounded-lg text-xl transition duration-200 disabled:cursor-not-allowed"
            >
              Start Game
            </button>
          ) : (
            <p className="text-blue-200 text-lg">
              Waiting for host to start the game...
            </p>
          )}
          
          <p className="text-blue-200 text-sm">
            {isHost ? "You are the host" : "Waiting for players to join teams..."}
          </p>
        </div>
      </div>
    </div>
  );
};

export default RoomPage;
