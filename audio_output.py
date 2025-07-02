from scipy.io.wavfile import write

def save_wav_file(filename, sample_rate, audio_data):
    write(filename, sample_rate, (audio_data * 32767).astype("int16"))
