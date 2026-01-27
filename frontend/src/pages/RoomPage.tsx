import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import useGameWebSocket from '../hooks/useGameWebSocket';

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
  const { code } = useParams<{ code: string }>();
  const navigate = useNavigate();
  const username = localStorage.getItem('username') || 'Anonymous';
  const userId = localStorage.getItem('user_id') || Date.now().toString();
  
  const { gameState, sendMessage, isConnected } = useGameWebSocket(code || '');
  const [selectedTeam, setSelectedTeam] = useState<number | null>(null);

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

  useEffect(() => {
    if (gameState?.status === 'playing') {
      navigate(`/room/${code}/play`);
    }
  }, [gameState?.status, code, navigate]);

  if (!isConnected || !gameState) {
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
            Room: {code}
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
