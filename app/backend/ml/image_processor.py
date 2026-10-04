from pathlib import Path
import cv2
import numpy as np


SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".webp"}


def load_image(image_path: str):
    """
    Load an image using OpenCV.
    """

    path = Path(image_path)

    if not path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    if path.suffix.lower() not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported image format: {path.suffix}. "
            f"Supported formats: {SUPPORTED_FORMATS}"
        )

    image = cv2.imread(str(path))

    if image is None:
        raise ValueError("Unable to read the image.")

    return image


def assess_image_quality(image):
    """
    Perform basic image-quality checks.

    Returns:
        Dictionary containing:
        - width
        - height
        - brightness
        - sharpness
        - quality_status
    """

    height, width = image.shape[:2]

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    brightness = float(np.mean(gray))

    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    if width < 224 or height < 224:
        quality_status = "LOW_RESOLUTION"

    elif sharpness < 50:
        quality_status = "POSSIBLY_BLURRY"

    elif brightness < 40:
        quality_status = "TOO_DARK"

    elif brightness > 220:
        quality_status = "TOO_BRIGHT"

    else:
        quality_status = "ACCEPTABLE"

    return {
        "width": width,
        "height": height,
        "brightness": round(brightness, 2),
        "sharpness": round(sharpness, 2),
        "quality_status": quality_status,
    }


def preprocess_image(image, image_size=(224, 224)):
    """
    Prepare image for the future MobileNetV3 model.
    """

    resized = cv2.resize(image, image_size)

    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

    normalized = rgb.astype(np.float32) / 255.0

    return normalized


def process_image(image_path: str):
    """
    Complete basic CancerLens image-processing pipeline.
    """

    image = load_image(image_path)

    quality = assess_image_quality(image)

    processed = preprocess_image(image)

    return {
        "original_image": image,
        "processed_image": processed,
        "quality": quality,
    }


if __name__ == "__main__":
    print("CancerLens Image Processor")
    print("Module loaded successfully.")