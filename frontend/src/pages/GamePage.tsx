import React, { useEffect, useRef, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import useGameWebSocket from '../hooks/useGameWebSocket';
import { soundPlayer } from '../utils/sounds';
import Confetti from 'react-confetti';

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

const GamePage: React.FC = () => {
  const { encryptedLink } = useParams<{ encryptedLink: string }>();
  const navigate = useNavigate();
  
  const [roomCode, setRoomCode] = useState<string>('');
  const [decrypting, setDecrypting] = useState(true);
  
  const { 
    gameState, 
    currentWord, 
    currentTabooWords,
    currentTranslation,
    timeLeft, 
    isPaused,
    roundSummary,
    setRoundSummary,
    timerEnded,
    teamSelection,
    gameWinner,
    sendMessage 
  } = useGameWebSocket(roomCode);

  const [showTranslation, setShowTranslation] = useState(false);
  const [translationWasUsed, setTranslationWasUsed] = useState(false);

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
          navigate('/');
          return;
        }

        const data = await response.json();
        setRoomCode(data.room_code);
        setDecrypting(false);
      } catch (err) {
        navigate('/');
      }
    };

    decryptLink();
  }, [encryptedLink, navigate]);

  const handleGuessed = () => {
    if (timeLeft > 0 || timeLeft === -1 || timerEnded) {
      soundPlayer.playGuessed();
      sendMessage({ 
        type: 'word_guessed',
        word: currentWord,
        taboo_words: currentTabooWords,
        used_translation: translationWasUsed // Use flag, not current visibility
      });
      setShowTranslation(false); // Reset for next word
      setTranslationWasUsed(false); // Reset usage flag
    }
  };

  const handleSkip = () => {
    if (timeLeft > 0 || timeLeft === -1 || timerEnded) {
      soundPlayer.playSkip();
      sendMessage({ type: 'word_skip' });
      setShowTranslation(false); // Reset for next word
      setTranslationWasUsed(false); // Reset usage flag
    }
  };

  const handleTeamSelected = (teamId: number) => {
    sendMessage({ type: 'team_selected', team_id: teamId });
  };

  const handleEndRound = () => {
    // For unlimited mode - manually end the round
    sendMessage({ type: 'end_round' });
  };

  const handleTaboo = () => {
    if (timeLeft > 0 || timeLeft === -1) {
      soundPlayer.playSkip(); // Taboo uses skip sound (negative)
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
    soundPlayer.playStartRound();
    const userId = localStorage.getItem('user_id') || '';
    sendMessage({ type: 'start_round', user_id: userId });
  };

  const userId = localStorage.getItem('user_id') || '';
  const teams = gameState?.teams || [];
  const mode = gameState?.mode || 'alias';
  const isTimeUp = timerEnded; // Use backend flag for accurate timer end
  const isUnlimitedTime = timeLeft === -1;
  const isRoundStarted = !!currentWord; // Round started if we have a word
  const needsStartButton = !currentWord && gameState?.status === 'playing'; // Show START ROUND button
  
  // Check if current user is in the playing team
  const currentTeam = teams[gameState?.current_team_index || 0];
  const isMyTeamPlaying = currentTeam?.players?.some(p => p.user_id === userId) || false;

  // Reset translation visibility when new word arrives
  useEffect(() => {
    setShowTranslation(false);
  }, [currentWord]);

  // Track previous timeLeft for tick sounds
  const prevTimeLeftRef = useRef<number>(timeLeft);

  // Play sound effects based on timer
  useEffect(() => {
    const prevTime = prevTimeLeftRef.current;
    prevTimeLeftRef.current = timeLeft;

    // Skip if paused or unlimited time
    if (isPaused || timeLeft === -1) return;

    // Round ended (time reached 0)
    if (prevTime > 0 && timeLeft === 0) {
      soundPlayer.playRoundEnd();
    }
    // Last 5 seconds - play tick sound
    else if (timeLeft > 0 && timeLeft <= 5 && prevTime !== timeLeft) {
      if (timeLeft === 1) {
        soundPlayer.playFinalTick(); // Higher pitch for last second
      } else {
        soundPlayer.playTick();
      }
    }
  }, [timeLeft, isPaused]);

  if (decrypting || !roomCode) {
    return <div className="min-h-screen flex items-center justify-center text-white">Loading room...</div>;
  }

  if (!gameState) {
    return <div className="min-h-screen flex items-center justify-center text-white">Connecting to game...</div>;
  }

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-6">
          <h1 className="text-3xl font-bold text-white mb-2">Room: {roomCode}</h1>
          <div className="flex justify-center items-center gap-8">
            {gameState?.status === 'playing' && (
              <div className="text-white text-lg font-semibold">
                Round {gameState?.current_round || 1}
              </div>
            )}
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
                {(isMyTeamPlaying || gameState?.settings?.solo_device) ? (
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
                {(isMyTeamPlaying || gameState?.settings?.solo_device) ? (
                  <>
                    <div className={`text-6xl font-bold mb-4 ${
                      isPaused ? 'text-orange-500' : showTranslation ? 'text-blue-600' : 'text-gray-800'
                    }`}>
                      {isPaused ? 'PAUSED' : currentWord}
                    </div>

                    {/* Translation section */}
                    {!isPaused && gameState?.settings?.show_translations && currentTranslation && currentTranslation !== "" && (
                      <div className="mb-6">
                        {showTranslation && (
                          <div className="text-4xl text-blue-600 font-semibold mb-4">
                            {currentTranslation}
                          </div>
                        )}
                        <button
                          onClick={() => {
                            if (!translationWasUsed) {
                              setTranslationWasUsed(true); // Mark as used on first show
                            }
                            setShowTranslation(!showTranslation); // Toggle visibility
                          }}
                          className={`${
                            showTranslation 
                              ? 'bg-gray-500 hover:bg-gray-600' 
                              : 'bg-blue-500 hover:bg-blue-600'
                          } text-white font-semibold py-3 px-8 rounded-lg transition duration-200`}
                        >
                          {showTranslation ? 'Hide Translation' : `Show Translation ${translationWasUsed ? '' : '(-0.5 points)'}`}
                        </button>
                      </div>
                    )}

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
          {isRoundStarted && (timeLeft > 0 || timeLeft === -1 || timerEnded) ? (
            <>
              {(isMyTeamPlaying || gameState?.settings?.solo_device) && (
                <>
                  <button
                    onClick={handleGuessed}
                    disabled={isPaused && !timerEnded}
                    className={`font-bold py-4 px-8 rounded-lg text-xl transition duration-200 ${
                      isPaused && !timerEnded
                        ? 'bg-gray-400 cursor-not-allowed text-white'
                        : 'bg-green-600 hover:bg-green-700 text-white'
                    }`}
                  >
                    Guessed
                  </button>
                  
                  <button
                    onClick={handleSkip}
                    disabled={isPaused && !timerEnded}
                    className={`font-bold py-4 px-8 rounded-lg text-xl transition duration-200 ${
                      isPaused && !timerEnded
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

                  {isUnlimitedTime && (
                    <button
                      onClick={handleEndRound}
                      disabled={isPaused}
                      className={`font-bold py-4 px-8 rounded-lg text-xl transition duration-200 ${
                        isPaused 
                          ? 'bg-gray-400 cursor-not-allowed text-white'
                          : 'bg-purple-600 hover:bg-purple-700 text-white'
                      }`}
                    >
                      End Round
                    </button>
                  )}
                </>
              )}

              {!timerEnded && (
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
              )}
            </>
          ) : null}
        </div>

        {/* Team Selection Modal - for last word after timer ended */}
        {teamSelection && (isMyTeamPlaying || gameState?.settings?.solo_device) && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg shadow-2xl max-w-md w-full">
              <div className="p-6 border-b">
                <h2 className="text-3xl font-bold text-gray-800">Who guessed it?</h2>
                <p className="text-gray-600 mt-2">
                  Last word: <span className="font-bold text-blue-600">{teamSelection.last_word}</span>
                </p>
              </div>

              <div className="p-6">
                <div className="space-y-3">
                  {teamSelection.teams.map((team) => (
                    <button
                      key={team.id}
                      onClick={() => handleTeamSelected(team.id)}
                      className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 px-6 rounded-lg text-xl transition duration-200"
                    >
                      {team.name}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Round Summary Modal - для играющей команды или solo device */}
        {roundSummary !== null && (isMyTeamPlaying || gameState?.settings?.solo_device) && (
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
                          <div className="flex items-baseline gap-2">
                            <div className="text-xl font-bold text-gray-800">{gw.word}</div>
                            {gameState?.settings?.show_translations && gw.translation && (
                              <div className="text-lg text-blue-600">({gw.translation})</div>
                            )}
                          </div>
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

        {/* Winner Screen - Full Page Overlay */}
        {gameWinner && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-80">
            <Confetti
              width={window.innerWidth}
              height={window.innerHeight}
              numberOfPieces={500}
              recycle={true}
            />
            <div className="text-center z-10 animate-bounce-in">
              <h1 className="text-8xl font-bold text-yellow-400 mb-8 animate-pulse">
                🎉 {gameWinner.winner} WINS! 🎉
              </h1>
              <div className="bg-white bg-opacity-20 backdrop-blur-md rounded-3xl p-8 mb-8">
                <h2 className="text-3xl font-bold text-white mb-4">Final Scores</h2>
                <div className="space-y-2">
                  {Object.entries(gameWinner.scores).map(([team, score]) => (
                    <div key={team} className={`text-2xl font-semibold ${team === gameWinner.winner ? 'text-yellow-300' : 'text-white'}`}>
                      {team}: {score} points
                    </div>
                  ))}
                </div>
              </div>
              <button
                onClick={() => navigate('/')}
                className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-bold py-4 px-12 rounded-full text-2xl transition duration-300 transform hover:scale-110 shadow-2xl"
              >
                Back to Lobby
              </button>
            </div>
          </div>
        )}

        {/* Exit to Lobby Button - Always visible */}
        <button
          onClick={() => {
            if (window.confirm('Exit to lobby? (Game will pause if you are playing)')) {
              navigate('/');
            }
          }}
          className="fixed top-4 right-4 bg-red-500 hover:bg-red-600 text-white font-bold py-2 px-6 rounded-lg transition duration-200"
        >
          Exit to Lobby
        </button>
      </div>
    </div>
  );
};

export default GamePage;
