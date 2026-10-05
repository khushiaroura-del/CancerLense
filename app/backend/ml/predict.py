"""
CancerLense Prediction Pipeline

AI-assisted oral lesion screening research prototype.

Pipeline:
1. Image loading
2. Image quality assessment
3. Smart Capture Coach
4. MobileNetV3 classification
5. Native PyTorch Grad-CAM
6. Image-based lesion candidate estimation

IMPORTANT:
- This is a research screening prototype.
- It is NOT a medical diagnosis.
- Model confidence is NOT clinical certainty.
- Grad-CAM shows regions influential to the model,
  not a clinically confirmed lesion boundary.
- Patient context does not modify model prediction.
- Physical lesion dimensions require calibration.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from torchvision import transforms

from app.backend.ml.capture_coach import evaluate_capture
from app.backend.ml.lesion_measurement import (
    estimate_lesion_measurement,
)
from app.backend.ml.mobilenet_model import create_model


# ============================================================
# PATH CONFIGURATION
# ============================================================

# predict.py is located at:
# CancerLens/app/backend/ml/predict.py
#
# parents[0] = ml
# parents[1] = backend
# parents[2] = app
# parents[3] = CancerLens
#
# Therefore parents[3] is the project root.

PROJECT_ROOT = Path(
    __file__
).resolve().parents[3]

MODEL_DIR = (
    PROJECT_ROOT / "models"
)

RESULTS_DIR = (
    PROJECT_ROOT / "results"
)

GRADCAM_DIR = (
    RESULTS_DIR / "gradcam"
)

MODEL_PATH = (
    MODEL_DIR / "best_model.pt"
)

GRADCAM_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# DEVICE
# ============================================================

DEVICE = torch.device(
    "cuda"
    if torch.cuda.is_available()
    else "cpu"
)


# ============================================================
# CLASS LABELS
# ============================================================

CLASS_NAMES = [
    "non_cancer",
    "cancer",
]


# ============================================================
# IMAGE TRANSFORM
# ============================================================

IMAGE_SIZE = 224

INFERENCE_TRANSFORM = transforms.Compose(
    [
        transforms.Resize(
            (
                IMAGE_SIZE,
                IMAGE_SIZE,
            )
        ),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[
                0.485,
                0.456,
                0.406,
            ],
            std=[
                0.229,
                0.224,
                0.225,
            ],
        ),
    ]
)


# ============================================================
# MODEL LOADING
# ============================================================

def load_model() -> torch.nn.Module:
    """
    Load the trained CancerLense MobileNetV3 model.
    """

    print(
        f"Loading model from: {MODEL_PATH}",
        file=sys.stderr,
    )

    if not MODEL_PATH.exists():

        raise FileNotFoundError(
            f"Model checkpoint not found: {MODEL_PATH}"
        )

    model = create_model()

    checkpoint = torch.load(
        MODEL_PATH,
        map_location=DEVICE,
    )

    # --------------------------------------------------------
    # Support different checkpoint formats
    # --------------------------------------------------------

    if (
        isinstance(
            checkpoint,
            dict,
        )
        and "model_state_dict" in checkpoint
    ):

        state_dict = checkpoint[
            "model_state_dict"
        ]

    elif (
        isinstance(
            checkpoint,
            dict,
        )
        and "state_dict" in checkpoint
    ):

        state_dict = checkpoint[
            "state_dict"
        ]

    else:

        state_dict = checkpoint

    # --------------------------------------------------------
    # Remove DataParallel prefix if present
    # --------------------------------------------------------

    cleaned_state_dict = {}

    for key, value in state_dict.items():

        if key.startswith(
            "module."
        ):

            key = key[
                len("module.") :
            ]

        cleaned_state_dict[
            key
        ] = value

    # --------------------------------------------------------
    # Load weights
    # --------------------------------------------------------

    model.load_state_dict(
        cleaned_state_dict,
        strict=False,
    )

    model.to(
        DEVICE
    )

    model.eval()

    return model


# ============================================================
# IMAGE QUALITY
# ============================================================

def calculate_image_quality(
    image_bgr: np.ndarray,
) -> dict[str, Any]:
    """
    Calculate basic technical image-quality metrics.

    These metrics describe the image only.
    They do not indicate disease severity.
    """

    if (
        image_bgr is None
        or image_bgr.size == 0
    ):

        raise ValueError(
            "Invalid image supplied."
        )

    height, width = (
        image_bgr.shape[:2]
    )

    gray = cv2.cvtColor(
        image_bgr,
        cv2.COLOR_BGR2GRAY,
    )

    brightness = float(
        np.mean(gray)
    )

    sharpness = float(
        cv2.Laplacian(
            gray,
            cv2.CV_64F,
        ).var()
    )

    # --------------------------------------------------------
    # Technical quality classification
    # --------------------------------------------------------

    if (
        width < 224
        or height < 224
    ):

        quality_status = "POOR"

    elif (
        sharpness < 20
        or brightness < 25
        or brightness > 245
    ):

        quality_status = "POOR"

    elif (
        sharpness < 60
        or brightness < 45
        or brightness > 225
    ):

        quality_status = "FAIR"

    else:

        quality_status = "ACCEPTABLE"

    return {
        "width": int(width),
        "height": int(height),
        "brightness": round(
            brightness,
            2,
        ),
        "sharpness": round(
            sharpness,
            2,
        ),
        "quality_status": quality_status,
    }


# ============================================================
# NATIVE GRAD-CAM
# ============================================================

class NativeGradCAM:
    """
    Native PyTorch Grad-CAM implementation.

    This avoids the external pytorch-grad-cam package.
    """

    def __init__(
        self,
        model: torch.nn.Module,
        target_layer: torch.nn.Module,
    ):

        self.model = model
        self.target_layer = target_layer

        self.activations = None
        self.gradients = None

        self.forward_handle = (
            target_layer.register_forward_hook(
                self._forward_hook
            )
        )

        self.backward_handle = (
            target_layer.register_full_backward_hook(
                self._backward_hook
            )
        )

    def _forward_hook(
        self,
        module,
        inputs,
        output,
    ):

        self.activations = output

    def _backward_hook(
        self,
        module,
        grad_input,
        grad_output,
    ):

        if grad_output:

            self.gradients = (
                grad_output[0]
            )

    def remove_hooks(
        self,
    ):

        self.forward_handle.remove()

        self.backward_handle.remove()

    def generate(
        self,
        input_tensor: torch.Tensor,
        target_class: int,
    ) -> np.ndarray:

        self.model.zero_grad(
            set_to_none=True
        )

        self.activations = None
        self.gradients = None

        output = self.model(
            input_tensor
        )

        target = output[
            0,
            target_class
        ]

        target.backward(
            retain_graph=True
        )

        if (
            self.activations is None
            or self.gradients is None
        ):

            raise RuntimeError(
                "Grad-CAM activations or gradients "
                "were not captured."
            )

        activations = (
            self.activations.detach()
        )

        gradients = (
            self.gradients.detach()
        )

        # Global average pooling of gradients.
        weights = gradients.mean(
            dim=(2, 3),
            keepdim=True,
        )

        cam = (
            weights * activations
        ).sum(
            dim=1,
            keepdim=True,
        )

        cam = F.relu(
            cam
        )

        cam = cam[
            0,
            0
        ].cpu().numpy()

        # Normalize to 0-1.
        cam -= cam.min()

        max_value = cam.max()

        if max_value > 0:

            cam /= max_value

        return cam


# ============================================================
# GRAD-CAM TARGET LAYER
# ============================================================

def get_gradcam_target_layer(
    model: torch.nn.Module,
) -> torch.nn.Module:
    """
    Select the final convolutional feature layer
    of MobileNetV3 Small.
    """

    try:

        return model.model.features[-1]

    except Exception as exc:

        raise RuntimeError(
            "Unable to locate MobileNetV3 target layer."
        ) from exc


# ============================================================
# GRAD-CAM GENERATION
# ============================================================

def generate_gradcam(
    model: torch.nn.Module,
    image_bgr: np.ndarray,
    input_tensor: torch.Tensor,
    target_class: int,
    output_path: Path,
) -> None:
    """
    Generate and save Grad-CAM overlay.
    """

    target_layer = (
        get_gradcam_target_layer(
            model
        )
    )

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

        gradcam.remove_hooks()

    height, width = (
        image_bgr.shape[:2]
    )

    cam_resized = cv2.resize(
        cam,
        (
            width,
            height,
        ),
        interpolation=cv2.INTER_LINEAR,
    )

    cam_uint8 = np.uint8(
        cam_resized * 255
    )

    heatmap = cv2.applyColorMap(
        cam_uint8,
        cv2.COLORMAP_JET,
    )

    overlay = cv2.addWeighted(
        image_bgr,
        0.55,
        heatmap,
        0.45,
        0,
    )

    cv2.imwrite(
        str(output_path),
        overlay,
    )


# ============================================================
# MODEL PREDICTION
# ============================================================

def run_model_prediction(
    model: torch.nn.Module,
    image_pil: Image.Image,
) -> dict[str, Any]:
    """
    Run MobileNetV3 classification.
    """

    input_tensor = (
        INFERENCE_TRANSFORM(
            image_pil
        )
        .unsqueeze(0)
        .to(DEVICE)
    )

    with torch.no_grad():

        logits = model(
            input_tensor
        )

        probabilities = torch.softmax(
            logits,
            dim=1,
        )[0]

    predicted_index = int(
        torch.argmax(
            probabilities
        ).item()
    )

    prediction_class = (
        CLASS_NAMES[
            predicted_index
        ]
    )

    class_scores = {}

    for index, class_name in enumerate(
        CLASS_NAMES
    ):

        class_scores[
            class_name
        ] = round(
            float(
                probabilities[
                    index
                ].item()
                * 100
            ),
            2,
        )

    model_confidence = round(
        float(
            probabilities[
                predicted_index
            ].item()
            * 100
        ),
        2,
    )

    return {
        "input_tensor": input_tensor,
        "prediction_class": prediction_class,
        "predicted_index": predicted_index,
        "model_confidence": model_confidence,
        "class_scores": class_scores,
    }


# ============================================================
# SCREENING SIGNAL
# ============================================================

def get_screening_signal(
    prediction_class: str,
) -> str:
    """
    Convert model output into a research screening signal.
    """

    if prediction_class == "cancer":

        return "CANCER-CLASS SIGNAL"

    return "NON-CANCER-CLASS SIGNAL"


# ============================================================
# RECOMMENDATION
# ============================================================

def get_recommendation(
    prediction_class: str,
) -> str:
    """
    Generate research workflow recommendation.

    This is not a medical diagnosis.
    """

    if prediction_class == "cancer":

        return (
            "Professional clinical examination is "
            "recommended for further evaluation."
        )

    return (
        "No cancer-class signal was identified by "
        "the current research model. Clinical evaluation "
        "may still be appropriate based on symptoms or "
        "professional assessment."
    )


# ============================================================
# MAIN PREDICTION PIPELINE
# ============================================================

def predict_image(
    image_path: str | Path,
) -> dict[str, Any]:
    """
    Complete CancerLense inference pipeline.
    """

    image_path = Path(
        image_path
    )

    if not image_path.exists():

        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    # --------------------------------------------------------
    # Read image
    # --------------------------------------------------------

    image_bgr = cv2.imread(
        str(image_path)
    )

    if image_bgr is None:

        raise ValueError(
            f"Unable to read image: {image_path}"
        )

    # --------------------------------------------------------
    # Convert BGR → RGB
    # --------------------------------------------------------

    image_rgb = cv2.cvtColor(
        image_bgr,
        cv2.COLOR_BGR2RGB,
    )

    image_pil = Image.fromarray(
        image_rgb
    )

    # --------------------------------------------------------
    # Load model
    # --------------------------------------------------------

    model = load_model()

    # --------------------------------------------------------
    # Image quality
    # --------------------------------------------------------

    quality = (
        calculate_image_quality(
            image_bgr
        )
    )

    # --------------------------------------------------------
    # Smart Capture Coach
    # --------------------------------------------------------

    capture_coach = (
        evaluate_capture(
            image_bgr
        )
    )

    # --------------------------------------------------------
    # MobileNetV3 prediction
    # --------------------------------------------------------

    prediction = (
        run_model_prediction(
            model=model,
            image_pil=image_pil,
        )
    )

    input_tensor = prediction[
        "input_tensor"
    ]

    prediction_class = prediction[
        "prediction_class"
    ]

    predicted_index = prediction[
        "predicted_index"
    ]

    model_confidence = prediction[
        "model_confidence"
    ]

    class_scores = prediction[
        "class_scores"
    ]

    # --------------------------------------------------------
    # Screening signal
    # --------------------------------------------------------

    screening_signal = (
        get_screening_signal(
            prediction_class
        )
    )

    # --------------------------------------------------------
    # Recommendation
    # --------------------------------------------------------

    recommendation = (
        get_recommendation(
            prediction_class
        )
    )

    # --------------------------------------------------------
    # Grad-CAM
    # --------------------------------------------------------

    gradcam_path = (
        GRADCAM_DIR
        / f"{image_path.stem}_gradcam.jpg"
    )

    try:

        generate_gradcam(
            model=model,
            image_bgr=image_bgr,
            input_tensor=input_tensor,
            target_class=predicted_index,
            output_path=gradcam_path,
        )

        gradcam_result = str(
            gradcam_path
        )

    except Exception as exc:

        gradcam_result = None

        print(
            f"Warning: Grad-CAM generation failed: {exc}",
            file=sys.stderr,
        )

    # --------------------------------------------------------
    # Lesion candidate estimation
    # --------------------------------------------------------

    try:

        lesion_measurement = (
            estimate_lesion_measurement(
                image_bgr
            )
        )

    except Exception as exc:

        lesion_measurement = {
            "status": "NOT_ESTIMATED",
            "method": (
                "image-based candidate region estimation"
            ),
            "candidate_score": None,
            "candidate_area_ratio": None,
            "width_pixels": None,
            "height_pixels": None,
            "area_pixels": None,
            "center": None,
            "bounding_box": None,
            "calibration_available": False,
            "physical_size": None,
            "note": (
                "Lesion candidate estimation could not "
                f"be completed: {exc}"
            ),
        }

    # --------------------------------------------------------
    # Research disclaimer
    # --------------------------------------------------------

    note = (
        "This is an AI-assisted research screening output "
        "and not a medical diagnosis. Model confidence is "
        "not clinical certainty."
    )

    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    result = {
        "status": "ANALYZED",

        "capture_coach": capture_coach,

        "quality": quality,

        "screening_signal": screening_signal,

        "prediction_class": prediction_class,

        "model_confidence": model_confidence,

        "class_scores": class_scores,

        "recommendation": recommendation,

        "note": note,

        "gradcam": gradcam_result,

        "lesion_measurement": lesion_measurement,
    }

    return result


# ============================================================
# COMMAND LINE INTERFACE
# ============================================================

def main() -> None:
    """
    Command-line interface for CancerLense.
    """

    if len(sys.argv) < 2:

        print(
            "Usage:"
        )

        print(
            'python -m app.backend.ml.predict '
            '"path\\to\\image.jpg"'
        )

        sys.exit(1)

    image_path = sys.argv[1]

    try:

        result = predict_image(
            image_path
        )

        print(
            json.dumps(
                result,
                indent=2,
                ensure_ascii=False,
            )
        )

    except Exception as exc:

        error_result = {
            "status": "ERROR",
            "error": str(exc),
        }

        print(
            json.dumps(
                error_result,
                indent=2,
                ensure_ascii=False,
            )
        )

        sys.exit(1)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()