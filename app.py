import os
import numpy as np
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from scipy.signal import spectrogram
import sounddevice as sd
import soundfile as sf
import threading
import cv2

# === Image Loading and Processing ===
def load_and_prepare_image(image_path, width, height):
    try:
        image = Image.open(image_path).convert("L")
        image = image.resize((width, height))
        image_array = np.array(image) / 255.0
        return image_array
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load image:\n{e}")
        return None

def load_and_prepare_cv_image(cv_image, width, height):
    image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
    image = cv2.resize(image, (width, height))
    image_array = image.astype(np.float32) / 255.0
    return image_array

# === Audio Synthesis ===
def generate_audio_from_image(image_array, sample_rate, duration_per_column, min_freq, max_freq):
    height, width = image_array.shape
    output = []

    time = np.linspace(0, duration_per_column, int(sample_rate * duration_per_column), endpoint=False)
    freqs = np.linspace(min_freq, max_freq, height)

    for col in range(width):
        frame = np.zeros_like(time)
        for row in range(height):
            amp = image_array[height - row - 1, col]
            if amp > 0.01:
                frame += amp * np.sin(2 * np.pi * freqs[row] * time)
        output.append(frame)

    audio = np.concatenate(output)
    if np.max(np.abs(audio)) > 0:
        audio /= np.max(np.abs(audio))
    return audio.astype(np.float32)

# === Visualization ===
def create_spectrogram_figure(audio_signal, sample_rate):
    f, t, Sxx = spectrogram(audio_signal, sample_rate, nperseg=1024)
    Sxx_dB = 10 * np.log10(Sxx + 1e-10)

    fig, ax = plt.subplots(figsize=(8, 4))
    pcm = ax.pcolormesh(t, f, Sxx_dB, shading='gouraud', cmap='inferno')
    ax.set_ylabel('Frequency [Hz]')
    ax.set_xlabel('Time [sec]')
    ax.set_title('Spectrogram of Generated Audio')
    ax.set_ylim(0, sample_rate / 2)
    fig.colorbar(pcm, ax=ax, label='Intensity [dB]')
    plt.tight_layout()
    return fig

def create_waveform_figure(audio_signal, sample_rate):
    time = np.linspace(0, len(audio_signal) / sample_rate, num=len(audio_signal))
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(time, audio_signal, lw=0.5)
    ax.set_title('Waveform of Generated Audio')
    ax.set_xlabel('Time [sec]')
    ax.set_ylabel('Amplitude')
    plt.tight_layout()
    return fig

# === Main App ===
class ImageToSoundApp(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("Image to Sound - Drag & Drop with Settings")
        self.geometry("1000x700")
        self.resizable(False, False)

        self.audio_signal = None
        self.sample_rate = 44100
        self.is_playing = False

        self.current_image_path = None
        self.last_cv_frame = None
        self.view_mode = 'spectrogram'

        self.create_widgets()

    def create_widgets(self):
        settings = ttk.LabelFrame(self, text="Settings")
        settings.place(x=20, y=20, width=300, height=350)

        def add_slider(label_text, variable, row, from_, to, resolution):
            ttk.Label(settings, text=label_text).grid(row=row, column=0, sticky="w", padx=5, pady=5)
            scale = ttk.Scale(settings, variable=variable, from_=from_, to=to, orient="horizontal", length=120)
            scale.grid(row=row, column=1, padx=5, pady=5)
            scale.bind("<ButtonRelease-1>", lambda e: self.schedule_reprocess())
            return scale

        self.size_var = tk.DoubleVar(value=256)
        self.density_var = tk.DoubleVar(value=1.0)
        self.duration_var = tk.DoubleVar(value=6.0)
        self.min_freq_var = tk.DoubleVar(value=200)
        self.max_freq_var = tk.DoubleVar(value=8000)

        add_slider("Max Image Size:", self.size_var, 0, 64, 1024, 1)
        add_slider("Density:", self.density_var, 1, 0.1, 10.0, 0.1)
        add_slider("Duration (s):", self.duration_var, 2, 1, 20, 0.5)
        add_slider("Min Frequency:", self.min_freq_var, 3, 20, 1000, 10)
        add_slider("Max Frequency:", self.max_freq_var, 4, 1000, 20000, 100)

        ttk.Button(self, text="Save Output", command=self.save_audio).grid(row=5, column=0, columnspan=2, pady=5)

        self.drop_label = ttk.Label(self, text="Drag & drop image here\nor click Browse", background="#e0e0e0", relief="ridge", anchor="center", font=("Arial", 14))
        self.drop_label.place(x=350, y=20, width=620, height=140)
        self.drop_label.drop_target_register(DND_FILES)
        self.drop_label.dnd_bind('<<Drop>>', self.handle_drop)

        ttk.Button(self, text="Browse Image", command=self.browse_file).place(x=350, y=180)
        ttk.Button(self, text="Capture from Webcam", command=self.capture_from_webcam).place(x=470, y=180)
        self.play_button = ttk.Button(self, text="Play", command=self.play_audio, state="disabled")
        self.play_button.place(x=650, y=180)
        self.pause_button = ttk.Button(self, text="Pause", command=self.pause_audio, state="disabled")
        self.pause_button.place(x=720, y=180)
        self.toggle_view_button = ttk.Button(self, text="\ud83d\udcc8", command=self.toggle_view)
        self.toggle_view_button.place(x=800, y=180)

        self.figure_canvas = None

    def handle_drop(self, event):
        files = self.tk.splitlist(event.data)
        if files:
            self.process_image(files[0])

    def browse_file(self):
        path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg *.bmp *.gif")])
        if path:
            self.process_image(path)

    def capture_from_webcam(self):
        preview_window = tk.Toplevel(self)
        preview_window.title("Webcam Capture")
        preview_window.geometry("640x520")
        video_label = ttk.Label(preview_window)
        video_label.place(x=0, y=0, width=640, height=480)

        self._webcam_running = True
        self._captured_frame = None

        def on_capture():
            self._webcam_running = False
            if self._captured_frame is not None:
                self.last_cv_frame = self._captured_frame.copy()
                self.drop_label.config(text="Captured webcam frame")
                self.process_cv_image(self.last_cv_frame)
            preview_window.destroy()

        capture_btn = ttk.Button(preview_window, text="\ud83d\udcf8 Capture Frame", command=on_capture)
        capture_btn.place(x=260, y=485)

        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            messagebox.showerror("Error", "Webcam not available")
            preview_window.destroy()
            return

        def update_preview():
            if not self._webcam_running:
                cap.release()
                return
            ret, frame = cap.read()
            if not ret or frame is None:
                print("⚠️ Warning: Could not read frame from webcam.")
                preview_window.after(100, update_preview)
                return
            self._captured_frame = frame.copy()
            cv_img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(cv_img_rgb)
            img_tk = ImageTk.PhotoImage(image=img_pil)
            video_label.imgtk = img_tk
            video_label.configure(image=img_tk)
            preview_window.after(30, update_preview)

        update_preview()

    def process_cv_image(self, frame):
        max_size = int(self.size_var.get())
        density = self.density_var.get()
        width = max(1, int(max_size / density))
        height = width

        image_arr = load_and_prepare_cv_image(frame, width, height)
        duration = self.duration_var.get()
        duration_per_column = duration / width
        min_f = self.min_freq_var.get()
        max_f = self.max_freq_var.get()
        self.audio_signal = generate_audio_from_image(image_arr, self.sample_rate, duration_per_column, min_f, max_f)

        self.update_buttons()
        self.update_visual()

    def schedule_reprocess(self):
        if self.last_cv_frame is not None:
            self.process_cv_image(self.last_cv_frame)
        elif self.current_image_path:
            self.process_image(self.current_image_path)

    def process_image(self, path):
        self.current_image_path = path
        max_size = int(self.size_var.get())
        density = self.density_var.get()
        width = max(1, int(max_size / density))
        height = width

        self.drop_label.config(text=f"Processing {os.path.basename(path)}...")
        image_arr = load_and_prepare_image(path, width, height)
        if image_arr is None:
            self.drop_label.config(text="Failed to load image.")
            return

        duration = self.duration_var.get()
        duration_per_column = duration / width
        min_f = self.min_freq_var.get()
        max_f = self.max_freq_var.get()

        self.audio_signal = generate_audio_from_image(image_arr, self.sample_rate, duration_per_column, min_f, max_f)
        self.drop_label.config(text=f"Processed {os.path.basename(path)}")
        self.update_buttons()
        self.update_visual()

    def update_visual(self):
        if self.figure_canvas:
            self.figure_canvas.get_tk_widget().destroy()
        if self.view_mode == 'spectrogram':
            fig = create_spectrogram_figure(self.audio_signal, self.sample_rate)
        else:
            fig = create_waveform_figure(self.audio_signal, self.sample_rate)
        self.figure_canvas = FigureCanvasTkAgg(fig, master=self)
        self.figure_canvas.draw()
        self.figure_canvas.get_tk_widget().place(x=350, y=240, width=620, height=430)

    def toggle_view(self):
        self.view_mode = 'waveform' if self.view_mode == 'spectrogram' else 'spectrogram'
        self.update_visual()

    def save_audio(self):
        if self.audio_signal is None:
            return
        path = filedialog.asksaveasfilename(defaultextension=".wav", filetypes=[("WAV files", "*.wav")])
        if path:
            sf.write(path, self.audio_signal, self.sample_rate)

    def play_audio(self):
        if self.audio_signal is None or self.is_playing:
            return
        def run_play():
            self.is_playing = True
            self.update_buttons()
            sd.play(self.audio_signal, self.sample_rate)
            sd.wait()
            self.is_playing = False
            self.update_buttons()
        threading.Thread(target=run_play, daemon=True).start()

    def pause_audio(self):
        if self.is_playing:
            sd.stop()
            self.is_playing = False
            self.update_buttons()

    def update_buttons(self):
        if self.is_playing:
            self.play_button.config(state="disabled")
            self.pause_button.config(state="normal")
        else:
            state = "normal" if self.audio_signal is not None else "disabled"
            self.play_button.config(state=state)
            self.pause_button.config(state="disabled")

if __name__ == '__main__':
    app = ImageToSoundApp()
    app.mainloop()



