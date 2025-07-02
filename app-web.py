import streamlit as st
import numpy as np
from PIL import Image
import io
import matplotlib.pyplot as plt
from scipy.signal import spectrogram
import soundfile as sf

# === Image Processing ===
def load_and_prepare_image(image: Image.Image, width: int):
    img_gray = image.convert("L").resize((width, width))
    img_arr = np.array(img_gray) / 255.0
    return img_arr

# === Audio Generation ===
def generate_audio_from_image(image_array, sample_rate, duration_per_column, min_freq, max_freq):
    height, width = image_array.shape
    t = np.linspace(0, duration_per_column, int(sample_rate * duration_per_column), endpoint=False)
    freqs = np.linspace(min_freq, max_freq, height)
    output = [np.dot(image_array[:, col], np.sin(2 * np.pi * freqs[:, None] * t)) for col in range(width)]
    audio = np.concatenate(output)
    if np.max(np.abs(audio)) > 0:
        audio /= np.max(np.abs(audio))
    return audio.astype(np.float32)

# === Visualization ===
def plot_spectrogram(audio_signal, sample_rate):
    f, t_vals, Sxx = spectrogram(audio_signal, sample_rate, nperseg=1024)
    Sxx_dB = 10 * np.log10(Sxx + 1e-10)
    fig, ax = plt.subplots(figsize=(8, 3))
    pcm = ax.pcolormesh(t_vals, f, Sxx_dB, shading='gouraud', cmap='inferno')
    ax.set_ylabel('Frequency [Hz]')
    ax.set_xlabel('Time [sec]')
    ax.set_ylim(0, sample_rate/2)
    fig.colorbar(pcm, ax=ax, label='Intensity [dB]')
    plt.tight_layout()
    return fig

def plot_waveform(audio_signal, sample_rate):
    times = np.linspace(0, len(audio_signal) / sample_rate, num=len(audio_signal))
    fig, ax = plt.subplots(figsize=(8, 3))
    ax.plot(times, audio_signal, linewidth=0.5)
    ax.set_title('Waveform')
    ax.set_xlabel('Time [sec]')
    ax.set_ylabel('Amplitude')
    plt.tight_layout()
    return fig

# === Streamlit UI ===
st.title("Image to Sound Converter")

option = st.radio("Input method:", ["Upload Image", "Use Webcam"])

if option == "Upload Image":
    uploaded_file = st.file_uploader("Choose an image", type=["png", "jpg", "jpeg", "bmp"])
    if uploaded_file:
        image = Image.open(uploaded_file)
else:
    image = st.camera_input("Take a photo")

if image:
    st.image(image, caption="Input Image", use_column_width=True)

    max_size = st.slider("Max Size (image width/height)", 64, 1024, 256)
    duration = st.slider("Duration (seconds)", 1.0, 20.0, 6.0)
    min_freq = st.slider("Min Frequency (Hz)", 20, 1000, 200)
    max_freq = st.slider("Max Frequency (Hz)", 1000, 20000, 8000)

    img_arr = load_and_prepare_image(image, max_size)
    per_col_duration = duration / img_arr.shape[1]

    audio = generate_audio_from_image(img_arr, 44100, per_col_duration, min_freq, max_freq)

    view = st.radio("View:", ["Spectrogram", "Waveform"])
    if view == "Spectrogram":
        fig = plot_spectrogram(audio, 44100)
    else:
        fig = plot_waveform(audio, 44100)
    st.pyplot(fig)

    audio_bytes = io.BytesIO()
    sf.write(audio_bytes, audio, 44100, format='WAV')
    audio_bytes.seek(0)

    st.audio(audio_bytes.read(), format='audio/wav')

    st.download_button(
        label="Download WAV",
        data=audio_bytes,
        file_name="output.wav",
        mime="audio/wav"
    )
