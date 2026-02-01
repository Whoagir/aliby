#!/usr/bin/env python3
"""Generate simple sound effects as WAV files"""
import wave
import struct
import math

def generate_sine_wave(frequency, duration, sample_rate=44100, amplitude=0.5):
    """Generate a sine wave"""
    num_samples = int(sample_rate * duration)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        sample = amplitude * math.sin(2 * math.pi * frequency * t)
        samples.append(int(sample * 32767))
    return samples

def generate_chord(frequencies, duration, sample_rate=44100, amplitude=0.3):
    """Generate a chord (multiple frequencies)"""
    num_samples = int(sample_rate * duration)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        sample = 0
        for freq in frequencies:
            sample += (amplitude / len(frequencies)) * math.sin(2 * math.pi * freq * t)
        # Apply fade out
        fade_factor = 1.0 if t < duration * 0.7 else (duration - t) / (duration * 0.3)
        samples.append(int(sample * 32767 * fade_factor))
    return samples

def save_wav(filename, samples, sample_rate=44100):
    """Save samples as WAV file"""
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        for sample in samples:
            wav_file.writeframes(struct.pack('<h', sample))

# Generate sounds
output_dir = 'public/sounds/'

# 1. Start round - energetic ascending tone
print("Generating start-round.wav...")
samples = []
for freq in range(400, 801, 100):
    samples.extend(generate_sine_wave(freq, 0.06, amplitude=0.4))
save_wav(output_dir + 'start-round.wav', samples)

# 2. Guessed - happy chord (C5, E5, G5)
print("Generating guessed.wav...")
samples = generate_chord([523.25, 659.25, 783.99], 0.4, amplitude=0.3)
save_wav(output_dir + 'guessed.wav', samples)

# 3. Skip - sad descending tone
print("Generating skip.wav...")
samples = []
for freq in range(500, 249, -50):
    samples.extend(generate_sine_wave(freq, 0.04, amplitude=0.3))
save_wav(output_dir + 'skip.wav', samples)

# 4. Round end - dramatic finish
print("Generating round-end.wav...")
samples = generate_sine_wave(600, 0.2, amplitude=0.4)
samples.extend(generate_sine_wave(300, 0.3, amplitude=0.4))
save_wav(output_dir + 'round-end.wav', samples)

# 5. Tick - short beep for countdown
print("Generating tick.wav...")
samples = generate_sine_wave(800, 0.05, amplitude=0.2)
save_wav(output_dir + 'tick.wav', samples)

# 6. Final tick - higher pitch for last second
print("Generating final-tick.wav...")
samples = generate_sine_wave(1200, 0.08, amplitude=0.25)
save_wav(output_dir + 'final-tick.wav', samples)

print("Done! All sounds generated in", output_dir)
