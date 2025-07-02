import numpy as np

def generate_audio_from_image(image_array, sample_rate=44100, duration_per_column=0.02):
    height, width = image_array.shape
    min_freq, max_freq = 200, 8000
    output = []

    time = np.linspace(0, duration_per_column, int(sample_rate * duration_per_column), endpoint=False)
    freqs = np.linspace(min_freq, max_freq, height)

    for col in range(width):
        frame = np.zeros_like(time)
        for row in range(height):
            amplitude = image_array[height - row - 1, col]
            if amplitude > 0.01:  # threshold to avoid silence
                frame += amplitude * np.sin(2 * np.pi * freqs[row] * time)
        output.append(frame)

    audio_signal = np.concatenate(output)
    audio_signal /= np.max(np.abs(audio_signal))  # Normalize
    return audio_signal.astype(np.float32), sample_rate
