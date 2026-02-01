import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

// Determine API URL based on environment
const getApiUrl = () => {
  // If env variable is set, use it
  if (process.env.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }
  
  // If on port 3050 (dev) or 8050 (backend direct), use backend directly
  if (window.location.port === '3050') {
    return 'http://localhost:8050';
  }
  
  // Otherwise, use same host:port as current page (nginx routing)
  return `${window.location.protocol}//${window.location.hostname}${window.location.port ? ':' + window.location.port : ''}`;
};

const API_URL = getApiUrl();

const HomePage: React.FC = () => {
  const [roomCode, setRoomCode] = useState('');
  const [username, setUsername] = useState('');
  const [loading, setLoading] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [selectedMode, setSelectedMode] = useState<'alias' | 'taboo'>('alias');
  const [showAdvanced, setShowAdvanced] = useState(false);
  
  // Game settings
  const [timedMode, setTimedMode] = useState(true);
  const [roundTime, setRoundTime] = useState(60);
  const [difficulty, setDifficulty] = useState('medium');
  const [language, setLanguage] = useState('en');
  const [scoreToWin, setScoreToWin] = useState(30);
  const [teamCount, setTeamCount] = useState(2);
  const [showTranslations, setShowTranslations] = useState(true);
  
  // Advanced settings
  const [customRoundTime, setCustomRoundTime] = useState(60);
  const [customScoreToWin, setCustomScoreToWin] = useState(30);
  const [enableMaxTranslations, setEnableMaxTranslations] = useState(false);
  const [maxTranslations, setMaxTranslations] = useState(10);
  
  const navigate = useNavigate();

  const openSettings = (mode: 'alias' | 'taboo') => {
    if (!username.trim()) {
      alert('Please enter your username');
      return;
    }
    setSelectedMode(mode);
    setShowSettings(true);
  };

  const createRoom = async () => {
    setLoading(true);
    try {
      // Get or create user_id (don't overwrite existing!)
      let userId = localStorage.getItem('user_id');
      if (!userId) {
        userId = Date.now().toString();
        localStorage.setItem('user_id', userId);
      }
      
      const params = new URLSearchParams({
        mode: selectedMode,
        timed_mode: timedMode.toString(),
        round_time: (showAdvanced ? customRoundTime : roundTime).toString(),
        difficulty: difficulty,
        language: language,
        score_to_win: (showAdvanced ? customScoreToWin : scoreToWin).toString(),
        team_count: teamCount.toString(),
        host_id: userId,
        show_translations: showTranslations.toString()
      });
      
      const fullUrl = `${API_URL}/rooms/create?${params}`;
      console.log('Creating room with URL:', fullUrl);
      console.log('API_URL:', API_URL);
      console.log('window.location:', window.location.href);
      
      const response = await fetch(fullUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      
      console.log('Response status:', response.status);
      console.log('Response ok:', response.ok);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Response error:', errorText);
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }
      
      const data = await response.json();
      console.log('Room created:', data);
      
      localStorage.setItem('username', username);
      // DON'T create new user_id - we already have it!
      // localStorage.setItem('user_id', userId); // Already saved above
      navigate(`/room/${data.room_code}`);
    } catch (error) {
      console.error('Failed to create room:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      alert(`Failed to create room: ${errorMessage}\nAPI_URL: ${API_URL}\nCheck console for details`);
    } finally {
      setLoading(false);
    }
  };

  const joinRoom = async () => {
    if (!username.trim()) {
      alert('Please enter your username');
      return;
    }
    
    if (!roomCode.trim() || roomCode.length !== 4) {
      alert('Please enter a valid 4-letter room code');
      return;
    }

    setLoading(true);
    try {
      // Get or create user_id (don't overwrite existing!)
      let userId = localStorage.getItem('user_id');
      if (!userId) {
        userId = Date.now().toString();
        localStorage.setItem('user_id', userId);
      }
      
      const response = await fetch(`${API_URL}/rooms/${roomCode.toUpperCase()}`);
      
      if (response.ok) {
        localStorage.setItem('username', username);
        navigate(`/room/${roomCode.toUpperCase()}`);
      } else {
        alert('Room not found');
      }
    } catch (error) {
      console.error('Failed to join room:', error);
      alert('Failed to join room. Make sure the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-8">
          <h1 className="text-5xl font-bold text-white mb-2">
            Alias & Taboo
          </h1>
          <p className="text-blue-200">Play word games with friends online</p>
        </div>

        <div className="bg-white rounded-lg shadow-xl p-8 space-y-6">
          {!showSettings ? (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Your Username
                </label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Enter your name"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  maxLength={20}
                />
              </div>

              <div className="space-y-3">
                <h2 className="text-lg font-semibold text-gray-800">Create New Game</h2>
                <button
                  onClick={() => openSettings('alias')}
                  disabled={loading}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-4 rounded-lg transition duration-200 disabled:opacity-50"
                >
                  Create Alias Game
                </button>
                <button
                  onClick={() => openSettings('taboo')}
                  disabled={loading}
                  className="w-full bg-purple-600 hover:bg-purple-700 text-white font-semibold py-3 px-4 rounded-lg transition duration-200 disabled:opacity-50"
                >
                  Create Taboo Game
                </button>
              </div>
            </>
          ) : (
            <>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold text-gray-800">Game Settings</h2>
                <button
                  onClick={() => setShowSettings(false)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  Back
                </button>
              </div>

              <div className="space-y-4">
                {/* Basic / Advanced Toggle */}
                <div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setShowAdvanced(false)}
                      className={`flex-1 py-2 px-4 rounded-lg font-medium transition ${
                        !showAdvanced
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                      }`}
                    >
                      Basic
                    </button>
                    <button
                      onClick={() => setShowAdvanced(true)}
                      className={`flex-1 py-2 px-4 rounded-lg font-medium transition ${
                        showAdvanced
                          ? 'bg-red-600 text-white'
                          : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                      }`}
                    >
                      Advanced
                    </button>
                  </div>
                </div>

                {showAdvanced ? (
                  <>
                    {/* Advanced: Custom Round Time */}
                    {timedMode && (
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Custom Round Time (seconds)
                        </label>
                        <input
                          type="number"
                          min="0"
                          max="1000"
                          value={customRoundTime}
                          onChange={(e) => setCustomRoundTime(Math.max(0, Math.min(1000, parseInt(e.target.value) || 0)))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        />
                        <p className="text-xs text-gray-500 mt-1">
                          {Math.floor(customRoundTime / 60)}:{(customRoundTime % 60).toString().padStart(2, '0')} (0-1000 seconds)
                        </p>
                      </div>
                    )}

                    {/* Advanced: Custom Score to Win */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Custom Score to Win
                      </label>
                      <input
                        type="number"
                        min="1"
                        max="500"
                        value={customScoreToWin}
                        onChange={(e) => setCustomScoreToWin(Math.max(1, Math.min(500, parseInt(e.target.value) || 1)))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                      />
                      <p className="text-xs text-gray-500 mt-1">1-500 points</p>
                    </div>

                    {/* Max Translations Limit */}
                    <div>
                      <div className="flex items-center space-x-3 mb-2">
                        <input
                          type="checkbox"
                          id="enableMaxTranslations"
                          checked={enableMaxTranslations}
                          onChange={(e) => setEnableMaxTranslations(e.target.checked)}
                          className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                        />
                        <label htmlFor="enableMaxTranslations" className="text-sm font-medium text-gray-700 cursor-pointer">
                          Limit Translations Per Round
                        </label>
                      </div>
                      
                      {enableMaxTranslations && (
                        <div>
                          <input
                            type="number"
                            min="1"
                            max="50"
                            value={maxTranslations}
                            onChange={(e) => setMaxTranslations(Math.max(1, Math.min(50, parseInt(e.target.value) || 10)))}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                          />
                          <p className="text-xs text-gray-500 mt-1">
                            Maximum {maxTranslations} translation{maxTranslations !== 1 ? 's' : ''} per round (1-50)
                          </p>
                        </div>
                      )}
                    </div>
                  </>
                ) : (
                  <>
                {/* Timer Mode */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Timer Mode
                  </label>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setTimedMode(true)}
                      className={`flex-1 py-2 px-4 rounded-lg font-medium transition ${
                        timedMode
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                      }`}
                    >
                      With Timer
                    </button>
                    <button
                      onClick={() => setTimedMode(false)}
                      className={`flex-1 py-2 px-4 rounded-lg font-medium transition ${
                        !timedMode
                          ? 'bg-blue-600 text-white'
                          : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                      }`}
                    >
                      Unlimited
                    </button>
                  </div>
                </div>

                {/* Round Time */}
                {timedMode && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Round Time
                    </label>
                    <div className="grid grid-cols-3 gap-2">
                      {[60, 180, 300].map((time) => (
                        <button
                          key={time}
                          onClick={() => setRoundTime(time)}
                          className={`py-2 px-4 rounded-lg font-medium transition ${
                            roundTime === time
                              ? 'bg-blue-600 text-white'
                              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                          }`}
                        >
                          {time / 60} min
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Language */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Language
                  </label>
                  <select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="en">English</option>
                    <option value="ru" disabled>Russian (coming soon)</option>
                  </select>
                </div>

                {/* Difficulty */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Difficulty
                  </label>
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      onClick={() => setDifficulty('easy')}
                      className={`py-2 px-4 rounded-lg font-medium transition ${
                        difficulty === 'easy'
                          ? 'bg-green-600 text-white'
                          : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                      }`}
                    >
                      Easy
                    </button>
                    <button
                      onClick={() => setDifficulty('medium')}
                      className={`py-2 px-4 rounded-lg font-medium transition ${
                        difficulty === 'medium'
                          ? 'bg-yellow-600 text-white'
                          : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                      }`}
                    >
                      Medium
                    </button>
                    <button
                      onClick={() => setDifficulty('hard')}
                      className={`py-2 px-4 rounded-lg font-medium transition ${
                        difficulty === 'hard'
                          ? 'bg-red-600 text-white'
                          : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                      }`}
                    >
                      Hard
                    </button>
                    <button
                      onClick={() => setDifficulty('mixed')}
                      className={`py-2 px-4 rounded-lg font-medium transition ${
                        difficulty === 'mixed'
                          ? 'bg-purple-600 text-white'
                          : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                      }`}
                    >
                      Random
                    </button>
                  </div>
                </div>

                {/* Score to Win */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Score to Win
                  </label>
                  <div className="grid grid-cols-3 gap-2">
                    {[30, 50, 100].map((score) => (
                      <button
                        key={score}
                        onClick={() => setScoreToWin(score)}
                        className={`py-2 px-4 rounded-lg font-medium transition ${
                          scoreToWin === score
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                        }`}
                      >
                        {score} pts
                      </button>
                    ))}
                  </div>
                </div>

                {/* Number of Teams */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Number of Teams
                  </label>
                  <div className="grid grid-cols-3 gap-2">
                    {[2, 3, 4].map((count) => (
                      <button
                        key={count}
                        onClick={() => setTeamCount(count)}
                        className={`py-2 px-4 rounded-lg font-medium transition ${
                          teamCount === count
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                        }`}
                      >
                        {count} teams
                      </button>
                    ))}
                  </div>
                </div>

                {/* Show Translations Checkbox */}
                <div className="flex items-center space-x-3 bg-gray-50 p-4 rounded-lg border border-gray-200">
                  <input
                    type="checkbox"
                    id="showTranslations"
                    checked={showTranslations}
                    onChange={(e) => setShowTranslations(e.target.checked)}
                    className="w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <label htmlFor="showTranslations" className="text-gray-700 font-medium cursor-pointer select-none">
                    Show Russian translations (для изучающих английский)
                  </label>
                </div>
                </>
                )}

                {/* Create Button */}
                <button
                  onClick={createRoom}
                  disabled={loading}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-4 rounded-lg transition duration-200 disabled:opacity-50 mt-6"
                >
                  {loading ? 'Creating...' : `Create ${selectedMode === 'alias' ? 'Alias' : 'Taboo'} Room`}
                </button>
              </div>
            </>
          )}

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white text-gray-500">Or</span>
            </div>
          </div>

          <div className="space-y-3">
            <h2 className="text-lg font-semibold text-gray-800">Join Existing Game</h2>
            <input
              type="text"
              value={roomCode}
              onChange={(e) => setRoomCode(e.target.value.toUpperCase())}
              placeholder="Enter 4-letter code"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent uppercase text-center text-2xl font-bold tracking-widest"
              maxLength={4}
            />
            <button
              onClick={joinRoom}
              disabled={loading}
              className="w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-4 rounded-lg transition duration-200 disabled:opacity-50"
            >
              Join Game
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HomePage;
