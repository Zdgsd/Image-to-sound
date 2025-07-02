# Image-to-Sound

**Image-to-Sound** is a project that converts images into sound, enabling an auditory representation of visual content. This application can be used for artistic, educational, or accessibility purposes, such as providing alternative ways for visually-impaired users to "perceive" images.

---

## Table of Contents

- [Features](#features)
- [How It Works](#how-it-works)
- [Installation](#installation)
- [Usage](#usage)
  - [Command Line Interface (CLI)](#command-line-interface-cli)
  - [API Usage](#api-usage)
  - [Example](#example)
- [Configuration](#configuration)
- [Supported Formats](#supported-formats)
- [Dependencies](#dependencies)
- [Project Structure](#project-structure)
- [Development](#development)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)

---

## Features

- Converts images (PNG, JPEG, etc.) to sound (WAV, MP3, etc.)
- Supports grayscale and color images
- Different sonification modes (e.g., pixel intensity, color mapping, frequency mapping)
- CLI and API interfaces
- Configurable parameters for sound generation (duration, pitch range, etc.)
- Batch processing
- Extensible design for custom mapping or effects

---

## How It Works

The application reads an input image and translates its pixel data into audio signals. For example, pixel brightness might map to sound frequency, or color channels might map to stereo panning or timbre. The generated audio is saved as a sound file or played back directly.

Typical steps:
1. **Image Loading:** The image is loaded and optionally resized or pre-processed.
2. **Mapping:** Each pixel or group of pixels is mapped to a sound parameter (like frequency, amplitude, or stereo position).
3. **Synthesis:** The mapped parameters are used to generate audio samples.
4. **Output:** The audio is saved to a file or streamed for playback.

---

## Installation

### Requirements

- Python 3.8+
- See [Dependencies](#dependencies) for required Python packages

### Clone the Repository

```sh
git clone https://github.com/Zdgsd/Image-to-sound.git
cd Image-to-sound
```

### Install Python Dependencies

It is recommended to use a virtual environment:

```sh
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

## Usage

### Command Line Interface (CLI)

The project provides a CLI for easy usage:

```sh
python image_to_sound.py --input path/to/image.png --output path/to/output.wav [options]
```

#### Options

- `--mode`         : Sonification mode (e.g., `intensity`, `color`, `frequency`)
- `--duration`     : Total duration of output audio (seconds)
- `--pitch-range`  : Frequency range, e.g., `200-2000`
- `--sample-rate`  : Audio sample rate (default: 44100)
- `--channel`      : Mono or stereo output
- `--play`         : Play result after generation
- `--batch`        : Directory of images to process

#### Example

```sh
python image_to_sound.py --input sample.jpg --output sample.wav --mode frequency --duration 10 --pitch-range 220-1760
```

### API Usage

You can import the core functionality as a Python module in your projects.

```python
from image_to_sound import ImageToSound

converter = ImageToSound(input_path="image.png", output_path="sound.wav", mode="frequency")
converter.convert()
```

---

## Configuration

You may configure the behavior via command-line flags, or by editing the `config.yaml` file (if provided).

Example `config.yaml`:

```yaml
mode: "frequency"
duration: 10
pitch_range: [220, 1760]
sample_rate: 44100
output_format: "wav"
```

---

## Supported Formats

- **Image Input:** PNG, JPG, BMP, GIF, TIFF
- **Audio Output:** WAV (default), MP3 (requires ffmpeg or pydub), FLAC, OGG (optional, depends on backend)

---

## Dependencies

- [Pillow](https://python-pillow.org/) (image processing)
- [NumPy](https://numpy.org/) (numerical operations)
- [SciPy](https://scipy.org/) (audio file output)
- [sounddevice](https://python-sounddevice.readthedocs.io/) or [pyaudio](https://people.csail.mit.edu/hubert/pyaudio/) (optional, for playback)
- [pydub](https://github.com/jiaaro/pydub) (optional, for MP3 output)
- [PyYAML](https://pyyaml.org/) (optional, for config files)

All required packages are listed in `requirements.txt`.

---

## Project Structure

```
Image-to-sound/
│
├── image_to_sound.py      # Main CLI and entry point
├── image_to_sound/        # Core module directory
│   ├── __init__.py
│   ├── core.py            # Main logic for conversion
│   ├── mapping.py         # Mapping strategies
│   ├── audio.py           # Audio synthesis and output
│   └── utils.py           # Utility functions
├── examples/              # Example images and outputs
├── requirements.txt
├── README.md
├── config.yaml            # Example config (optional)
└── tests/                 # Unit tests
```

---

## Development

### Setting Up

1. Fork and clone the repository
2. Set up the virtual environment and install dependencies
3. Make your changes on a separate branch

### Linting & Formatting

- Use `flake8` for linting and `black` for code formatting.

### Extending

- Add new mapping strategies in `image_to_sound/mapping.py`
- Add new CLI options in `image_to_sound.py`

---

## Testing

Run tests using:

```sh
pytest tests/
```

Ensure that all new features are covered by unit tests.

---

## Contributing

Contributions are welcome! Please open issues for bug reports or feature requests, and submit pull requests for improvements.

1. Fork the repository
2. Create a new branch (`git checkout -b feature/YourFeature`)
3. Commit your changes with clear messages
4. Push to your fork and submit a pull request

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Acknowledgments

- Inspired by various sonification projects and research.
- Thanks to contributors and open source communities for libraries used.

---
