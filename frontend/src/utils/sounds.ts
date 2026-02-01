/**
 * Sound effects player using WAV files
 */

class SoundPlayer {
  private sounds: Map<string, HTMLAudioElement> = new Map();
  private enabled: boolean = false;

  constructor() {
    // Preload all sound files
    this.loadSound('start-round', '/sounds/start-round.wav');
    this.loadSound('guessed', '/sounds/guessed.wav');
    this.loadSound('skip', '/sounds/skip.wav');
    this.loadSound('round-end', '/sounds/round-end.wav');
    this.loadSound('tick', '/sounds/tick.wav');
    this.loadSound('final-tick', '/sounds/final-tick.wav');
    
    console.log('SoundPlayer initialized with', this.sounds.size, 'sounds');
  }

  private loadSound(name: string, path: string) {
    const audio = new Audio(path);
    audio.preload = 'auto';
    this.sounds.set(name, audio);
    
    // Enable sounds on first user interaction
    audio.addEventListener('canplaythrough', () => {
      console.log('Sound loaded:', name);
    }, { once: true });
  }

  // Enable sounds after first user interaction
  enable() {
    if (!this.enabled) {
      this.enabled = true;
      console.log('Sounds enabled!');
    }
  }

  private play(name: string, volume: number = 0.5) {
    this.enable(); // Auto-enable on first play attempt
    
    const sound = this.sounds.get(name);
    if (sound) {
      sound.volume = volume;
      sound.currentTime = 0; // Reset to start
      console.log('Playing sound:', name, 'volume:', volume);
      sound.play()
        .then(() => console.log('Sound played:', name))
        .catch(err => console.warn('Sound play failed:', name, err.message));
    } else {
      console.error('Sound not found:', name);
    }
  }

  playStartRound() {
    this.play('start-round', 0.6);
  }

  playGuessed() {
    this.play('guessed', 0.5);
  }

  playSkip() {
    this.play('skip', 0.4);
  }

  playRoundEnd() {
    this.play('round-end', 0.6);
  }

  playTick() {
    this.play('tick', 0.3);
  }

  playFinalTick() {
    this.play('final-tick', 0.4);
  }
}

// Singleton instance
export const soundPlayer = new SoundPlayer();
