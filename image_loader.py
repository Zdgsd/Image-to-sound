from PIL import Image
import numpy as np

def load_and_prepare_image(image_path, size=(256, 256)):
    image = Image.open(image_path).convert("L")  # Convert to grayscale
    image = image.resize(size)
    image_array = np.array(image) / 255.0  # Normalize to 0–1
    return image_array
