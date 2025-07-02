from image_loader import load_and_prepare_image
from synth import generate_audio_from_image
from audio_output import save_wav_file
from visualizer import show_spectrogram

def main():
    # Load and prepare image
    image_array = load_and_prepare_image("assets/test_image.png", size=(256, 256))

    # Generate audio signal from image
    audio_signal, sample_rate = generate_audio_from_image(image_array)

    # Save audio to WAV file
    save_wav_file("output.wav", sample_rate, audio_signal)

    # Show spectrogram of generated audio
    show_spectrogram(audio_signal, sample_rate)

if __name__ == "__main__":
    main()
