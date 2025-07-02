import os
import numpy as np
from PIL import Image
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
    gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, (width, height))
    return resized.astype(np.float32) / 255.0

# === Audio Synthesis ===
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
def create_spectrogram_figure(audio_signal, sample_rate):
    f, t_vals, Sxx = spectrogram(audio_signal, sample_rate, nperseg=1024)
    Sxx_dB = 10 * np.log10(Sxx + 1e-10)
    fig, ax = plt.subplots(figsize=(8, 4))
    pcm = ax.pcolormesh(t_vals, f, Sxx_dB, shading='gouraud', cmap='inferno')
    ax.set_ylabel('Frequency [Hz]')
    ax.set_xlabel('Time [sec]')
    ax.set_title('Spectrogram')
    ax.set_ylim(0, sample_rate/2)
    fig.colorbar(pcm, ax=ax, label='Intensity [dB]')
    plt.tight_layout()
    return fig

def create_waveform_figure(audio_signal, sample_rate):
    times = np.linspace(0, len(audio_signal)/sample_rate, num=len(audio_signal))
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(times, audio_signal, linewidth=0.5)
    ax.set_title('Waveform')
    ax.set_xlabel('Time [sec]')
    ax.set_ylabel('Amplitude')
    plt.tight_layout()
    return fig

# === Webcam Capture Helper ===
def webcam_capture(callback):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        messagebox.showerror("Error", "Webcam not available")
        return
    captured_frame = [None]
    def do_capture():
        captured_frame[0] = frame.copy()
        cap.release()
        cv2.destroyAllWindows()
        callback(captured_frame[0])
    cv2.namedWindow('Webcam')
    cv2.setMouseCallback('Webcam', lambda event,x,y,f,p: do_capture() if event == cv2.EVENT_LBUTTONDOWN else None)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.flip(frame,1)
        disp = frame.copy()
        cv2.putText(disp, 'Click or SPACE to capture', (10, disp.shape[0]-20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)
        cv2.imshow('Webcam', disp)
        key = cv2.waitKey(1)
        if key == 32:  # SPACE
            do_capture()
            break
        if key == 27:  # ESC
            break
    cap.release()
    cv2.destroyAllWindows()

# === Main Application ===
class ImageToSoundApp(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title('Image to Sound Converter')
        self.geometry('1000x700')
        self.resizable(False, False)
        self.audio_signal = None
        self.sample_rate = 44100
        self.is_playing = False
        self.current_path = None
        self.slider_job = None
        self.view_mode = 'spectrogram'
        self._build_ui()

    def _build_ui(self):
        p = ttk.LabelFrame(self, text='Settings')
        p.place(x=20, y=20, width=300, height=350)

        def mk_slider(label, default, row, mn, mx):
            var = tk.DoubleVar(value=default)
            setattr(self, f"{label.lower().replace(' ', '_')}_var", var)
            ttk.Label(p, text=label).grid(row=row, column=0, padx=5, pady=5, sticky='w')
            slider = ttk.Scale(p, variable=var, from_=mn, to=mx, orient='horizontal', command=self._schedule)
            slider.grid(row=row, column=1, padx=5, pady=5)

        mk_slider('Max Size', 256, 0, 64, 1024)
        mk_slider('Density', 1.0, 1, 0.1, 10)
        mk_slider('Duration', 6.0, 2, 1, 20)
        mk_slider('Min Freq', 200, 3, 20, 1000)
        mk_slider('Max Freq', 8000, 4, 1000, 20000)

        ttk.Button(p, text='Save Output', command=self._save).grid(row=5, column=0, columnspan=2, pady=5)

        self.drop_lbl = ttk.Label(self, text='Drag & drop or Browse', relief='ridge', anchor='center')
        self.drop_lbl.place(x=350, y=20, width=620, height=140)
        self.drop_lbl.drop_target_register(DND_FILES)
        self.drop_lbl.dnd_bind('<<Drop>>', lambda e: self._load(e.data))

        ttk.Button(self, text='Browse', command=self._browse).place(x=350, y=180)
        ttk.Button(self, text='Webcam', command=lambda: webcam_capture(self._process_frame)).place(x=450, y=180)
        self.play_btn = ttk.Button(self, text='Play', command=self._play, state='disabled')
        self.play_btn.place(x=550, y=180)
        self.pause_btn = ttk.Button(self, text='Pause', command=lambda: sd.stop(), state='disabled')
        self.pause_btn.place(x=620, y=180)
        self.toggle_btn = ttk.Button(self, text='Toggle View', command=self._toggle)
        self.toggle_btn.place(x=690, y=180)

        self.canvas = None

    def _schedule(self, *_):
        if self.slider_job:
            self.after_cancel(self.slider_job)
        self.slider_job = self.after(150, self._reload)

    def _reload(self):
        if self.current_path:
            self._process_path(self.current_path)

    def _load(self, path):
        self._process_path(path)

    def _browse(self):
        path = filedialog.askopenfilename(filetypes=[('Images', '*.png;*.jpg;*.bmp')])
        if path:
            self._process_path(path)

    def _process_path(self, path):
        self.current_path = path
        self.drop_lbl.config(text=os.path.basename(path))
        sz = int(self.max_size_var.get())
        dt = self.duration_var.get()
        dns = self.density_var.get()
        minf = self.min_freq_var.get()
        maxf = self.max_freq_var.get()
        w = max(1, int(sz / dns))
        img = load_and_prepare_image(path, w, w)
        if img is None:
            return
        per = dt / w
        self.audio_signal = generate_audio_from_image(img, self.sample_rate, per, minf, maxf)
        self._update_buttons()
        self._show()

    def _process_frame(self, frame):
        sz = int(self.max_size_var.get())
        dt = self.duration_var.get()
        dns = self.density_var.get()
        minf = self.min_freq_var.get()
        maxf = self.max_freq_var.get()
        w = max(1, int(sz / dns))
        arr = load_and_prepare_cv_image(frame, w, w)
        per = dt / w
        self.audio_signal = generate_audio_from_image(arr, self.sample_rate, per, minf, maxf)
        self._update_buttons()
        self._show()

    def _show(self):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        fig = create_spectrogram_figure(self.audio_signal, self.sample_rate) if self.view_mode == 'spectrogram' else create_waveform_figure(self.audio_signal, self.sample_rate)
        self.canvas = FigureCanvasTkAgg(fig, self)
        self.canvas.draw()
        self.canvas.get_tk_widget().place(x=350, y=240, width=620, height=430)

    def _toggle(self):
        self.view_mode = 'waveform' if self.view_mode == 'spectrogram' else 'spectrogram'
        self._show()

    def _play(self):
        if self.audio_signal is None or self.is_playing:
            return

        def run():
            self.is_playing = True
            self._update_buttons()
            sd.play(self.audio_signal, self.sample_rate)
            sd.wait()
            self.is_playing = False
            self._update_buttons()

        threading.Thread(target=run, daemon=True).start()

    def _update_buttons(self):
        state = 'normal' if self.audio_signal is not None and not self.is_playing else 'disabled'
        self.play_btn.config(state=state)
        self.pause_btn.config(state='normal' if self.is_playing else 'disabled')

    def _save(self):
        if self.audio_signal is None:
            return
        path = filedialog.asksaveasfilename(defaultextension='.wav', filetypes=[('WAV', '.wav')])
        if path:
            sf.write(path, self.audio_signal, self.sample_rate)

if __name__ == '__main__':
    app = ImageToSoundApp()
    app.mainloop()



