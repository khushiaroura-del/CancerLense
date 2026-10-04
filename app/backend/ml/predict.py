import sys
from pathlib import Path

import cv2
import torch

from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget
from pytorch_grad_cam.utils.image import show_cam_on_image

from app.backend.ml.image_processor import process_image
from app.backend.ml.mobilenet_model import create_model


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

MODEL_PATH = PROJECT_ROOT / "models" / "best_model.pth"

GRADCAM_DIR = PROJECT_ROOT / "results" / "gradcam"

GRADCAM_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# CLASS NAMES
# ============================================================

CLASS_NAMES = {
    0: "cancer",
    1: "non-cancer"
}


# ============================================================
# LOAD MODEL
# ============================================================

def load_model():

    model = create_model()

    checkpoint = torch.load(
        MODEL_PATH,
        map_location=torch.device("cpu"),
        weights_only=False
    )

    if (
        isinstance(checkpoint, dict)
        and "model_state_dict" in checkpoint
    ):

        model.load_state_dict(
            checkpoint["model_state_dict"]
        )

    else:

        model.load_state_dict(
            checkpoint
        )

    model.eval()

    return model


# ============================================================
# FIND GRAD-CAM TARGET LAYER
# ============================================================

def get_target_layer(model):

    # CancerLenseModel
    #       |
    #       └── self.model
    #             |
    #             └── MobileNetV3 Small
    #                    |
    #                    └── features

    return model.model.features[-1]


# ============================================================
# GENERATE GRAD-CAM
# ============================================================

def generate_gradcam(
    model,
    tensor,
    original_image,
    predicted_class,
    output_path
):

    try:

        # ----------------------------------------------------
        # Target layer
        # ----------------------------------------------------

        target_layer = get_target_layer(
            model
        )

        target_layers = [
            target_layer
        ]

        # ----------------------------------------------------
        # Target prediction
        # ----------------------------------------------------

        targets = [
            ClassifierOutputTarget(
                predicted_class
            )
        ]

        # ----------------------------------------------------
        # Generate CAM
        # ----------------------------------------------------

        with GradCAM(
            model=model,
            target_layers=target_layers
        ) as cam:

            grayscale_cam = cam(
                input_tensor=tensor,
                targets=targets
            )

        grayscale_cam = grayscale_cam[
            0
        ]

        # ----------------------------------------------------
        # Prepare original image
        # ----------------------------------------------------

        original_image = original_image.astype(
            "float32"
        )

        # Make sure image is in 0-1 range
        if original_image.max() > 1.0:

            original_image = (
                original_image / 255.0
            )

        # ----------------------------------------------------
        # Overlay heatmap
        # ----------------------------------------------------

        visualization = show_cam_on_image(
            original_image,
            grayscale_cam,
            use_rgb=True
        )

        # ----------------------------------------------------
        # Save Grad-CAM image
        # ----------------------------------------------------

        cv2.imwrite(
            str(output_path),
            cv2.cvtColor(
                visualization,
                cv2.COLOR_RGB2BGR
            )
        )

        return output_path

    except Exception as exc:

        print(
            f"Grad-CAM generation failed: {exc}"
        )

        return None


# ============================================================
# PREDICT IMAGE
# ============================================================

def predict_image(image_path):

    image_path = Path(
        image_path
    )

    if not image_path.exists():

        raise FileNotFoundError(
            f"Image not found: {image_path}"
        )

    # ========================================================
    # 1. IMAGE QUALITY + PREPROCESSING
    # ========================================================

    processed = process_image(
        str(image_path)
    )

    quality = processed[
        "quality"
    ]

    # ========================================================
    # 2. REJECT POOR-QUALITY IMAGE
    # ========================================================

    if (
        quality["quality_status"]
        != "ACCEPTABLE"
    ):

        return {

            "image": str(
                image_path
            ),

            "status": "REJECTED",

            "reason": quality[
                "quality_status"
            ],

            "quality": quality
        }

    # ========================================================
    # 3. PREPARE IMAGE TENSOR
    # ========================================================

    image = processed[
        "processed_image"
    ]

    tensor = torch.tensor(
        image,
        dtype=torch.float32
    )

    # --------------------------------------------------------
    # HWC -> CHW
    # --------------------------------------------------------

    tensor = tensor.permute(
        2,
        0,
        1
    )

    # ========================================================
    # IMAGENET NORMALIZATION
    # ========================================================

    mean = torch.tensor(
        [0.485, 0.456, 0.406],
        dtype=torch.float32
    ).view(
        3,
        1,
        1
    )

    std = torch.tensor(
        [0.229, 0.224, 0.225],
        dtype=torch.float32
    ).view(
        3,
        1,
        1
    )

    tensor = (
        tensor - mean
    ) / std

    tensor = tensor.unsqueeze(
        0
    )

    # ========================================================
    # 4. LOAD TRAINED MODEL
    # ========================================================

    model = load_model()

    # ========================================================
    # 5. MODEL INFERENCE
    # ========================================================

    with torch.no_grad():

        output = model(
            tensor
        )

        probabilities = torch.softmax(
            output,
            dim=1
        )

    # --------------------------------------------------------
    # Predicted class
    # --------------------------------------------------------

    predicted_class = torch.argmax(
        probabilities,
        dim=1
    ).item()

    prediction = CLASS_NAMES[
        predicted_class
    ]

    # --------------------------------------------------------
    # Confidence
    # --------------------------------------------------------

    model_confidence = (
        probabilities[
            0,
            predicted_class
        ].item()
        * 100
    )

    # --------------------------------------------------------
    # Class probabilities
    # --------------------------------------------------------

    cancer_probability = (
        probabilities[
            0,
            0
        ].item()
        * 100
    )

    non_cancer_probability = (
        probabilities[
            0,
            1
        ].item()
        * 100
    )

    # ========================================================
    # 6. SCREENING INTERPRETATION
    # ========================================================

    if prediction == "cancer":

        screening_signal = (
            "CANCER-CLASS SIGNAL"
        )

        recommendation = (
            "Professional clinical examination "
            "is recommended for further evaluation."
        )

    else:

        screening_signal = (
            "NON-CANCER-CLASS SIGNAL"
        )

        recommendation = (
            "This AI screening result does not "
            "rule out disease. Professional "
            "evaluation should be considered "
            "when clinically appropriate."
        )

    # ========================================================
    # 7. GENERATE GRAD-CAM
    # ========================================================

    gradcam_path = (
        GRADCAM_DIR
        / f"{image_path.stem}_gradcam.jpg"
    )

    gradcam_result = generate_gradcam(
        model=model,
        tensor=tensor,
        original_image=image,
        predicted_class=predicted_class,
        output_path=gradcam_path
    )

    # ========================================================
    # 8. FINAL RESULT
    # ========================================================

    result = {

        "image": str(
            image_path
        ),

        "status": "ANALYZED",

        "quality": quality,

        "screening_signal": (
            screening_signal
        ),

        "prediction_class": (
            prediction
        ),

        "model_confidence": round(
            model_confidence,
            2
        ),

        "class_scores": {

            "cancer": round(
                cancer_probability,
                2
            ),

            "non_cancer": round(
                non_cancer_probability,
                2
            )
        },

        "recommendation": (
            recommendation
        ),

        "note": (
            "This is an AI-assisted research "
            "screening output and not a medical diagnosis."
        )
    }

    # ========================================================
    # ADD GRAD-CAM PATH
    # ========================================================

    if gradcam_result:

        result["gradcam"] = str(
            gradcam_result
        )

    return result


# ============================================================
# COMMAND-LINE TESTING
# ============================================================

if __name__ == "__main__":

    if len(sys.argv) < 2:

        print(
            "Usage:\n"
            "python -m app.backend.ml.predict "
            "\"IMAGE_PATH\""
        )

        sys.exit(1)

    image_path = sys.argv[1]

    result = predict_image(
        image_path
    )

    print()
    print(
        "CancerLens Screening Result"
    )

    print(
        "--------------------------------"
    )

    for key, value in result.items():

        print(
            f"{key}: {value}"
        )