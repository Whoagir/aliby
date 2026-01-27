import React from 'react';
import { useParams } from 'react-router-dom';
import useGameWebSocket from '../hooks/useGameWebSocket';

const GamePage: React.FC = () => {
  const { code } = useParams<{ code: string }>();
  const { 
    gameState, 
    currentWord, 
    currentTabooWords,
    timeLeft, 
    isPaused,
    roundSummary,
    setRoundSummary,
    sendMessage 
  } = useGameWebSocket(code || '');

  const handleGuessed = () => {
    if (timeLeft > 0 || timeLeft === -1) {
      sendMessage({ 
        type: 'word_guessed',
        word: currentWord,
        taboo_words: currentTabooWords
      });
    }
  };

  const handleSkip = () => {
    if (timeLeft > 0 || timeLeft === -1) {
      sendMessage({ type: 'word_skip' });
    }
  };

  const handleTaboo = () => {
    if (timeLeft > 0 || timeLeft === -1) {
      sendMessage({ type: 'word_taboo' });
    }
  };

  const handlePauseToggle = () => {
    sendMessage({ type: isPaused ? 'resume_game' : 'pause_game' });
  };

  const handleRemoveWord = (word: string) => {
    sendMessage({ type: 'remove_word', word });
  };

  const handleConfirmRoundEnd = () => {
    setRoundSummary(null);
    sendMessage({ type: 'round_end' });
  };

  const handleStartRound = () => {
    const userId = localStorage.getItem('user_id') || '';
    sendMessage({ type: 'start_round', user_id: userId });
  };

  const userId = localStorage.getItem('user_id') || '';
  const teams = gameState?.teams || [];
  const mode = gameState?.mode || 'alias';
  const isTimeUp = timeLeft === 0 && currentWord; // Time up only if round was started
  const isUnlimitedTime = timeLeft === -1;
  const isRoundStarted = !!currentWord; // Round started if we have a word
  const needsStartButton = !currentWord && gameState?.status === 'playing'; // Show START ROUND button
  
  // Check if current user is in the playing team
  const currentTeam = teams[gameState?.current_team_index || 0];
  const isMyTeamPlaying = currentTeam?.players?.some(p => p.user_id === userId) || false;

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-6">
          <h1 className="text-3xl font-bold text-white mb-2">Room: {code}</h1>
          <div className="flex justify-center items-center gap-8">
            <div className="text-white">
              Round: {gameState?.current_round || 0}
            </div>
            <div className={`text-4xl font-bold ${
              isTimeUp ? 'text-red-500' : isUnlimitedTime ? 'text-green-400' : 'text-yellow-400'
            }`}>
              {isUnlimitedTime ? 'Unlimited' : isTimeUp ? 'TIME UP!' : `${timeLeft}s`}
            </div>
          </div>
        </div>

        {/* Score Board */}
        <div className={`grid gap-4 mb-8 ${teams.length === 2 ? 'grid-cols-2' : teams.length === 3 ? 'grid-cols-3' : 'grid-cols-2'}`}>
          {teams.map((team, index) => {
            const isCurrentTeam = index === gameState?.current_team_index;
            const hasExplainingPlayer = team.players.some(p => p.is_explaining);
            
            return (
              <div 
                key={team.id} 
                className={`rounded-lg p-4 relative ${
                  isCurrentTeam && hasExplainingPlayer
                    ? 'bg-green-500 text-white ring-4 ring-green-300 shadow-xl'
                    : 'bg-white text-gray-800'
                }`}
              >
                {isCurrentTeam && hasExplainingPlayer && (
                  <div className="absolute top-2 right-2 bg-yellow-400 text-black text-xs font-bold px-2 py-1 rounded">
                    NOW PLAYING
                  </div>
                )}
                <h3 className={`text-xl font-bold mb-2 ${isCurrentTeam && hasExplainingPlayer ? 'text-white' : 'text-gray-800'}`}>
                  {team.name}
                </h3>
                <div className={`text-3xl font-bold mb-2 ${isCurrentTeam && hasExplainingPlayer ? 'text-white' : 'text-blue-600'}`}>
                  {team.score} points
                </div>
                <div className={`text-sm ${isCurrentTeam && hasExplainingPlayer ? 'text-green-100' : 'text-gray-600'}`}>
                  {team.players.map(p => p.username).join(', ') || 'No players'}
                </div>
              </div>
            );
          })}
        </div>

        {/* Word Card */}
        <div className="bg-white rounded-lg shadow-2xl p-12 mb-6">
          <div className="text-center">
            {needsStartButton ? (
              <div className="py-8">
                {isMyTeamPlaying ? (
                  <button
                    onClick={handleStartRound}
                    className="bg-green-600 hover:bg-green-700 text-white font-bold py-6 px-12 rounded-lg text-3xl transition duration-200 shadow-lg"
                  >
                    START ROUND
                  </button>
                ) : (
                  <div className="text-3xl text-gray-400 py-8">
                    Waiting for {currentTeam?.name} to start...
                  </div>
                )}
              </div>
            ) : isRoundStarted ? (
              <>
                {isMyTeamPlaying ? (
                  <>
                    <div className={`text-6xl font-bold mb-8 ${
                      isPaused ? 'text-orange-500' : 'text-gray-800'
                    }`}>
                      {isPaused ? 'PAUSED' : currentWord}
                    </div>

                    {mode === 'taboo' && currentTabooWords.length > 0 && !isPaused && (
                      <div className="mb-8">
                        <p className="text-red-600 font-semibold mb-3">Forbidden words:</p>
                        <div className="flex flex-wrap justify-center gap-2">
                          {currentTabooWords.map((word, idx) => (
                            <span
                              key={idx}
                              className="bg-red-100 text-red-800 px-4 py-2 rounded-full font-medium"
                            >
                              {word}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                ) : (
                  <div className="text-3xl text-gray-600 py-8">
                    {isPaused ? 'Game Paused' : `Watching ${currentTeam?.name} play...`}
                  </div>
                )}
              </>
            ) : (
              <div className="text-3xl text-gray-400 py-8">
                Waiting...
              </div>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-center gap-4 flex-wrap">
          {isRoundStarted && !isTimeUp ? (
            <>
              {isMyTeamPlaying && (
                <>
                  <button
                    onClick={handleGuessed}
                    disabled={isPaused}
                    className={`font-bold py-4 px-8 rounded-lg text-xl transition duration-200 ${
                      isPaused 
                        ? 'bg-gray-400 cursor-not-allowed text-white'
                        : 'bg-green-600 hover:bg-green-700 text-white'
                    }`}
                  >
                    Guessed
                  </button>
                  
                  <button
                    onClick={handleSkip}
                    disabled={isPaused}
                    className={`font-bold py-4 px-8 rounded-lg text-xl transition duration-200 ${
                      isPaused 
                        ? 'bg-gray-400 cursor-not-allowed text-white'
                        : 'bg-yellow-600 hover:bg-yellow-700 text-white'
                    }`}
                  >
                    Skip
                  </button>

                  {mode === 'taboo' && (
                    <button
                      onClick={handleTaboo}
                      disabled={isPaused}
                      className={`font-bold py-4 px-8 rounded-lg text-xl transition duration-200 ${
                        isPaused 
                          ? 'bg-gray-400 cursor-not-allowed text-white'
                          : 'bg-red-600 hover:bg-red-700 text-white'
                      }`}
                    >
                      Taboo Violation
                    </button>
                  )}
                </>
              )}

              <button
                onClick={handlePauseToggle}
                className={`font-bold py-4 px-8 rounded-lg text-xl transition duration-200 ${
                  isPaused
                    ? 'bg-blue-600 hover:bg-blue-700 text-white'
                    : 'bg-orange-600 hover:bg-orange-700 text-white'
                }`}
              >
                {isPaused ? 'Resume' : 'Pause'}
              </button>
            </>
          ) : isTimeUp ? (
            <button
              onClick={() => setRoundSummary(roundSummary || [])}
              className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-6 px-12 rounded-lg text-2xl transition duration-200"
            >
              Review Round
            </button>
          ) : null}
        </div>

        {/* Round Summary Modal - ТОЛЬКО для играющей команды */}
        {roundSummary !== null && isMyTeamPlaying && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-hidden flex flex-col">
              <div className="p-6 border-b">
                <h2 className="text-3xl font-bold text-gray-800">Round Complete!</h2>
                <p className="text-gray-600 mt-2">
                  Review the words below. Remove any that shouldn't count (e.g., same root word).
                </p>
              </div>

              <div className="flex-1 overflow-y-auto p-6">
                {roundSummary.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">No words were guessed this round.</p>
                ) : (
                  <div className="space-y-3">
                    {roundSummary.map((gw, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition"
                      >
                        <div className="flex-1">
                          <div className="text-xl font-bold text-gray-800">{gw.word}</div>
                          {gw.taboo_words && gw.taboo_words.length > 0 && (
                            <div className="text-sm text-gray-600 mt-1">
                              Taboo: {gw.taboo_words.join(', ')}
                            </div>
                          )}
                        </div>
                        <button
                          onClick={() => handleRemoveWord(gw.word)}
                          className="bg-red-500 hover:bg-red-600 text-white font-semibold py-2 px-4 rounded-lg transition duration-200"
                        >
                          Remove
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="p-6 border-t bg-gray-50">
                <div className="flex justify-between items-center">
                  <div className="text-lg font-semibold text-gray-700">
                    Total: {roundSummary.length} word{roundSummary.length !== 1 ? 's' : ''}
                  </div>
                  <button
                    onClick={handleConfirmRoundEnd}
                    className="bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-8 rounded-lg text-xl transition duration-200"
                  >
                    Continue to Next Round
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default GamePage;
