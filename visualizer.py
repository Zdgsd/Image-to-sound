import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import spectrogram

def show_spectrogram(audio_signal, sample_rate):
    # Compute spectrogram
    f, t, Sxx = spectrogram(audio_signal, sample_rate, nperseg=1024)

    # Convert power spectrogram to decibel scale (log)
    Sxx_dB = 10 * np.log10(Sxx + 1e-10)

    # Plot
    plt.figure(figsize=(10, 6))
    plt.pcolormesh(t, f, Sxx_dB, shading='gouraud', cmap='inferno')
    plt.ylabel('Frequency [Hz]')
    plt.xlabel('Time [sec]')
    plt.title('Spectrogram of Generated Audio')
    plt.colorbar(label='Intensity [dB]')
    plt.ylim(0, 10000)  # Limit to 10 kHz for clarity
    plt.tight_layout()
    plt.show()
