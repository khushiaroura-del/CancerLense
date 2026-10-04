import json
from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from torchvision import transforms

from app.backend.ml.mobilenet_model import create_model


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

MODEL_DIR = PROJECT_ROOT / "models"
RESULTS_DIR = PROJECT_ROOT / "results"

GRADCAM_DIR = RESULTS_DIR / "gradcam"

MODEL_PATH = MODEL_DIR / "best_model.pth"

GRADCAM_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# DEVICE
# ============================================================

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ============================================================
# CLASS MAPPING
# IMPORTANT:
# 0 = cancer
# 1 = non-cancer
# ============================================================

CLASS_NAMES = {
    0: "cancer",
    1: "non_cancer",
}


# ============================================================
# IMAGE TRANSFORM
# ============================================================

transform = transforms.Compose(
    [
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ]
)


# ============================================================
# LOAD MODEL
# ============================================================

def load_model():
    model = create_model()

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Model checkpoint not found: {MODEL_PATH}"
        )

    checkpoint = torch.load(
        MODEL_PATH,
        map_location=DEVICE,
        weights_only=False,
    )

    if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
        model.load_state_dict(checkpoint["model_state_dict"])
    else:
        model.load_state_dict(checkpoint)

    model.to(DEVICE)
    model.eval()

    return model


# ============================================================
# IMAGE QUALITY
# ============================================================

def calculate_image_quality(image):
    """
    Calculates basic image-derived quality metrics.

    brightness:
        Mean grayscale intensity.

    sharpness:
        Variance of Laplacian.

    These are image quality indicators only.
    """

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    brightness = float(np.mean(gray))

    sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    height, width = gray.shape

    if width < 224 or height < 224:
        quality_status = "LOW_RESOLUTION"

    elif brightness < 35:
        quality_status = "TOO_DARK"

    elif brightness > 235:
        quality_status = "TOO_BRIGHT"

    elif sharpness < 20:
        quality_status = "BLURRY"

    else:
        quality_status = "ACCEPTABLE"

    return {
        "width": int(width),
        "height": int(height),
        "brightness": round(brightness, 2),
        "sharpness": round(sharpness, 2),
        "quality_status": quality_status,
    }


# ============================================================
# GRAD-CAM
# NATIVE PYTORCH IMPLEMENTATION
#
# This replaces pytorch-grad-cam completely.
# ============================================================

class NativeGradCAM:
    def __init__(self, model, target_layer):
        self.model = model
        self.target_layer = target_layer

        self.activations = None
        self.gradients = None

        self.forward_handle = target_layer.register_forward_hook(
            self._forward_hook
        )

    def _forward_hook(self, module, inputs, output):
        self.activations = output

        if isinstance(output, torch.Tensor):
            output.register_hook(self._gradient_hook)

    def _gradient_hook(self, grad):
        self.gradients = grad

    def remove(self):
        if self.forward_handle is not None:
            self.forward_handle.remove()

    def generate(self, input_tensor, target_class):
        self.model.zero_grad(set_to_none=True)

        output = self.model(input_tensor)

        target_score = output[:, target_class].sum()

        target_score.backward()

        if self.activations is None:
            raise RuntimeError(
                "Grad-CAM activation was not captured."
            )

        if self.gradients is None:
            raise RuntimeError(
                "Grad-CAM gradients were not captured."
            )

        activations = self.activations.detach()
        gradients = self.gradients.detach()

        # Global average pooling over spatial dimensions
        weights = gradients.mean(
            dim=(2, 3),
            keepdim=True,
        )

        cam = (weights * activations).sum(
            dim=1,
            keepdim=True,
        )

        cam = F.relu(cam)

        cam = F.interpolate(
            cam,
            size=(224, 224),
            mode="bilinear",
            align_corners=False,
        )

        cam = cam.squeeze(0).squeeze(0)

        cam = cam.cpu().numpy()

        cam_min = cam.min()
        cam_max = cam.max()

        if cam_max - cam_min > 1e-8:
            cam = (cam - cam_min) / (
                cam_max - cam_min
            )
        else:
            cam = np.zeros_like(cam)

        return cam


# ============================================================
# TARGET LAYER
# ============================================================

def get_target_layer(model):
    """
    CancerLenseModel contains the actual torchvision
    MobileNetV3 model under model.model.

    The final feature layer is used for Grad-CAM.
    """

    return model.model.features[-1]


# ============================================================
# GENERATE GRAD-CAM IMAGE
# ============================================================

def generate_gradcam(
    model,
    image_rgb,
    input_tensor,
    target_class,
    output_path,
):
    """
    Creates a Grad-CAM overlay.

    Important:
    Grad-CAM indicates image regions that influenced
    the model prediction.

    It is NOT a clinical lesion boundary.
    """

    target_layer = get_target_layer(model)

    gradcam = NativeGradCAM(
        model=model,
        target_layer=target_layer,
    )

    try:
        cam = gradcam.generate(
            input_tensor=input_tensor,
            target_class=target_class,
        )
    finally:
        gradcam.remove()

    # Original image resized to model input dimensions
    original_resized = cv2.resize(
        image_rgb,
        (224, 224),
    )

    # Convert CAM to 8-bit
    heatmap_uint8 = np.uint8(
        255 * cam
    )

    heatmap = cv2.applyColorMap(
        heatmap_uint8,
        cv2.COLORMAP_JET,
    )

    original_bgr = cv2.cvtColor(
        original_resized,
        cv2.COLOR_RGB2BGR,
    )

    overlay = cv2.addWeighted(
        original_bgr,
        0.55,
        heatmap,
        0.45,
        0,
    )

    cv2.imwrite(
        str(output_path),
        overlay,
    )

    return output_path


# ============================================================
# LESION CANDIDATE ESTIMATION
# ============================================================

def estimate_lesion_measurement(image_bgr):
    """
    Estimates a candidate abnormal-looking region using
    image processing.

    IMPORTANT:
    This is NOT a clinical lesion segmentation algorithm.

    Physical dimensions cannot be calculated without
    a valid calibration reference.
    """

    image = image_bgr.copy()

    height, width = image.shape[:2]

    hsv = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2HSV,
    )

    # HSV channels
    saturation = hsv[:, :, 1]
    value = hsv[:, :, 2]

    # Red / pink candidate regions
    red_1 = cv2.inRange(
        hsv,
        np.array([0, 45, 45]),
        np.array([15, 255, 255]),
    )

    red_2 = cv2.inRange(
        hsv,
        np.array([165, 45, 45]),
        np.array([180, 255, 255]),
    )

    red_mask = cv2.bitwise_or(
        red_1,
        red_2,
    )

    # Filter out extremely dark pixels
    valid_brightness = cv2.inRange(
        value,
        45,
        255,
    )

    mask = cv2.bitwise_and(
        red_mask,
        valid_brightness,
    )

    # Morphological cleanup
    kernel = np.ones(
        (7, 7),
        np.uint8,
    )

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_OPEN,
        kernel,
    )

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_CLOSE,
        kernel,
    )

    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    candidates = []

    image_area = width * height

    for contour in contours:
        area = cv2.contourArea(contour)

        if area < image_area * 0.002:
            continue

        if area > image_area * 0.80:
            continue

        x, y, w, h = cv2.boundingRect(contour)

        if w < 20 or h < 20:
            continue

        candidates.append(
            {
                "contour": contour,
                "area": float(area),
                "x": int(x),
                "y": int(y),
                "width": int(w),
                "height": int(h),
            }
        )

    if not candidates:
        return {
            "status": "NOT_ESTIMATED",
            "method": "image-based candidate region estimation",
            "width_pixels": None,
            "height_pixels": None,
            "area_pixels": None,
            "center": None,
            "bounding_box": None,
            "calibration_available": False,
            "physical_size": None,
            "note": (
                "No reliable candidate region was identified "
                "using the current image-based estimation method."
            ),
        }

    # Select largest reasonable candidate
    candidate = max(
        candidates,
        key=lambda item: item["area"],
    )

    x = candidate["x"]
    y = candidate["y"]
    w = candidate["width"]
    h = candidate["height"]
    area = candidate["area"]

    center_x = x + (w / 2)
    center_y = y + (h / 2)

    return {
        "status": "ESTIMATED",
        "method": "image-based candidate region estimation",
        "width_pixels": int(w),
        "height_pixels": int(h),
        "area_pixels": round(area, 2),
        "center": {
            "x": round(center_x, 2),
            "y": round(center_y, 2),
        },
        "bounding_box": {
            "x": int(x),
            "y": int(y),
            "width": int(w),
            "height": int(h),
        },
        "calibration_available": False,
        "physical_size": None,
        "note": (
            "Physical size in millimeters or centimeters "
            "cannot be determined without a valid image "
            "calibration reference."
        ),
    }


# ============================================================
# MAIN PREDICTION FUNCTION
# ============================================================

def predict_image(image_path):
    """
    Main CancerLense inference pipeline.

    Returns:
        quality
        screening signal
        prediction
        confidence
        class scores
        Grad-CAM
        lesion measurement
        recommendation
        research disclaimer
    """

    image_path = Path(image_path)

    if not image_path.exists():
        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    # --------------------------------------------------------
    # Load original image
    # --------------------------------------------------------

    image_bgr = cv2.imread(
        str(image_path)
    )

    if image_bgr is None:
        raise ValueError(
            "Unable to read image."
        )

    image_rgb = cv2.cvtColor(
        image_bgr,
        cv2.COLOR_BGR2RGB,
    )

    # --------------------------------------------------------
    # Image quality
    # --------------------------------------------------------

    quality = calculate_image_quality(
        image_bgr
    )

    # --------------------------------------------------------
    # Load model
    # --------------------------------------------------------

    model = load_model()

    # --------------------------------------------------------
    # Prepare input
    # --------------------------------------------------------

    pil_image = Image.fromarray(
        image_rgb
    )

    input_tensor = transform(
        pil_image
    ).unsqueeze(0)

    input_tensor = input_tensor.to(
        DEVICE
    )

    # --------------------------------------------------------
    # Prediction
    # --------------------------------------------------------

    with torch.no_grad():
        logits = model(
            input_tensor
        )

        probabilities = torch.softmax(
            logits,
            dim=1,
        )

    predicted_index = int(
        torch.argmax(
            probabilities,
            dim=1,
        ).item()
    )

    predicted_class = CLASS_NAMES[
        predicted_index
    ]

    confidence = float(
        probabilities[
            0,
            predicted_index
        ].item()
        * 100
    )

    cancer_score = float(
        probabilities[0, 0].item()
        * 100
    )

    non_cancer_score = float(
        probabilities[0, 1].item()
        * 100
    )

    # --------------------------------------------------------
    # Screening signal
    # --------------------------------------------------------

    if predicted_class == "cancer":
        screening_signal = "CANCER-CLASS SIGNAL"

        recommendation = (
            "Professional clinical examination "
            "is recommended for further evaluation."
        )

    else:
        screening_signal = "NON-CANCER-CLASS SIGNAL"

        recommendation = (
            "The image produced a non-cancer-class "
            "model signal. Clinical assessment may "
            "still be appropriate based on symptoms "
            "and professional evaluation."
        )

    # --------------------------------------------------------
    # Grad-CAM
    # --------------------------------------------------------

    gradcam_path = None

    gradcam_filename = (
        image_path.stem
        + "_gradcam.jpg"
    )

    gradcam_output = (
        GRADCAM_DIR
        / gradcam_filename
    )

    try:
        gradcam_path = generate_gradcam(
            model=model,
            image_rgb=image_rgb,
            input_tensor=input_tensor,
            target_class=predicted_index,
            output_path=gradcam_output,
        )

    except Exception as error:
        print(
            f"[CancerLense] Grad-CAM generation failed: {error}"
        )

        gradcam_path = None

    # --------------------------------------------------------
    # Lesion measurement
    # --------------------------------------------------------

    lesion_measurement = (
        estimate_lesion_measurement(
            image_bgr
        )
    )

    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    result = {
        "status": "ANALYZED",

        "quality": quality,

        "screening_signal": screening_signal,

        "prediction_class": predicted_class,

        "model_confidence": round(
            confidence,
            2,
        ),

        "class_scores": {
            "cancer": round(
                cancer_score,
                2,
            ),
            "non_cancer": round(
                non_cancer_score,
                2,
            ),
        },

        "recommendation": recommendation,

        "note": (
            "This is an AI-assisted research "
            "screening output and not a medical diagnosis."
        ),

        "gradcam": (
            str(gradcam_path)
            if gradcam_path
            else None
        ),

        "lesion_measurement": lesion_measurement,
    }

    return result


# ============================================================
# CLI SUPPORT
# ============================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="CancerLense image prediction"
    )

    parser.add_argument(
        "image",
        help="Path to image",
    )

    args = parser.parse_args()

    result = predict_image(
        args.image
    )

    print(
        json.dumps(
            result,
            indent=2,
        )
    )