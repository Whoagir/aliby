import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';

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

interface GameHistory {
  id: number;
  room_code: string;
  played_at: string;
  teams: Array<{ name: string; score: number }>;
  winner: string;
  final_scores: Record<string, number>;
  guessed_words: Array<{ word: string; team: string; translation?: string }>;
}

const HistoryPage: React.FC = () => {
  const navigate = useNavigate();
  const [games, setGames] = useState<GameHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedGame, setSelectedGame] = useState<GameHistory | null>(null);

  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    const token = localStorage.getItem('auth_token');
    if (!token) {
      navigate('/login');
      return;
    }

    try {
      const response = await fetch(`${API_URL}/history/my-games`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to fetch history');
      }

      const data = await response.json();
      setGames(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-white text-2xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-4">
      <div className="max-w-4xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-4xl font-bold text-white">My Game History</h1>
          <button
            onClick={() => navigate('/')}
            className="bg-white text-blue-600 px-6 py-2 rounded-lg font-medium hover:bg-gray-100 transition"
          >
            Back to Home
          </button>
        </div>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {games.length === 0 ? (
          <div className="bg-white rounded-lg shadow-lg p-8 text-center">
            <p className="text-gray-600 text-xl">No games played yet!</p>
            <button
              onClick={() => navigate('/')}
              className="mt-4 bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
            >
              Play Your First Game
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {games.map((game) => (
              <div
                key={game.id}
                className="bg-white rounded-lg shadow-lg p-6 cursor-pointer hover:shadow-xl transition"
                onClick={() => setSelectedGame(game)}
              >
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-2xl font-bold text-gray-800">
                      Room: {game.room_code}
                    </h3>
                    <p className="text-gray-500">{formatDate(game.played_at)}</p>
                  </div>
                  <div className="text-right">
                    <span className="inline-block bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm font-medium">
                      Winner: {game.winner}
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {game.teams.map((team, idx) => (
                    <div key={idx} className="bg-gray-100 rounded-lg p-3">
                      <p className="font-medium text-gray-700">{team.name}</p>
                      <p className="text-2xl font-bold text-blue-600">{team.score} pts</p>
                    </div>
                  ))}
                </div>

                <div className="mt-4 text-sm text-gray-500">
                  {game.guessed_words.length} words guessed • Click for details
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Game Details Modal */}
        {selectedGame && (
          <div 
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
            onClick={() => setSelectedGame(null)}
          >
            <div 
              className="bg-white rounded-lg shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="p-6 border-b">
                <div className="flex justify-between items-start">
                  <div>
                    <h2 className="text-3xl font-bold text-gray-800">
                      Game Details
                    </h2>
                    <p className="text-gray-500 mt-1">
                      {formatDate(selectedGame.played_at)}
                    </p>
                  </div>
                  <button
                    onClick={() => setSelectedGame(null)}
                    className="text-gray-400 hover:text-gray-600 text-2xl"
                  >
                    ×
                  </button>
                </div>
              </div>

              <div className="p-6 overflow-y-auto max-h-[60vh]">
                <h3 className="text-xl font-bold text-gray-800 mb-4">
                  Teams & Scores
                </h3>
                <div className="grid grid-cols-2 gap-4 mb-6">
                  {selectedGame.teams.map((team, idx) => (
                    <div 
                      key={idx} 
                      className={`rounded-lg p-4 ${
                        team.name === selectedGame.winner
                          ? 'bg-green-100 border-2 border-green-500'
                          : 'bg-gray-100'
                      }`}
                    >
                      <p className="font-bold text-gray-700">{team.name}</p>
                      <p className="text-3xl font-bold text-blue-600">{team.score}</p>
                      {team.name === selectedGame.winner && (
                        <span className="text-green-600 text-sm font-medium">Winner!</span>
                      )}
                    </div>
                  ))}
                </div>

                <h3 className="text-xl font-bold text-gray-800 mb-4">
                  Guessed Words ({selectedGame.guessed_words.length})
                </h3>
                <div className="space-y-2">
                  {selectedGame.guessed_words.map((word, idx) => (
                    <div 
                      key={idx}
                      className="bg-gray-50 rounded-lg p-3 flex justify-between items-center"
                    >
                      <div>
                        <span className="font-medium text-gray-800">{word.word}</span>
                        {word.translation && (
                          <span className="text-blue-600 ml-2">({word.translation})</span>
                        )}
                      </div>
                      <span className="text-sm text-gray-500">{word.team}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default HistoryPage;
